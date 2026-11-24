import re

from dataclasses import dataclass
from typing import Optional, Union, cast

from swebench.types import (
    SWEbenchInstance,
)


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
    context_dir: Optional[str] = None

    def __post_init__(self):
        """Validate the dataclass fields after initialization."""
        if not self.instance_id:
            raise ValueError("instance_id cannot be empty")
        if not self.dockerfile:
            raise ValueError("dockerfile cannot be empty")
        if self.arch not in ["amd64", "arm64", "riscv64"]:
            raise ValueError(
                f"Invalid architecture: {self.arch}. Must be 'x86_64' or 'arm64' or 'riscv64'"
            )
        if self.namespace is not None and not self.namespace:
            raise ValueError("namespace cannot be empty string if provided")

    @property
    def name(self):
        # keep the published naming; amd64 images are tagged x86_64 as they always were
        arch = "x86_64" if self.arch == "amd64" else self.arch
        key = f"sweb.eval.{arch}.{self.instance_id}:{self.tag}"
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
        elif self.arch == "riscv64":
            return "linux/riscv64"
        else:
            raise ValueError(f"Invalid architecture: {self.arch}")


def get_image_specs_from_dataset(
    dataset: Union[list[SWEbenchInstance], list[ImageSpec]],
    dockerfiles: dict[str, str],
    namespace: Optional[str] = None,
    tag: str = "latest",
    context_dirs: Optional[dict] = None,
) -> list[ImageSpec]:
    """
    Idempotent function that converts a list of SWEbenchInstance objects to a list of ImageSpec objects.

    Args:
        dataset: List of SWEbenchInstance objects or ImageSpec objects.
        dockerfiles: Dict mapping instance_id to Dockerfile content.
        namespace: Docker registry namespace.
        tag: Docker image tag.
        context_dirs: Dict mapping instance_id to its build context directory.
    """
    if isinstance(dataset[0], ImageSpec):
        return cast(list[ImageSpec], dataset)
    context_dirs = context_dirs or {}
    return [
        make_image_spec(
            x,
            dockerfiles[x["instance_id"]],
            namespace,
            tag,
            context_dirs.get(x["instance_id"]),
        )
        for x in cast(list[SWEbenchInstance], dataset)
    ]


def make_image_spec(
    instance: SWEbenchInstance,
    dockerfile: str,
    namespace: Optional[str] = None,
    tag: str = "latest",
    context_dir: Optional[str] = None,
) -> ImageSpec:
    """
    Create an ImageSpec from a SWEbenchInstance for image building purposes.

    Args:
        instance: SWEbenchInstance dict.
        dockerfile: Dockerfile content string (pre-generated).
        namespace: Docker registry namespace.
        tag: Docker image tag.
        context_dir: Directory to build in, when the Dockerfile COPYs from it.
    """
    if isinstance(instance, ImageSpec):
        return instance
    assert tag is not None, "tag cannot be None"

    return ImageSpec(
        instance_id=instance["instance_id"],
        dockerfile=dockerfile,
        namespace=namespace,
        tag=tag,
        arch=_arch_from_dockerfile(dockerfile),
        context_dir=str(context_dir) if context_dir else None,
    )


def _arch_from_dockerfile(dockerfile: str) -> str:
    """Read the target architecture from the Dockerfile FROM --platform line."""
    m = re.search(r"FROM\s+--platform=linux/([a-z0-9_]+)", dockerfile)
    if m:
        arch = m.group(1)
        if arch.startswith("arm64"):
            return "arm64"
        if arch.startswith("riscv64"):
            return "riscv64"
        if arch.startswith("amd64") or arch.startswith("x86_64"):
            return "amd64"
    return "amd64"