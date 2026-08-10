# Command line interface

Installing the package provides a `swebench` command. Every command takes
`-h/--help`, and the top level takes `-v/--verbose`.

`DATASET` accepts an alias, a HuggingFace id, or a local path:

| alias | dataset |
|---|---|
| `full` | `SWE-bench/SWE-bench` |
| `lite` | `SWE-bench/SWE-bench_Lite` |
| `verified` | `SWE-bench/SWE-bench_Verified` |
| `multimodal`, `mm` | `SWE-bench/SWE-bench_Multimodal` |
| `multilingual`, `ml` | `SWE-bench/SWE-bench_Multilingual` |

## Evaluate

### `swebench eval DATASET`

Run the reference patches or a model's predictions.

```bash
swebench eval verified --gold
swebench eval lite -p preds.jsonl --run-id gpt5 -j 16
swebench eval multimodal --gold -i carbon-design-system__carbon-10188
swebench eval full --gold --modal
```

Pass exactly one of `--gold` or `-p/--predictions`. `-i/--instance` is
repeatable, `-j/--workers` sets parallelism, `-t/--timeout` is per instance.

### `swebench report RUN_ID`

Recompute verdicts from a finished run's saved logs, without starting
containers. Useful after a log-parser fix, since the test output is already on
disk.

```bash
swebench report my-run -d verified
swebench report my-run -d multimodal -i grommet__grommet-6282
```

## Images

Images are per instance but selected through a dataset, because the Dockerfile
comes from the instance row. Narrow with `-i`.

```bash
swebench images build verified -j 8
swebench images build multimodal -i carbon-design-system__carbon-10188
swebench images build lite --dry-run

swebench images check multilingual        # which images are missing from the registry
swebench images clean --run-id my-run     # remove leftover containers
```

`images check` is worth running before a long evaluation: it catches a stale or
partially-pushed image set in seconds rather than one instance at a time.

## Datasets

### `swebench dataset build DATASET`

Regenerate a dataset's parquet. This joins the public columns from HuggingFace
with the `eval_script`, `log_parser`, `eval_type` and `image` fields produced by
the dockerfile repositories' generators. Run it after changing a generator, then
push the result to HuggingFace.

```bash
swebench dataset build multimodal -s test
swebench dataset build verified --dockerfile-repos ~/code
```

It expects the `swe-bench-dockerfiles`, `swe-bench-multilingual-dockerfiles` and
`swe-bench-multimodal-dockerfiles` checkouts, found via `--dockerfile-repos` or
`SWEBENCH_DOCKERFILE_REPOS`.

### `swebench dataset collect REPOS...`

Scrape pull requests from GitHub into candidate task instances.

```bash
swebench dataset collect scikit-learn/scikit-learn
swebench dataset collect psf/requests --max-pulls 200 --cutoff-date 20230101
```

### `swebench dataset versions INSTANCES_PATH`

Attach a version to each candidate instance. Install specs are keyed by version,
so instances without one cannot be built.

```bash
swebench dataset versions tasks/scikit-learn-task-instances.jsonl
swebench dataset versions tasks/foo.jsonl --retrieval-method build --testbed /tmp/tb
```

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
