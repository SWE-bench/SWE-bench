from pathlib import Path

import yaml


def upload_run(bucket_id, run_id, files, private=True, dry_run=False):
    files = [Path(f) for f in files]
    plan = {"bucket": bucket_id, "files": [f"{run_id}/{f.name}" for f in files]}
    if dry_run:
        return plan

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_bucket(bucket_id, private=private, exist_ok=True)
    api.batch_bucket_files(bucket_id, add=list(zip(files, plan["files"])))
    return plan


def write_eval_result(dataset, task_id, value, source_url, out_path):
    entry = {
        "dataset": {"id": dataset, "task_id": task_id},
        "value": value,
        "source": {"url": source_url},
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump([entry], sort_keys=False))
    return out_path
