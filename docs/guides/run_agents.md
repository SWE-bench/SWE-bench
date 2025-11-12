# Running Coding Agents with SWE-bench

The `swebench/inference/run_agent.py` script allows you to run local coding agents on SWE-bench tasks inside the same Docker containers used for evaluation.

## Usage

```bash
python -m swebench.inference.run_agent \
    --dataset_name SWE-bench/SWE-bench_Lite \
    --split test \
    --agent_command 'prompt="$(cat $PROBLEM_STATEMENT)" ; claude --permission-mode bypassPermissions "$prompt"' \
    --output_dir ./agent_results \
    --max_workers 1 \
    --agent_name claude

```

## Key Features

- **Docker Integration**: Runs agents inside the same Docker containers used for SWE-bench evaluation
- **Problem Statement Parameterization**: Uses `$PROBLEM_STATEMENT` placeholder in commands as a path to a file with the problem statement
- **AGENTS.md / CLAUDE.md Parameterization**: Can add an optional `--agents_md <path_to_md>` flag which sets up an AGENTS.md and CLAUDE.md file prior to agent execution. 


## Output Format

Results are written in JSONL format compatible with SWE-bench evaluation:

```json
{
    "instance_id": "repo__issue-123",
    "model_patch": "diff --git a/file.py b/file.py\n...",
    "model_name_or_path": "agent",
    "agent_command": "claude-code --problem-statement-file /tmp/problem_statement.txt",
    "agent_output": "Agent's stdout/stderr output...",
    "git_diff": "Git diff of changes made..."
}
```

## Docker Container Behavior

1. **Container Creation**: Uses the same Docker images as SWE-bench evaluation
2. **Problem Statement**: Written to `/tmp/problem_statement.txt` inside container
3. **Working Directory**: Agent runs in the repository root (`/testbed` typically)
4. **Change Detection**: Git diff captures all changes made by the agent
5. **Cleanup**: Containers are automatically stopped and removed after each run

## Example Workflow

1. **Run Agent**: Execute coding agent on dataset instances
```bash
python -m swebench.inference.run_agent \
    --dataset_name SWE-bench/SWE-bench_Lite \
    --split test \
    --agent_command 'prompt="$(cat $PROBLEM_STATEMENT)" ; claude --permission-mode bypassPermissions "$prompt"' \
    --output_dir ./results
```

2. **Evaluate Results**: Use standard SWE-bench evaluation
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Lite \
    --predictions_path ./results/agent__SWE-bench_Lite__test.jsonl \
    --max_workers 4 \
    --run_id agent_evaluation
```
