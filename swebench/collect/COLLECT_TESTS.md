# collect_tests.py

## Overview

`collect_tests.py` collects and categorizes test results for SWE-bench instances. It identifies:
- **FAIL_TO_PASS**: Tests that failed before the patch but pass after applying it
- **PASS_TO_PASS**: Tests that passed both before and after the patch

## How It Works

For each instance:
1. Clones the repository at the base commit
2. Builds a Docker container and runs tests (before patch)
3. Applies the patch and runs tests again (after patch)
4. Compares results to determine FAIL_TO_PASS and PASS_TO_PASS tests
5. Updates the dataset JSON file with the test lists

**Key Features:**
- Parallel processing with configurable workers
- Incremental saving (results preserved on interruption)
- Resume support (skips already-processed instances)

## Usage

### Basic Command

```bash
python collect_tests.py <dataset_path> <output_path>
```

### Arguments

**Required:**
- `dataset_path`: Input dataset JSON file
- `output_path`: Output dataset JSON file with collected tests

**Optional:**
- `--instance-ids <id1> <id2>`: Process only specific instances
- `--force-rebuild`: Force rebuild of Docker images
- `--max-workers <N>`: Number of parallel workers (default: 8)
- `--timeout <seconds>`: Test execution timeout (default: 1800)

### Examples

```bash
# Process entire dataset
python collect_tests.py gradle_prs_swe_bench.json output.json

# Process specific instances with 4 workers
python collect_tests.py dataset.json output.json --instance-ids repo__project-123 --max-workers 4

# Resume interrupted run with longer timeout
python collect_tests.py dataset.json output.json --timeout 3600
```

## Input/Output Format

**Input:** JSON file with instances containing `instance_id`, `patch`, `repo`, `base_commit`, etc.

**Output:** Same instances with added fields:
```json
{
  "instance_id": "repo__project-123",
  "FAIL_TO_PASS": ["test.package.TestClass::testMethod1"],
  "PASS_TO_PASS": ["test.package.TestClass::testMethod3"]
}
```

## Troubleshooting

**Docker errors:** Ensure Docker daemon is running and user has permissions

**Timeouts:** Increase with `--timeout` flag or check for hanging tests

**Patch failures:** Check instance logs in `/tmp/collect_tests_*` directories

**Disk space:** Clean up with `docker system prune`

**Resume after interruption:** Re-run same command (already-processed instances are skipped)
