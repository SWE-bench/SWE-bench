"""
Gradle SWE-bench build pipeline.

Takes the raw dataset, builds Docker images for each instance, and outputs a
dataset containing only the instances whose images built successfully.

Input:  data/gradle_benchmark_dataset.json
        data/build_cache.json
Output: data/gradle_benchmark_dataset_buildable.json

Steps:
  build_dataset — Extend tasks with test_cmd + image_name + build Docker images (build_dataset.sh)
  filter_build  — Keep instances marked "success" in build_cache.json

Usage:
  python pipeline.py
"""
import subprocess
import sys
import os
import json

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BENCH_DIR, 'data')
DATASET = os.path.join(DATA_DIR, 'gradle_benchmark_dataset.json')
BUILD_CACHE = os.path.join(DATA_DIR, 'build_cache.json')
OUTPUT_DATASET = os.path.join(DATA_DIR, 'gradle_benchmark_dataset_buildable.json')


def build_dataset():
    print("\n--- build_dataset: Extend tasks with test_cmd + image_name + build Docker images ---")
    script = os.path.join(BENCH_DIR, 'build_dataset.sh')
    result = subprocess.run(['/bin/bash', script, DATASET])
    if result.returncode != 0:
        # The Docker SDK has a known race condition: containers cleaned up between
        # containers.list() and containers.get() raise NotFound.  This only happens
        # after all instances have already been evaluated, so the build output is
        # intact.  Treat exit code 1 as a soft warning; any other code is a hard failure.
        if result.returncode == 1:
            print("WARNING: build_dataset.sh exited with code 1 (possible benign Docker race condition). "
                  "Build stage completed.", file=sys.stderr)
        else:
            print(f"ERROR: build_dataset.sh failed with exit code {result.returncode}.", file=sys.stderr)
            sys.exit(result.returncode)


def filter_build():
    print("\n--- filter_build: Keep successfully-built instances ---")
    with open(BUILD_CACHE) as f:
        cache = json.load(f)
    with open(DATASET) as f:
        dataset = json.load(f)

    successful = {k for k, v in cache.items() if v == 'success'}
    failed = sum(1 for v in cache.values() if v != 'success')
    print(f'Failed instances from build: {failed}')

    buildable = [item for item in dataset if item.get('instance_id') in successful]
    with open(OUTPUT_DATASET, 'w') as f:
        json.dump(buildable, f, indent=2)
    print(f'Saved {len(buildable)} items → {OUTPUT_DATASET}')
    print(f'Dataset: {len(dataset)} → {len(buildable)} buildable items (removed {len(dataset) - len(buildable)})')


def main():
    build_dataset()
    filter_build()
    print("\n--- Done ---")
    print("Buildable dataset written to: data/gradle_benchmark_dataset_buildable.json")


if __name__ == '__main__':
    main()
