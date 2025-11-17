# CLI Docker Specs Example

This example demonstrates how to use the `--docker_spec` CLI argument to override docker specifications at runtime.

## Example Scenario

You have a dataset with tasks that use Ubuntu 20.04 and Python 3.9 by default, but you want to test with Ubuntu 22.04 and Python 3.11 without modifying the dataset files.

## Dataset Configuration

Your dataset (`tasks.jsonl`) has:

```json
{
  "instance_id": "task-1",
  "repo": "psf/requests",
  "version": "2.31",
  "base_commit": "abc123",
  "problem_statement": "Fix the connection pool issue",
  ...
}
```

And the repository specs in `MAP_REPO_VERSION_TO_SPECS` define:

```python
"psf/requests": {
    "2.31": {
        "docker_specs": {
            "ubuntu_version": "20.04",
            "python_version": "3.9"
        }
    }
}
```

## Running with Default Specs

```bash
python -m swebench.harness.run_evaluation \
  --dataset_name tasks.jsonl \
  --predictions_path predictions.jsonl \
  --run_id default_run \
  --namespace ''
```

This will use:
- Ubuntu 20.04
- Python 3.9

## Running with CLI Override

```bash
python -m swebench.harness.run_evaluation \
  --dataset_name tasks.jsonl \
  --predictions_path predictions.jsonl \
  --run_id override_run \
  --namespace '' \
  --docker_spec ubuntu_version=22.04 \
  --docker_spec python_version=3.11
```

This will use:
- Ubuntu 22.04 ✓ (overridden)
- Python 3.11 ✓ (overridden)

## Using Environment Variables

You can also use environment variables:

```bash
export UBUNTU_VERSION=22.04
export PYTHON_VERSION=3.11

python -m swebench.harness.run_evaluation \
  --dataset_name tasks.jsonl \
  --predictions_path predictions.jsonl \
  --run_id env_run \
  --namespace '' \
  --docker_spec ubuntu_version=$UBUNTU_VERSION \
  --docker_spec python_version=$PYTHON_VERSION
```

## With run_agent

The same feature works with `run_agent`:

```bash
python -m swebench.inference.run_agent \
  --dataset_name tasks.jsonl \
  --agent_name claude \
  --agent_command 'claude --permission-mode bypassPermissions "$(cat $PROBLEM_STATEMENT)"' \
  --output_dir ./results \
  --namespace '' \
  --docker_spec ubuntu_version=22.04 \
  --docker_spec python_version=3.11
```

## Combining with Custom Dockerfiles

If you have a custom Dockerfile that uses template variables:

**Dataset with custom Dockerfile:**
```json
{
  "instance_id": "task-1",
  "dockerfile_base": {
    "contents": "FROM ubuntu:{ubuntu_version}\nRUN apt-get update && apt-get install -y python{python_version}"
  }
}
```

**Run with override:**
```bash
python -m swebench.harness.run_evaluation \
  --docker_spec ubuntu_version=22.04 \
  --docker_spec python_version=3.11 \
  ...
```

The Dockerfile will be rendered as:
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y python3.11
```

## Image Key Generation

Different docker specs result in different image keys:

```bash
# Run 1: Creates image with key including hash of ubuntu_version=20.04
--docker_spec ubuntu_version=20.04

# Run 2: Creates different image with different key
--docker_spec ubuntu_version=22.04
```

This ensures proper caching and avoids conflicts between different configurations.

## Validation

The CLI parser validates the format:

```bash
# ✓ Correct
--docker_spec ubuntu_version=22.04

# ✗ Wrong - missing equals sign
--docker_spec ubuntu_version

# ✗ Wrong - will give you an error
--docker_spec "ubuntu version=22.04"  # no spaces in key name
```

## Use Cases

1. **Testing different versions**: Quickly test your evaluation with different Python/Ubuntu versions
2. **CI/CD integration**: Pass versions from pipeline variables
3. **Experimentation**: Try different configurations without modifying dataset files
4. **Reproducibility**: Document exact versions used in your runs via CLI args

