"""Dataset name resolution shared by the CLI commands."""

# One spelling per dataset. Anything else, including a full HuggingFace id or a
# local path, passes through untouched.
DATASET_ALIASES = {
    "full": "SWE-bench/SWE-bench",
    "lite": "SWE-bench/SWE-bench_Lite",
    "verified": "SWE-bench/SWE-bench_Verified",
    "multilingual": "SWE-bench/SWE-bench_Multilingual",
    "multimodal": "SWE-bench/SWE-bench_Multimodal",
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
