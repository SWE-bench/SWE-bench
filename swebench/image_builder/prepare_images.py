import docker
import re
import resource
import subprocess
import tempfile

from argparse import ArgumentParser
from contextlib import contextmanager
from pathlib import Path

from swebench.image_builder.image_spec import get_image_specs_from_dataset
from swebench.image_builder.docker_build import build_instance_images
from swebench.image_builder.docker_utils import list_images
from swebench.harness.utils import load_swebench_dataset, str2bool, optional_str

DOCKERFILES_SUBDIR = Path("src") / "dockerfiles"


def load_dockerfiles_from_dir(dockerfiles_dir: Path) -> dict[str, str]:
    """
    Load Dockerfiles from a flat directory.

    Expects structure: dockerfiles_dir/<instance_id>.Dockerfile

    Args:
        dockerfiles_dir: Path to directory containing <instance_id>.Dockerfile files.
    Returns:
        Dict mapping instance_id to Dockerfile content.
    """
    dockerfiles = {}
    if not dockerfiles_dir.exists():
        raise FileNotFoundError(f"Dockerfiles directory not found: {dockerfiles_dir}")
    for dockerfile_path in dockerfiles_dir.glob("*.Dockerfile"):
        instance_id = dockerfile_path.name.removesuffix(".Dockerfile")
        dockerfiles[instance_id] = dockerfile_path.read_text()
    return dockerfiles


def _is_github_ref(dockerfile_repo: str) -> bool:
    """Check if the dockerfile_repo is a GitHub reference (not a local path)."""
    if re.match(r"^https?://github\.com/", dockerfile_repo):
        return True
    if re.match(r"^[\w.-]+/[\w.-]+$", dockerfile_repo) and not Path(dockerfile_repo).is_dir():
        return True
    return False


def _github_ref_to_urls(dockerfile_repo: str) -> list[str]:
    """Convert a GitHub reference to clone URLs (SSH first, then HTTPS fallback)."""
    if re.match(r"^https?://github\.com/", dockerfile_repo):
        # Extract owner/repo from URL
        match = re.match(r"^https?://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?/?$", dockerfile_repo)
        if not match:
            return [dockerfile_repo.rstrip("/") + ".git"]
        owner_repo = match.group(1)
    else:
        owner_repo = dockerfile_repo
    return [
        f"git@github.com:{owner_repo}.git",
        f"https://github.com/{owner_repo}.git",
    ]


@contextmanager
def resolve_dockerfile_repo(dockerfile_repo: str):
    """
    Resolve a dockerfile repo reference to a local path.

    Accepts:
        - A local directory path (used directly)
        - A GitHub repo in "owner/repo" format
        - A GitHub URL like "https://github.com/owner/repo"

    Yields the local Path to the repo root.
    """
    if not _is_github_ref(dockerfile_repo):
        repo_path = Path(dockerfile_repo)
        if not repo_path.is_dir():
            raise FileNotFoundError(f"Local dockerfile repo not found: {dockerfile_repo}")
        yield repo_path
        return

    clone_urls = _github_ref_to_urls(dockerfile_repo)
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, clone_url in enumerate(clone_urls):
            print(f"Cloning dockerfile repo from {clone_url}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, tmpdir],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                break
            if i < len(clone_urls) - 1:
                print(f"Clone failed, trying next URL...")
            else:
                raise RuntimeError(
                    f"Failed to clone dockerfile repo. Last error:\n{result.stderr}"
                )
        yield Path(tmpdir)


def filter_image_specs(
    image_specs: list,
    client: docker.DockerClient,
    force_rebuild: bool,
):
    """
    Filter the dataset to only include instances that need to be built.
    """
    existing_images = list_images(client)
    data_to_build = []

    for spec in image_specs:
        if force_rebuild:
            data_to_build.append(spec)
        elif spec.name not in existing_images:
            data_to_build.append(spec)

    return data_to_build


def main(
    dataset_name,
    split,
    instance_ids,
    max_workers,
    force_rebuild,
    open_file_limit,
    namespace,
    tag,
    dry_run,
    dockerfile_repo,
):
    """
    Build Docker images for the specified instances.

    Args:
        dataset_name (str): Name of the HuggingFace dataset.
        split (str): Dataset split to use.
        instance_ids (list): List of instance IDs to build.
        max_workers (int): Number of workers for parallel processing.
        force_rebuild (bool): Whether to force rebuild all images.
        open_file_limit (int): Open file limit.
        namespace (str): Docker registry namespace.
        tag (str): Docker image tag.
        dry_run (bool): If True, create docker files and build contexts but don't build images.
        dockerfile_repo (str): Dockerfile repo reference — a local path, GitHub "owner/repo", or GitHub URL.
    """
    # Set open file limit
    resource.setrlimit(resource.RLIMIT_NOFILE, (open_file_limit, open_file_limit))
    client = docker.from_env(timeout=600)

    # Load pre-generated dockerfiles
    with resolve_dockerfile_repo(dockerfile_repo) as repo_path:
        dockerfiles_dir = repo_path / DOCKERFILES_SUBDIR
        dockerfiles = load_dockerfiles_from_dir(dockerfiles_dir)

    # Load dataset and create image specs
    dataset = load_swebench_dataset(dataset_name, split, instance_ids=instance_ids)
    image_specs = get_image_specs_from_dataset(dataset, dockerfiles, namespace, tag)
    image_specs = filter_image_specs(image_specs, client, force_rebuild)

    if len(image_specs) == 0:
        print("All images exist. Nothing left to build.")
        return 0

    if dry_run:
        print(
            f"DRY RUN MODE: Creating build contexts for {len(image_specs)} images (no actual builds will be performed)"
        )

    # Build images for remaining instances
    successful, failed = build_instance_images(
        client=client,
        image_specs=image_specs,
        force_rebuild=force_rebuild,
        max_workers=max_workers,
        dry_run=dry_run,
    )
    if dry_run:
        print(f"Successfully created build contexts for {len(successful)} images")
        if len(failed) > 0:
            print(f"Failed to create build contexts for {len(failed)} images")
    else:
        print(f"Successfully built {len(successful)} images")
        if len(failed) > 0:
            print(f"Failed to build {len(failed)} images")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="SWE-bench/SWE-bench_Verified",
        help="Name of the dataset to use",
    )
    parser.add_argument("--split", type=str, default="test", help="Split to use")
    parser.add_argument(
        "--instance_ids",
        nargs="+",
        type=str,
        help="Instance IDs to run (space separated)",
    )
    parser.add_argument(
        "--max_workers", type=int, default=4, help="Max workers for parallel processing"
    )
    parser.add_argument(
        "--force_rebuild", type=str2bool, default=False, help="Force rebuild images"
    )
    parser.add_argument(
        "--open_file_limit", type=int, default=8192, help="Open file limit"
    )
    parser.add_argument(
        "--namespace",
        type=optional_str,
        default=None,
        help="Namespace to use for the images (default: None)",
    )
    parser.add_argument(
        "--tag", type=str, default="latest", help="Tag to use for the images"
    )
    parser.add_argument(
        "--dry_run",
        type=str2bool,
        default=False,
        help="Create docker files and build contexts but don't build images",
    )
    parser.add_argument(
        "--dockerfile_repo",
        type=str,
        required=True,
        help="Dockerfile repo: local path, GitHub 'owner/repo', or 'https://github.com/owner/repo'",
    )
    args = parser.parse_args()
    main(**vars(args))
