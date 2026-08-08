"""
SWE-bench Image Builder

This module handles Docker image building for SWE-bench instances.
It provides functionality to build base, environment, and instance images
required for evaluation.
"""

from swebench.image_builder.image_spec import (
    ImageSpec,
    make_image_spec,
    get_image_specs_from_dataset,
)
from swebench.image_builder.docker_build import (
    build_instance_image,
    build_instance_images,
    BuildImageError,
)
from swebench.image_builder.docker_utils import (
    remove_image,
)

__all__ = [
    "ImageSpec",
    "make_image_spec",
    "get_image_specs_from_dataset",
    "build_base_images",
    "build_env_images",
    "build_instance_images",
    "build_instance_image",
    "BuildImageError",
    "remove_image",
]
