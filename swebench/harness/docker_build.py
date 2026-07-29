from __future__ import annotations

import docker
import docker.errors
import logging
import platform as _platform
import subprocess
import sys
import traceback

from pathlib import Path

from swebench.harness.constants import (
    BASE_IMAGE_BUILD_DIR,
    DOCKER_USER,
    ENV_IMAGE_BUILD_DIR,
    INSTANCE_IMAGE_BUILD_DIR,
    UTF8,
)
from swebench.harness.docker_utils import cleanup_container, remove_image
from swebench.harness.test_spec.test_spec import (
    get_test_specs_from_dataset,
    make_test_spec,
    TestSpec,
)
from swebench.harness.utils import ansi_escape, run_threadpool


# ---- Local dep-cache: hostnames whose traffic gets rewritten to nginx
# via --add-host at image build time when SWEBENCH_DEP_CACHE_ENABLED=1.
# Kept in sync with infra/dep-cache/nginx/nginx.conf server_name blocks
# in the PARENT repo. Five distinct hostnames; dl.google.com serves
# both Google Maven at /dl/android/maven2/ AND Android SDK at
# /android/repository/ via location-specific rewrites in nginx.
_DEP_CACHE_HOSTS = (
    "repo1.maven.org",
    "repo.maven.apache.org",
    "dl.google.com",
    "plugins.gradle.org",
    "services.gradle.org",
)


def _dep_cache_enabled() -> bool:
    import os
    return os.environ.get("SWEBENCH_DEP_CACHE_ENABLED") == "1"


_DEP_CACHE_BUILDER_NAME = "dep-cache-builder"
_DEP_CACHE_NETWORK = "dep-cache_default"
_DEP_CACHE_NGINX_CONTAINER = "dep-cache-nginx"


def _ensure_dep_cache_buildx_builder() -> None:
    """Docker Desktop's default buildx builder uses the `docker` driver,
    which silently DROPS --add-host at buildx-build time. That routes
    base-image downloads to the real internet, defeating the point of
    enabling the dep-cache at build time.

    We use a `docker-container`-driver builder instead, but there is a
    second gotcha: that driver honors --add-host as a flag but does NOT
    understand the `host-gateway` magic value (host-gateway is resolved
    by dockerd for regular container-run, not by the isolated BuildKit
    daemon a docker-container builder spawns). So we ALSO attach the
    builder to the compose network dep-cache_default and pass nginx's
    concrete IP as the --add-host target (resolved in the caller via
    _dep_cache_nginx_ip()).

    Idempotent: if the named builder already exists AND was created
    with the correct network attachment, do nothing. Otherwise the
    builder is recreated so the network attachment is fresh. Only
    invoked when SWEBENCH_DEP_CACHE_ENABLED=1."""
    inspect = subprocess.run(
        ["docker", "buildx", "inspect", _DEP_CACHE_BUILDER_NAME],
        capture_output=True,
        text=True,
    )
    if inspect.returncode == 0 and _DEP_CACHE_NETWORK in inspect.stdout:
        return
    # Either missing, or present without the network attachment. Recreate
    # cleanly so we don't inherit a stale network config.
    if inspect.returncode == 0:
        subprocess.run(
            ["docker", "buildx", "rm", _DEP_CACHE_BUILDER_NAME],
            capture_output=True,
            text=True,
        )
    subprocess.run(
        [
            "docker", "buildx", "create",
            "--name", _DEP_CACHE_BUILDER_NAME,
            "--driver", "docker-container",
            "--driver-opt", f"network={_DEP_CACHE_NETWORK}",
            "--bootstrap",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _dep_cache_nginx_ip() -> str:
    """Resolve dep-cache-nginx's IP on the dep-cache_default network so we
    can pass a concrete --add-host target (docker-container buildx driver
    doesn't understand `host-gateway`). Fails loudly if nginx isn't
    running — the wrapper's preflight should have caught that already,
    but this is a second line of defense."""
    result = subprocess.run(
        [
            "docker", "inspect", _DEP_CACHE_NGINX_CONTAINER,
            "--format",
            "{{(index .NetworkSettings.Networks \"" + _DEP_CACHE_NETWORK + "\").IPAddress}}",
        ],
        capture_output=True,
        text=True,
    )
    ip = result.stdout.strip()
    if result.returncode != 0 or not ip:
        raise RuntimeError(
            f"could not resolve {_DEP_CACHE_NGINX_CONTAINER}'s IP on "
            f"network {_DEP_CACHE_NETWORK}: exit {result.returncode}, "
            f"stderr={result.stderr.strip()!r}"
        )
    return ip


def _is_cross_platform_build(target_platform: str) -> bool:
    """Return True when the build targets a platform different from the host.

    The Docker SDK's legacy builder (``client.api.build``) cannot resolve
    locally-built images whose architecture differs from the host.  When this
    function returns ``True`` the caller should fall back to
    ``docker buildx build --load`` which handles cross-platform local images
    correctly.
    """
    machine = _platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        host_platform = "linux/x86_64"
    elif machine in ("arm64", "aarch64"):
        host_platform = "linux/arm64/v8"
    else:
        # Unknown host – be conservative and assume same platform.
        return False

    return target_platform != host_platform


class BuildImageError(Exception):
    def __init__(self, image_name, message, logger):
        super().__init__(message)
        self.super_str = super().__str__()
        self.image_name = image_name
        self.log_path = logger.log_file
        self.logger = logger

    def __str__(self):
        return (
            f"Error building image {self.image_name}: {self.super_str}\n"
            f"Check ({self.log_path}) for more information."
        )


def setup_logger(instance_id: str, log_file: Path, mode="w", add_stdout: bool = False):
    """
    This logger is used for logging the build process of images and containers.
    It writes logs to the log file.

    If `add_stdout` is True, logs will also be sent to stdout, which can be used for
    streaming ephemeral output from Modal containers.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"{instance_id}.{log_file.name}")
    handler = logging.FileHandler(log_file, mode=mode, encoding=UTF8)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    setattr(logger, "log_file", log_file)
    if add_stdout:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            f"%(asctime)s - {instance_id} - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def close_logger(logger):
    # To avoid too many open files
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)


def build_image(
    image_name: str,
    setup_scripts: dict,
    dockerfile: str,
    platform: str,
    client: docker.DockerClient,
    build_dir: Path,
    nocache: bool = False,
):
    """
    Builds a docker image with the given name, setup scripts, dockerfile, and platform.

    Args:
        image_name (str): Name of the image to build
        setup_scripts (dict): Dictionary of setup script names to setup script contents
        dockerfile (str): Contents of the Dockerfile
        platform (str): Platform to build the image for
        client (docker.DockerClient): Docker client to use for building the image
        build_dir (Path): Directory for the build context (will also contain logs, scripts, and artifacts)
        nocache (bool): Whether to use the cache when building
    """
    # Create a logger for the build process
    logger = setup_logger(image_name, build_dir / "build_image.log")
    logger.info(
        f"Building image {image_name}\n"
        f"Using dockerfile:\n{dockerfile}\n"
        f"Adding ({len(setup_scripts)}) setup scripts to image build repo"
    )

    for setup_script_name, setup_script in setup_scripts.items():
        logger.info(f"[SETUP SCRIPT] {setup_script_name}:\n{setup_script}")
    try:
        # Write the setup scripts to the build directory
        for setup_script_name, setup_script in setup_scripts.items():
            setup_script_path = build_dir / setup_script_name
            with open(setup_script_path, "w") as f:
                f.write(setup_script)
            if setup_script_name not in dockerfile:
                logger.warning(
                    f"Setup script {setup_script_name} may not be used in Dockerfile"
                )

        # Write the dockerfile to the build directory
        dockerfile_path = build_dir / "Dockerfile"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)

        # Build the image
        logger.info(
            f"Building docker image {image_name} in {build_dir} with platform {platform}"
        )

        if _is_cross_platform_build(platform) or _dep_cache_enabled():
            # The Docker SDK's legacy builder (client.api.build) cannot
            # resolve locally-built images when the target platform differs
            # from the host architecture.  Use ``docker buildx build --load``
            # instead, which uses BuildKit and handles this correctly.
            logger.info(
                f"Cross-platform build detected (target={platform}). "
                "Using 'docker buildx build --load'."
            )
            cmd = [
                "docker", "buildx", "build",
                "--platform", platform,
                "--load",
                "--tag", image_name,
            ]
            if nocache:
                cmd.append("--no-cache")

            if _dep_cache_enabled():
                # docker-driver builder silently ignores --add-host at
                # build-container level. Force a docker-container-driver
                # builder so BuildKit honors the flag, attached to the
                # dep-cache_default network so we can reach nginx by IP.
                # host-gateway is NOT supported by docker-container so we
                # resolve nginx's actual IP and pass it directly.
                _ensure_dep_cache_buildx_builder()
                nginx_ip = _dep_cache_nginx_ip()
                cmd.extend(["--builder", _DEP_CACHE_BUILDER_NAME])
                for host in _DEP_CACHE_HOSTS:
                    cmd.extend(["--add-host", f"{host}:{nginx_ip}"])

            cmd.append(str(build_dir))

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            buildlog = ""
            for line in process.stdout:
                clean_line = ansi_escape(line)
                logger.info(clean_line.rstrip())
                buildlog += clean_line
            process.wait()
            if process.returncode != 0:
                raise docker.errors.BuildError(
                    f"docker buildx build exited with code {process.returncode}",
                    buildlog,
                )
        else:
            response = client.api.build(
                path=str(build_dir),
                tag=image_name,
                rm=True,
                forcerm=True,
                decode=True,
                platform=platform,
                nocache=nocache,
            )

            # Log the build process continuously
            buildlog = ""
            for chunk in response:
                if "stream" in chunk:
                    # Remove ANSI escape sequences from the log
                    chunk_stream = ansi_escape(chunk["stream"])
                    logger.info(chunk_stream.strip())
                    buildlog += chunk_stream
                elif "errorDetail" in chunk:
                    # Decode error message, raise BuildError
                    logger.error(f"Error: {ansi_escape(chunk['errorDetail']['message'])}")
                    raise docker.errors.BuildError(
                        chunk["errorDetail"]["message"], buildlog
                    )
                elif "error" in chunk:
                    # Some Docker versions return 'error' without 'errorDetail'
                    error_msg = ansi_escape(str(chunk["error"]))
                    logger.error(f"Error: {error_msg}")
                    raise docker.errors.BuildError(error_msg, buildlog)

        # Verify the image was actually created — the legacy builder can
        # silently fail (e.g. Dockerfile parse errors) without raising an
        # error through the response stream.
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            raise docker.errors.BuildError(
                f"Image {image_name} not found after build completed. "
                "The build may have silently failed (check the Dockerfile for syntax errors).",
                buildlog,
            )
        logger.info("Image built successfully!")
    except docker.errors.BuildError as e:
        logger.error(f"docker.errors.BuildError during {image_name}: {e}")
        raise BuildImageError(image_name, str(e), logger) from e
    except Exception as e:
        logger.error(f"Error building image {image_name}: {e}")
        raise BuildImageError(image_name, str(e), logger) from e
    finally:
        close_logger(logger)  # functions that create loggers should close them


def _collect_gradle_warmup(test_specs: list[TestSpec]) -> str:
    """
    For all Kotlin TestSpecs that have gradle_distribution_url:
      - injects a stable cache-bust key into docker_specs (so base_image_key hash
        changes when the URL set changes — must be called before first key access)
      - returns the shell script content to pass as setup_scripts["gradle_warmup.sh"]

    Returns a no-op script if no Kotlin specs have a distribution URL.
    """
    from swebench.harness.dockerfiles.kotlin import make_gradle_warmup_script

    urls = sorted({
        s.gradle_distribution_url
        for s in test_specs
        if s.language == "kotlin" and s.gradle_distribution_url
    })
    script = make_gradle_warmup_script(urls) if urls else "#!/bin/bash\nexit 0\n"
    cache_key = " ".join(urls)  # changes when URL set changes → invalidates base_image_key
    for spec in test_specs:
        if spec.language == "kotlin":
            spec.docker_specs["gradle_warmup_urls"] = cache_key
    return script


def build_base_images(
    client: docker.DockerClient,
    dataset: list,
    force_rebuild: bool = False,
    namespace: str = None,
    instance_image_tag: str = None,
    env_image_tag: str = None,
):
    """
    Builds the base images required for the dataset if they do not already exist.

    Args:
        client (docker.DockerClient): Docker client to use for building the images
        dataset (list): List of test specs or dataset to build images for
        force_rebuild (bool): Whether to force rebuild the images even if they already exist
    """
    # Get the base images to build from the dataset
    test_specs = get_test_specs_from_dataset(
        dataset,
        namespace=namespace,
        instance_image_tag=instance_image_tag,
        env_image_tag=env_image_tag,
    )
    warmup_script = _collect_gradle_warmup(test_specs)  # mutates docker_specs, must run before first key access
    base_images = {
        x.base_image_key: (x.base_dockerfile, x.platform, x.language) for x in test_specs
    }

    # Build the base images
    for image_name, (dockerfile, platform, language) in base_images.items():
        try:
            # Check if the base image already exists
            client.images.get(image_name)
            if force_rebuild:
                # Remove the base image if it exists and force rebuild is enabled
                remove_image(client, image_name, "quiet")
            else:
                print(f"Base image {image_name} already exists, skipping build.")
                continue
        except docker.errors.ImageNotFound:
            pass
        # Build the base image (if it does not exist or force rebuild is enabled)
        print(f"Building base image ({image_name})")
        scripts = {"gradle_warmup.sh": warmup_script} if language == "kotlin" else {}
        # If SWEBENCH_CA_CERT is set, plumb the PEM bytes into the build
        # context as `ca.crt`. The kotlin base Dockerfile picks this up via
        # the {ca_install} block wired in get_dockerfile_base(). Validation
        # (file exists, is a PEM) lives in the single get_ca_cert_pem()
        # helper so this call path can't disagree with the Dockerfile side.
        if language == "kotlin":
            from swebench.harness.dockerfiles.kotlin import get_ca_cert_pem
            pem = get_ca_cert_pem()  # raises on invalid config; None if unset
            if pem is not None:
                scripts["ca.crt"] = pem
        build_image(
            image_name=image_name,
            setup_scripts=scripts,
            dockerfile=dockerfile,
            platform=platform,
            client=client,
            build_dir=BASE_IMAGE_BUILD_DIR / image_name.replace(":", "__"),
        )
    print("Base images built successfully.")


def get_env_configs_to_build(
    client: docker.DockerClient,
    dataset: list,
    namespace: str = None,
    instance_image_tag: str = None,
    env_image_tag: str = None,
):
    """
    Returns a dictionary of image names to build scripts and dockerfiles for environment images.
    Returns only the environment images that need to be built.

    Args:
        client (docker.DockerClient): Docker client to use for building the images
        dataset (list): List of test specs or dataset to build images for
    """
    image_scripts = dict()
    base_images = dict()
    test_specs = get_test_specs_from_dataset(
        dataset,
        namespace=namespace,
        instance_image_tag=instance_image_tag,
        env_image_tag=env_image_tag,
    )
    _collect_gradle_warmup(test_specs)  # mutates docker_specs before any key access

    for test_spec in test_specs:
        # Check if the base image exists
        try:
            if test_spec.base_image_key not in base_images:
                base_images[test_spec.base_image_key] = client.images.get(
                    test_spec.base_image_key
                )
            base_image = base_images[test_spec.base_image_key]
        except docker.errors.ImageNotFound:
            raise Exception(
                f"Base image {test_spec.base_image_key} not found for {test_spec.env_image_key}\n."
                "Please build the base images first."
            )

        # Check if the environment image exists
        image_exists = False
        try:
            env_image = client.images.get(test_spec.env_image_key)
            image_exists = True
        except docker.errors.ImageNotFound:
            pass
        if not image_exists:
            # Add the environment image to the list of images to build
            image_scripts[test_spec.env_image_key] = {
                "setup_script": test_spec.setup_env_script,
                "dockerfile": test_spec.env_dockerfile,
                "platform": test_spec.platform,
                "language": test_spec.language,
            }
    return image_scripts


def build_env_images(
    client: docker.DockerClient,
    dataset: list,
    force_rebuild: bool = False,
    max_workers: int = 4,
    namespace: str = None,
    instance_image_tag: str = None,
    env_image_tag: str = None,
):
    """
    Builds the environment images required for the dataset if they do not already exist.

    Args:
        client (docker.DockerClient): Docker client to use for building the images
        dataset (list): List of test specs or dataset to build images for
        force_rebuild (bool): Whether to force rebuild the images even if they already exist
        max_workers (int): Maximum number of workers to use for building images
    """
    # Get the environment images to build from the dataset
    test_specs = get_test_specs_from_dataset(
        dataset,
        namespace=namespace,
        instance_image_tag=instance_image_tag,
        env_image_tag=env_image_tag,
    )
    _collect_gradle_warmup(test_specs)  # mutates docker_specs before any key access
    if force_rebuild:
        for key in {x.env_image_key for x in test_specs}:
            remove_image(client, key, "quiet")
    build_base_images(
        client, test_specs, force_rebuild, namespace, instance_image_tag, env_image_tag
    )
    configs_to_build = get_env_configs_to_build(
        client, test_specs, namespace, instance_image_tag, env_image_tag
    )
    if len(configs_to_build) == 0:
        print("No environment images need to be built.")
        return [], []
    print(f"Total environment images to build: {len(configs_to_build)}")

    warmup_script = _collect_gradle_warmup(test_specs)
    args_list = list()
    # If SWEBENCH_CA_CERT is set, env-image builds also need `ca.crt` in
    # their build context because the kotlin env-image Dockerfile falls
    # back to _DOCKERFILE_BASE_KOTLIN (no dedicated _DOCKERFILE_ENV entry
    # for kotlin exists) and that template's {ca_install} block references
    # `COPY ca.crt`. Without this plumbing the env build fails with
    # "ca.crt: not found" at buildx-context transfer time.
    from swebench.harness.dockerfiles.kotlin import get_ca_cert_pem
    _ca_pem = get_ca_cert_pem()  # raises on invalid config; None if unset
    for image_name, config in configs_to_build.items():
        scripts = {"setup_env.sh": config["setup_script"]}
        if config.get("language") == "kotlin":
            scripts["gradle_warmup.sh"] = warmup_script
            if _ca_pem is not None:
                scripts["ca.crt"] = _ca_pem
        args_list.append(
            (
                image_name,
                scripts,
                config["dockerfile"],
                config["platform"],
                client,
                ENV_IMAGE_BUILD_DIR / image_name.replace(":", "__"),
            )
        )

    successful, failed = run_threadpool(build_image, args_list, max_workers)
    # Show how many images failed to build
    if len(failed) == 0:
        print("All environment images built successfully.")
    else:
        print(f"{len(failed)} environment images failed to build.")

    # Return the list of (un)successfuly built images
    return successful, failed


def build_instance_images(
    client: docker.DockerClient,
    dataset: list,
    force_rebuild: bool = False,
    max_workers: int = 4,
    namespace: str = None,
    tag: str = None,
    env_image_tag: str = None,
    on_complete=None,
):
    """
    Builds the instance images required for the dataset if they do not already exist.

    Args:
        dataset (list): List of test specs or dataset to build images for
        client (docker.DockerClient): Docker client to use for building the images
        force_rebuild (bool): Whether to force rebuild the images even if they already exist
        max_workers (int): Maximum number of workers to use for building images
    """
    # Build environment images (and base images as needed) first
    test_specs = list(
        map(
            lambda x: make_test_spec(
                x,
                namespace=namespace,
                instance_image_tag=tag,
                env_image_tag=env_image_tag,
            ),
            dataset,
        )
    )
    if force_rebuild:
        for spec in test_specs:
            remove_image(client, spec.instance_image_key, "quiet")
    _, env_failed = build_env_images(client, test_specs, force_rebuild, max_workers)

    skipped_payloads = []
    if len(env_failed) > 0:
        # Don't build images for instances that depend on failed-to-build env images
        env_failed_keys = {payload[0] for payload in env_failed}
        dont_run_specs = [
            spec for spec in test_specs if spec.env_image_key in env_failed_keys
        ]
        test_specs = [
            spec for spec in test_specs if spec.env_image_key not in env_failed_keys
        ]
        skipped_payloads = [(spec, client, None, False) for spec in dont_run_specs]
        print(
            f"Skipping {len(dont_run_specs)} instances - due to failed env image builds"
        )
    print(f"Building instance images for {len(test_specs)} instances")
    successful, failed = list(), list()

    # `logger` is set to None b/c logger is created in build-instage_image
    payloads = [(spec, client, None, False) for spec in test_specs]
    # Build the instance images
    successful, failed = run_threadpool(build_instance_image, payloads, max_workers, on_complete=on_complete)
    failed.extend(skipped_payloads)
    # Show how many images failed to build
    if len(failed) == 0:
        print("All instance images built successfully.")
    else:
        print(f"{len(failed)} instance images failed to build.")

    # Return the list of (un)successfuly built images
    return successful, failed


def build_instance_image(
    test_spec: TestSpec,
    client: docker.DockerClient,
    logger: logging.Logger | None,
    nocache: bool,
):
    """
    Builds the instance image for the given test spec if it does not already exist.

    Args:
        test_spec (TestSpec): Test spec to build the instance image for
        client (docker.DockerClient): Docker client to use for building the image
        logger (logging.Logger): Logger to use for logging the build process
        nocache (bool): Whether to use the cache when building
    """
    # Set up logging for the build process
    build_dir = INSTANCE_IMAGE_BUILD_DIR / test_spec.instance_image_key.replace(
        ":", "__"
    )
    new_logger = False
    if logger is None:
        new_logger = True
        logger = setup_logger(test_spec.instance_id, build_dir / "prepare_image.log")

    # Get the image names and dockerfile for the instance image
    image_name = test_spec.instance_image_key
    env_image_name = test_spec.env_image_key
    dockerfile = test_spec.instance_dockerfile

    # Check that the env. image the instance image is based on exists
    try:
        env_image = client.images.get(env_image_name)
    except docker.errors.ImageNotFound as e:
        raise BuildImageError(
            test_spec.instance_id,
            f"Environment image {env_image_name} not found for {test_spec.instance_id}",
            logger,
        ) from e
    logger.info(
        f"Environment image {env_image_name} found for {test_spec.instance_id}\n"
        f"Building instance image {image_name} for {test_spec.instance_id}"
    )

    # Check if the instance image already exists
    image_exists = False
    try:
        client.images.get(image_name)
        image_exists = True
    except docker.errors.ImageNotFound:
        pass

    # Build the instance image
    if not image_exists:
        build_image(
            image_name=image_name,
            setup_scripts={
                "setup_repo.sh": test_spec.install_repo_script,
            },
            dockerfile=dockerfile,
            platform=test_spec.platform,
            client=client,
            build_dir=build_dir,
            nocache=nocache,
        )
    else:
        logger.info(f"Image {image_name} already exists, skipping build.")

    if new_logger:
        close_logger(logger)


def build_container(
    test_spec: TestSpec,
    client: docker.DockerClient,
    run_id: str,
    logger: logging.Logger,
    nocache: bool,
    force_rebuild: bool = False,
):
    """
    Builds the instance image for the given test spec and creates a container from the image.

    Args:
        test_spec (TestSpec): Test spec to build the instance image and container for
        client (docker.DockerClient): Docker client for building image + creating the container
        run_id (str): Run ID identifying process, used for the container name
        logger (logging.Logger): Logger to use for logging the build process
        nocache (bool): Whether to use the cache when building
        force_rebuild (bool): Whether to force rebuild the image even if it already exists
    """
    # Build corresponding instance image
    if force_rebuild:
        remove_image(client, test_spec.instance_image_key, "quiet")
    if not test_spec.is_remote_image:
        build_instance_image(test_spec, client, logger, nocache)
    else:
        try:
            client.images.get(test_spec.instance_image_key)
        except docker.errors.ImageNotFound:
            try:
                client.images.pull(test_spec.instance_image_key)
            except docker.errors.NotFound as e:
                raise BuildImageError(test_spec.instance_id, str(e), logger) from e
            except Exception as e:
                raise Exception(
                    f"Error occurred while pulling image {test_spec.base_image_key}: {str(e)}"
                )

    container = None
    try:
        # Create the container
        logger.info(f"Creating container for {test_spec.instance_id}...")

        # Define arguments for running the container
        run_args = test_spec.docker_specs.get("run_args", {})
        cap_add = run_args.get("cap_add", [])

        container = client.containers.create(
            image=test_spec.instance_image_key,
            name=test_spec.get_instance_container_name(run_id),
            user=DOCKER_USER,
            detach=True,
            command="tail -f /dev/null",
            platform=test_spec.platform,
            cap_add=cap_add,
        )
        logger.info(f"Container for {test_spec.instance_id} created: {container.id}")
        return container
    except Exception as e:
        # If an error occurs, clean up the container and raise an exception
        logger.error(f"Error creating container for {test_spec.instance_id}: {e}")
        logger.info(traceback.format_exc())
        cleanup_container(client, container, logger)
        raise BuildImageError(test_spec.instance_id, str(e), logger) from e
