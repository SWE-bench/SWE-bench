"""
Convert extracted conda environments from JSONL to individual YAML files.
"""

import json
from pathlib import Path
from tqdm import tqdm


def main():
    input_file = "old_conda_envs_SWE-bench__SWE-bench_full_only.jsonl"
    output_base = Path("swebench/resources/swebench-og/environments")

    # Count total entries
    total = 0
    with open(input_file) as f:
        for line in f:
            if line.strip():
                total += 1

    print(f"Converting {total} environments from {input_file}")

    created = 0
    skipped = 0
    errors = 0

    with open(input_file) as f:
        for line in tqdm(f, total=total, desc="Converting"):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                instance_id = data["instance_id"]
                env_yml = data["environment"]["environment_yml"]

                # Determine owner (first part before __)
                owner = instance_id.split("__")[0]

                # Create owner directory if needed
                owner_dir = output_base / owner
                owner_dir.mkdir(parents=True, exist_ok=True)

                # Write YAML file
                output_file = owner_dir / f"{instance_id}.yml"

                # Skip if file already exists (from Verified)
                if output_file.exists():
                    skipped += 1
                    continue

                output_file.write_text(env_yml)
                created += 1

            except Exception as e:
                print(f"Error processing line: {e}")
                errors += 1
                continue

    print("\nResults:")
    print(f"  Created: {created}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total: {total}")


if __name__ == "__main__":
    main()
