# Command line interface

Installing the package provides a `swebench` command. Every command takes
`-h/--help`, and the top level takes `-v/--verbose`.

`DATASET` accepts an alias, a HuggingFace id, or a local path:

| alias | dataset |
|---|---|
| `full` | `SWE-bench/SWE-bench` |
| `verified` | `SWE-bench/SWE-bench_Verified` |
| `multimodal` | `SWE-bench/SWE-bench_Multimodal` |
| `multilingual` | `SWE-bench/SWE-bench_Multilingual` |

## Evaluate

### `swebench infer DATASET`

Generate predictions with [mini-SWE-agent](https://mini-swe-agent.com), writing
`preds.json` plus one trajectory per instance.

A thin wrapper around `mini-extra swebench`: it resolves SWE-bench's dataset aliases
(so `infer` and `eval` read the same dataset, rather than mini's older
`princeton-nlp/*` mirrors) and passes mini's bundled config explicitly, because mini
drops its own default as soon as any `-c` is given. Unrecognized arguments are
forwarded to mini, so `--filter`, `--slice` and the rest work as documented there.

```bash
swebench infer verified -m gpt-5 -o preds -w 8
swebench infer verified -c model.yaml -w 12 -o output
swebench infer lite -m gpt-5 --dry-run -- --filter "astropy.*"
```

If mini-SWE-agent lives in a different environment than `swebench`, point at it with
`--python /path/to/venv/bin/python`.

API keys are mini's business, not this command's -- export whatever the provider reads
before running. Note that `api_key: os.environ/VAR` inside a model config is **not**
resolved by litellm outside its proxy: it is sent as that literal string. Set the real
environment variable instead (for an OpenAI-compatible endpoint, `OPENAI_API_KEY`).

### `swebench eval DATASET`

Run the reference patches or a model's predictions.

```bash
swebench eval verified --gold
swebench eval verified -p preds.jsonl --run-id gpt5 -j 16
swebench eval multimodal --gold -i carbon-design-system__carbon-10188
swebench eval full --gold --modal
```

Pass exactly one of `--gold` or `-p/--predictions`. `-i/--instance` is
repeatable, `-j/--workers` sets parallelism, `-t/--timeout` is per instance.

### `swebench report RUN_ID`

Recompute verdicts from a finished run's saved logs, without starting
containers. Useful after a log-parser fix, since the test output is already on
disk.

The dataset comes from the run itself, recorded at evaluation time in
`logs/run_evaluation/<run_id>/run.json`. Pass `-d` for runs made before that was
added, or to grade against a different dataset on purpose.

```bash
swebench report my-run                     # dataset taken from the run itself
swebench report my-run -d multimodal -i grommet__grommet-6282
```

## Submit

Submission commands live under `swebench submit`. Two destinations:
the SWE-bench leaderboard (via
[`SWE-bench/experiments`](https://github.com/SWE-bench/experiments)) and
HuggingFace's community eval-results system.

### `swebench submit hf RUN_ID`

Upload a run's report (and optionally its predictions) to a HuggingFace bucket,
and write a `.eval_results/*.yaml` entry scored against it
([format](https://huggingface.co/docs/hub/eval-results)).

The score comes from the report's own `resolved_instances` / `total_instances`,
and the entry's `source.url` points at the uploaded report. Buckets are created
private unless you pass `--public`; a private bucket means that URL is not
readable by anyone else, so `--public` is what you want for a shared entry.

```bash
swebench submit hf my-run -b myuser/swebench-runs --report gpt5.my-run.json -d verified --public
swebench submit hf my-run -b myuser/runs --report r.json -d verified --dry-run
```

Requires the `submit` extra (`pip install swebench[submit]`) for bucket support.

## Images

Images are built from a task repo: each task carries its own Dockerfile, and its
`task.yaml` names the image the dataset will tell the harness to pull. Narrow
with `-i`, which can name a task in an unpublished split.

```bash
swebench images build ~/swe-bench-tasks -j 8
swebench images build ~/swe-bench-multimodal-tasks -i carbon-design-system__carbon-10188
swebench images build ~/swe-bench-tasks --dry-run

swebench images check ~/swe-bench-tasks    # which images are missing from the registry
swebench images push  ~/swe-bench-tasks    # publish them, under the names task.yaml declares
swebench images clean --run-id my-run      # remove leftover containers
```

`images check` is worth running before a long evaluation: it catches a stale or
partially-pushed image set in seconds rather than one instance at a time.
`images push --dry-run` prints the exact `docker push` commands and stops.

## Datasets

A task repo holds one directory per instance:

```
sweb.yaml                    the dataset this repo publishes, and its splits
tasks/<instance_id>/
    task.yaml                short metadata, including which split the task is in
    tests.json               the tests that decide whether a patch resolved it
    problem_statement.md     the issue text shown to a model
    hints.md                 discussion from the issue, absent when there is none
    gold.patch               the reference fix
    test.patch               the tests that grade it
    eval.sh                  the script the harness runs
    Dockerfile               the image it runs in
    assets/                  binary files a patch cannot carry
```

The tree is the source of truth. Nothing below reads HuggingFace to build the
dataset, so a new dataset can be developed entirely locally.

### `swebench dataset check TASK_REPO`

Check that a task repo is well formed: every task has its files, its metadata,
and a split registered in `sweb.yaml`. This runs automatically before building
or publishing, so a malformed tree is never published.

```bash
swebench dataset check ~/swe-bench-tasks
swebench dataset check ~/swe-bench-tasks --fix   # write back what the tree implies
```

`--fix` only writes what can be derived from the tree itself: the split list in
`sweb.yaml`, and image names that follow the naming convention. It never
invents data it cannot see.

### `swebench dataset build TASK_REPO`

Compile the repo into one parquet per split.

```bash
swebench dataset build ~/swe-bench-multilingual-tasks
swebench dataset build ~/swe-bench-tasks -o /tmp/parquets
```

### `swebench dataset diff TASK_REPO`

Show how the tree differs from the dataset it publishes, per column.

```bash
swebench dataset diff ~/swe-bench-multilingual-tasks
```

### `swebench dataset push TASK_REPO`

Overwrite the HuggingFace dataset named in `sweb.yaml`.

```bash
swebench dataset push ~/swe-bench-tasks --dry-run
swebench dataset push ~/swe-bench-tasks
```

A task whose split is not published, `deprecated` for example, stays in the tree
and can still be built by id, but never reaches the dataset.

### `swebench dataset collect REPOS...`

Scrape pull requests from GitHub into candidate task instances.

```bash
swebench dataset collect scikit-learn/scikit-learn
swebench dataset collect psf/requests --max-pulls 200 --cutoff-date 20230101
```

Versioning candidate instances is no longer part of this CLI. That tooling lives with
the task data, at [swe-bench-tasks/src/versioning](https://github.com/SWE-bench/swe-bench-tasks/tree/main/src/versioning).

## Older invocations

Every module is still runnable directly, with the same arguments as before:

```bash
python -m swebench.harness.run_evaluation --dataset_name ... --predictions_path ...
python -m swebench.image_builder.prepare_images --dataset_name ...
```

The inference utilities are not exposed through `swebench` and are run this way:

```bash
python -m swebench.inference.run_api --help
```
