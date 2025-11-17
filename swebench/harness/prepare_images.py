import docker
import resource

from argparse import ArgumentParser

from swebench.harness.constants import KEY_INSTANCE_ID
from swebench.harness.docker_build import build_instance_images
from swebench.harness.docker_utils import list_images
from swebench.harness.test_spec.test_spec import make_test_spec
from swebench.harness.utils import load_swebench_dataset, str2bool, optional_str


def filter_dataset_to_build(
    dataset: list,
    instance_ids: list | None,
    client: docker.DockerClient,
    force_rebuild: bool,
    namespace: str = None,
    tag: str = None,
    env_image_tag: str = None,
    cli_docker_specs: dict = None,
):
    """
    Filter the dataset to only include instances that need to be built.

    Args:
        dataset (list): List of instances (usually all of SWE-bench dev/test split)
        instance_ids (list): List of instance IDs to build.
        client (docker.DockerClient): Docker client.
        force_rebuild (bool): Whether to force rebuild all images.
        cli_docker_specs (dict): Docker specs from CLI to override config values.
    """
    # Get existing images
    existing_images = list_images(client)
    data_to_build = []

    if instance_ids is None:
        instance_ids = [instance[KEY_INSTANCE_ID] for instance in dataset]

    # Check if all instance IDs are in the dataset
    not_in_dataset = set(instance_ids).difference(
        set([instance[KEY_INSTANCE_ID] for instance in dataset])
    )
    if not_in_dataset:
        raise ValueError(f"Instance IDs not found in dataset: {not_in_dataset}")

    for instance in dataset:
        if instance[KEY_INSTANCE_ID] not in instance_ids:
            # Skip instances not in the list
            continue

        # Check if the instance needs to be built (based on force_rebuild flag and existing images)
        spec = make_test_spec(
            instance,
            namespace=namespace,
            instance_image_tag=tag,
            env_image_tag=env_image_tag,
            cli_docker_specs=cli_docker_specs,
        )
        if force_rebuild:
            data_to_build.append(instance)
        elif spec.instance_image_key not in existing_images:
            data_to_build.append(instance)

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
    env_image_tag,
    docker_spec=None,
):
    """
    Build Docker images for the specified instances.

    Args:
        instance_ids (list): List of instance IDs to build.
        max_workers (int): Number of workers for parallel processing.
        force_rebuild (bool): Whether to force rebuild all images.
        open_file_limit (int): Open file limit.
        docker_spec (list): List of docker spec overrides in KEY=VALUE format.
    """
    # Parse docker_spec arguments
    cli_docker_specs = {}
    if docker_spec:
        for spec in docker_spec:
            if "=" not in spec:
                raise ValueError(f"Invalid docker_spec format: '{spec}'. Expected KEY=VALUE format.")
            key, value = spec.split("=", 1)
            cli_docker_specs[key.strip()] = value.strip()
        print(f"CLI Docker specs: {cli_docker_specs}")
    
    # Set open file limit
    resource.setrlimit(resource.RLIMIT_NOFILE, (open_file_limit, open_file_limit))
    client = docker.from_env()

    # Filter out instances that were not specified
    dataset = load_swebench_dataset(dataset_name, split)
    dataset = filter_dataset_to_build(
        dataset, instance_ids, client, force_rebuild, namespace, tag, env_image_tag, cli_docker_specs
    )

    if len(dataset) == 0:
        print("All images exist. Nothing left to build.")
        return 0

    # Build images for remaining instances
    successful, failed = build_instance_images(
        client=client,
        dataset=dataset,
        force_rebuild=force_rebuild,
        max_workers=max_workers,
        namespace=namespace,
        tag=tag,
        env_image_tag=env_image_tag,
        cli_docker_specs=cli_docker_specs,
    )
    print(f"Successfully built {len(successful)} images")
    print(f"Failed to build {len(failed)} images")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="SWE-bench/SWE-bench_Lite",
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
        "--tag", type=str, default=None, help="Tag to use for the images"
    )
    parser.add_argument(
        "--env_image_tag", type=str, default=None, help="Environment image tag to use"
    )
    parser.add_argument(
        "--docker_spec",
        action="append",
        type=str,
        metavar="KEY=VALUE",
        help="Override docker spec variables (can be used multiple times). Example: --docker_spec ubuntu_version=22.04 --docker_spec python_version=3.11"
    )
    args = parser.parse_args()
    main(**vars(args))
