Evaluate SWE-bench Multilingual with gold patches:

```
PYTHONUNBUFFERED=1 uv run python -m swebench.harness.run_evaluation \ 
    --dataset_name SWE-bench/SWE-bench_Multilingual \
    --split test \
    --predictions_path gold \
    --max_workers 100 \
    --modal True \
    --run_id validate-gold &> gold-multilingual.log
```
