import json
from argparse import ArgumentParser

from swebench.harness.run_evaluation import _docker_client

"""
Script for removing containers associated with specified instance IDs.
"""


def main(instance_ids=None, predictions_path=None, run_id=None):
    all_ids = set()
    if predictions_path:
        with open(predictions_path, "r") as f:
            predictions = json.loads(f.read())
            for pred in predictions:
                all_ids.add(pred["instance_id"])

    if instance_ids:
        all_ids |= set(instance_ids)

    if not all_ids and not run_id:
        print("Provide --instance_ids, --predictions_path or --run_id, exiting.")
        return

    client = _docker_client()
    # containers are named sweb.eval.<instance_id>.<run_id>, so match on the
    # prefix rather than an exact name
    removed = 0
    for container in client.containers.list(all=True):
        name = container.name
        if not name.startswith("sweb.eval."):
            continue
        rest = name[len("sweb.eval.") :]
        instance_id, _, container_run = rest.rpartition(".")
        if not instance_id:  # no run id in the name
            instance_id, container_run = rest, ""
        if all_ids and instance_id not in all_ids:
            continue
        if run_id and container_run != run_id:
            continue
        try:
            container.remove(force=True)
            print(f"Removed container {name}")
            removed += 1
        except Exception as e:
            print(f"Error removing container {name}: {e}")
    print(f"Removed {removed} container(s).")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--instance_ids", nargs="+", type=str, help="Instance IDs to remove containers for"
    )
    parser.add_argument("--predictions_path", type=str, help="Path to predictions file")
    parser.add_argument("--run_id", type=str, help="Only remove containers from this run")
    args = parser.parse_args()
    main(**vars(args))
