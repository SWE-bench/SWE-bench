"""Dataset name resolution shared by the CLI commands."""

DATASET_ALIASES = {
    "full": "SWE-bench/SWE-bench",
    "swe-bench": "SWE-bench/SWE-bench",
    "lite": "SWE-bench/SWE-bench_Lite",
    "verified": "SWE-bench/SWE-bench_Verified",
    "multimodal": "SWE-bench/SWE-bench_Multimodal",
    "mm": "SWE-bench/SWE-bench_Multimodal",
    "multilingual": "SWE-bench/SWE-bench_Multilingual",
    "ml": "SWE-bench/SWE-bench_Multilingual",
}


def resolve_dataset(name: str) -> str:
    """Expand a short alias; pass anything else through untouched.

    A HuggingFace id or a local path is returned as given, so the aliases are a
    convenience and never the only way to name a dataset.
    """
    return DATASET_ALIASES.get(name.strip().lower(), name)


def alias_help() -> str:
    seen, pairs = set(), []
    for alias, full in DATASET_ALIASES.items():
        if full in seen:
            continue
        seen.add(full)
        pairs.append(f"{alias} -> {full.split('/')[-1]}")
    return ", ".join(pairs)
