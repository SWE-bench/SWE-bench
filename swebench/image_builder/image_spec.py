from dataclasses import dataclass
from typing import Optional, Union, cast

from swebench.types import (
    SWEbenchInstance,
)
from swebench.image_builder.dockerfile_gen import get_dockerfile
from swebench.harness.utils import load_swebench_dataset


@dataclass
class ImageSpec:
    """
    A dataclass that represents an image specification for building Docker images
    for a single SWE-bench instance.
    """

    instance_id: str
    dockerfile: str
    namespace: Optional[str]
    tag: str = "latest"
    arch: str = "amd64"

    def __post_init__(self):
        """Validate the dataclass fields after initialization."""
        if not self.instance_id:
            raise ValueError("instance_id cannot be empty")
        if not self.dockerfile:
            raise ValueError("dockerfile cannot be empty")
        if self.arch not in ["amd64", "arm64"]:
            raise ValueError(
                f"Invalid architecture: {self.arch}. Must be 'x86_64' or 'arm64'"
            )
        if self.namespace is not None and not self.namespace:
            raise ValueError("namespace cannot be empty string if provided")

    @property
    def name(self):
        key = f"{self.arch}.{self.instance_id}:{self.tag}"
        if self.is_remote_image:
            # docker hub doesn't allow dunders in image names, so we replace them with _1776_
            key = f"{self.namespace}/{key}".replace("__", "_1776_")
        return key.lower()

    @property
    def filesafe_name(self):
        return self.name.replace(":", "__")

    @property
    def is_remote_image(self):
        return self.namespace is not None

    @property
    def platform(self):
        if self.arch == "amd64":
            return "linux/amd64"
        elif self.arch == "x86_64":
            return "linux/amd64"
        elif self.arch == "arm64":
            return "linux/arm64/v8"
        else:
            raise ValueError(f"Invalid architecture: {self.arch}")


def get_image_specs_from_dataset(
    dataset: Union[list[SWEbenchInstance], list[ImageSpec]],
    dataset_name: str,
    namespace: Optional[str] = None,
    tag: str = "latest",
) -> list[ImageSpec]:
    """
    Idempotent function that converts a list of SWEbenchInstance objects to a list of ImageSpec objects.
    """
    if isinstance(dataset[0], ImageSpec):
        return cast(list[ImageSpec], dataset)
    return list(
        map(
            lambda x: make_image_spec(x, dataset_name, namespace, tag),
            cast(list[SWEbenchInstance], dataset),
        )
    )


def make_image_spec(
    instance: SWEbenchInstance,
    dataset_name: str,
    namespace: Optional[str] = None,
    tag: str = "latest",
) -> ImageSpec:
    """
    Create an ImageSpec from a SWEbenchInstance for image building purposes.
    """
    if isinstance(instance, ImageSpec):
        return instance
    assert tag is not None, "tag cannot be None"

    instance_id = instance["instance_id"]
    dockerfile = get_dockerfile(instance, dataset_name)

    return ImageSpec(
        instance_id=instance_id,
        dockerfile=dockerfile,
        namespace=namespace,
        tag=tag,
    )


def load_swebench_dataset_image_specs(
    dataset_name="SWE-bench/SWE-bench",
    split="test",
    namespace: Optional[str] = None,
    tag: str = "latest",
    instance_ids=None,
) -> list[ImageSpec]:
    """
    Load a list of ImageSpec objects from a SWE-bench dataset.
    """
    dataset = load_swebench_dataset(dataset_name, split, instance_ids=instance_ids)
    return [
        make_image_spec(instance, dataset_name, namespace, tag) for instance in dataset
    ]
