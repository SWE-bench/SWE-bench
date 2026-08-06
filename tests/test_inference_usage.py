from types import SimpleNamespace

from swebench.inference.usage import usage_to_dict


def test_usage_to_dict_preserves_openai_cached_tokens():
    usage = SimpleNamespace(
        prompt_tokens=100,
        completion_tokens=20,
        prompt_tokens_details=SimpleNamespace(cached_tokens=40),
    )

    assert usage_to_dict(
        usage,
        input_tokens_field="prompt_tokens",
        output_tokens_field="completion_tokens",
    ) == {
        "input_tokens": 100,
        "output_tokens": 20,
        "cached_input_tokens": 40,
    }


def test_usage_to_dict_preserves_anthropic_cache_tokens():
    usage = SimpleNamespace(
        input_tokens=100,
        output_tokens=20,
        cache_creation_input_tokens=15,
        cache_read_input_tokens=35,
    )

    assert usage_to_dict(
        usage,
        input_tokens_field="input_tokens",
        output_tokens_field="output_tokens",
    ) == {
        "input_tokens": 100,
        "output_tokens": 20,
        "cached_input_tokens": 35,
        "cache_creation_input_tokens": 15,
        "cache_read_input_tokens": 35,
    }


def test_usage_to_dict_handles_dict_details():
    usage = {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "prompt_tokens_details": {"cached_tokens": 40},
    }

    assert usage_to_dict(
        usage,
        input_tokens_field="prompt_tokens",
        output_tokens_field="completion_tokens",
    ) == {
        "input_tokens": 100,
        "output_tokens": 20,
        "cached_input_tokens": 40,
    }
