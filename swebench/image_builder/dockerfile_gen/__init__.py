from argparse import ArgumentParser
from swebench.constants import (
    OG_SWE_BENCH_DATASETS,
    SWE_BENCH_MULTIMODAL_DATASETS,
    SWE_BENCH_MULTILINGUAL_DATASETS,
)
from swebench.harness.utils import load_swebench_dataset
from swebench.image_builder.constants import IMAGE_BUILDER_LOG_DIR
from pathlib import Path


def get_dockerfile(instance: dict, dataset_name: str) -> str:
    """
    The main dockerfile generator function.
    """
    if dataset_name in OG_SWE_BENCH_DATASETS:
        from swebench.image_builder.dockerfile_gen._swebench import _get_dockerfile

        return _get_dockerfile(instance)
    elif dataset_name in SWE_BENCH_MULTIMODAL_DATASETS:
        from swebench.image_builder.dockerfile_gen._swebench_multimodal import (
            _get_dockerfile,
        )

        return _get_dockerfile(instance)
    elif dataset_name in SWE_BENCH_MULTILINGUAL_DATASETS:
        from swebench.image_builder.dockerfile_gen._swebench_multilingual import (
            _get_dockerfile,
        )

        return _get_dockerfile(instance)
    elif dataset_name in SWE_BENCH_MULTILINGUAL_DATASETS:
        # TODO: Implement this
        raise NotImplementedError("Multilingual dataset not yet supported")
    else:
        raise ValueError(f"Invalid dataset name: {dataset_name}")


def main(
    dataset_name: str, split: str, output_dir: str, instance_ids: list[str] | None
):
    dataset = load_swebench_dataset(dataset_name, split, instance_ids=instance_ids)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for instance in dataset:
        dockerfile = get_dockerfile(instance, dataset_name)
        instance_dir = output_dir / instance["instance_id"]
        instance_dir.mkdir(parents=True, exist_ok=True)
        (instance_dir / "Dockerfile").write_text(dockerfile)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("dataset_name", type=str)
    parser.add_argument("split", type=str)
    parser.add_argument("output_dir", type=str, default=IMAGE_BUILDER_LOG_DIR)
    parser.add_argument("--instance_ids", type=list[str], default=None)
    args = parser.parse_args()
    main(**vars(args))
