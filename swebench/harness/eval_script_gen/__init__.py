from argparse import ArgumentParser
from swebench.constants import (
    OG_SWE_BENCH_DATASETS,
    SWE_BENCH_MULTIMODAL_DATASETS,
    SWE_BENCH_MULTILINGUAL_DATASETS,
)
from swebench.harness.utils import load_swebench_dataset
from pathlib import Path


def get_eval_script(instance: dict, dataset_name: str) -> str:
    """
    The main eval script generator function.
    Returns a complete bash eval script for the given instance and dataset.
    """
    if dataset_name in OG_SWE_BENCH_DATASETS:
        from swebench.harness.eval_script_gen._swebench import (
            get_eval_script as _get_eval_script,
        )

        return _get_eval_script(instance)
    elif dataset_name in SWE_BENCH_MULTIMODAL_DATASETS:
        from swebench.harness.eval_script_gen._swebench_multimodal import (
            get_eval_script as _get_eval_script,
        )

        return _get_eval_script(instance)
    elif dataset_name in SWE_BENCH_MULTILINGUAL_DATASETS:
        from swebench.harness.eval_script_gen._swebench_multilingual import (
            get_eval_script as _get_eval_script,
        )

        return _get_eval_script(instance)
    else:
        raise ValueError(f"Invalid dataset name: {dataset_name}")


def get_eval_script_list(instance: dict, dataset_name: str) -> list[str]:
    """
    Returns the eval script as a list of commands for the given instance and dataset.
    """
    if dataset_name in OG_SWE_BENCH_DATASETS:
        from swebench.harness.eval_script_gen._swebench import (
            get_eval_script_list as _get_eval_script_list,
        )

        return _get_eval_script_list(instance)
    elif dataset_name in SWE_BENCH_MULTIMODAL_DATASETS:
        from swebench.harness.eval_script_gen._swebench_multimodal import (
            get_eval_script_list as _get_eval_script_list,
        )

        return _get_eval_script_list(instance)
    elif dataset_name in SWE_BENCH_MULTILINGUAL_DATASETS:
        from swebench.harness.eval_script_gen._swebench_multilingual import (
            get_eval_script_list as _get_eval_script_list,
        )

        return _get_eval_script_list(instance)
    else:
        raise ValueError(f"Invalid dataset name: {dataset_name}")


def main(
    dataset_name: str, split: str, output_dir: str, instance_ids: list[str] | None
):
    """Generate eval scripts for all instances in a dataset."""
    dataset = load_swebench_dataset(dataset_name, split, instance_ids=instance_ids)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for instance in dataset:
        eval_script = get_eval_script(instance, dataset_name)
        instance_dir = output_dir / instance["instance_id"]
        instance_dir.mkdir(parents=True, exist_ok=True)
        (instance_dir / "eval_script.sh").write_text(eval_script)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("dataset_name", type=str)
    parser.add_argument("split", type=str)
    parser.add_argument("output_dir", type=str)
    parser.add_argument("--instance_ids", type=list[str], default=None)
    args = parser.parse_args()
    main(**vars(args))
