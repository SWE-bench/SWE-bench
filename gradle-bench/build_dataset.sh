#!/usr/bin/env bash
SCRIPT_DIR="$(dirname "$0")"
DATASET=${1:-$SCRIPT_DIR/data/gradle_benchmark_dataset_high_quality_72.json}
# Drop the dataset arg if present, leaving any remaining args to forward to
# prepare_images (e.g. --rebuild_failures, --force_rebuild true,
# --instance_ids id1 id2).
if [ $# -gt 0 ]; then shift; fi

# 1. Extend the dataset in place with per-task "test_cmd" and "image_name"
#    fields resolved from MAP_REPO_VERSION_TO_SPECS (includes repo_customization
#    overrides).
python "$SCRIPT_DIR/augment_dataset.py" "$DATASET"

# 2. Build a Docker image per task.
python -m swebench.harness.prepare_images \
  --dataset_name "$DATASET" \
  --max_workers 8 \
  --namespace "" \
  --tag latest \
  --env_image_tag latest \
  --cache_path "$SCRIPT_DIR/data/build_cache.json" \
  "$@"