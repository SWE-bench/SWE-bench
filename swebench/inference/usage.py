"""Helpers for preserving provider token usage details in inference outputs."""

from __future__ import annotations

from typing import Any


def _usage_value(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def usage_to_dict(
    usage: Any,
    *,
    input_tokens_field: str,
    output_tokens_field: str,
) -> dict[str, Any]:
    """Normalize SDK usage objects into JSON-serializable token counters."""
    if usage is None:
        return {}

    result = {}

    input_tokens = _usage_value(usage, input_tokens_field)
    output_tokens = _usage_value(usage, output_tokens_field)
    if input_tokens is not None:
        result["input_tokens"] = input_tokens
    if output_tokens is not None:
        result["output_tokens"] = output_tokens

    token_details = (
        _usage_value(usage, "prompt_tokens_details")
        or _usage_value(usage, "input_tokens_details")
    )
    cached_input_tokens = _usage_value(token_details, "cached_tokens")
    cache_creation_input_tokens = _usage_value(usage, "cache_creation_input_tokens")
    cache_read_input_tokens = _usage_value(usage, "cache_read_input_tokens")

    if cache_read_input_tokens is not None and cached_input_tokens is None:
        cached_input_tokens = cache_read_input_tokens

    if cached_input_tokens is not None:
        result["cached_input_tokens"] = cached_input_tokens
    if cache_creation_input_tokens is not None:
        result["cache_creation_input_tokens"] = cache_creation_input_tokens
    if cache_read_input_tokens is not None:
        result["cache_read_input_tokens"] = cache_read_input_tokens

    return result
