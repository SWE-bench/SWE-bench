"""
Tests for the LiteLLM inference path in swebench/inference/run_api.py.

`litellm` is an optional dependency, so we install a lightweight stub in
sys.modules before importing run_api. This lets the suite run without the real
package and lets us assert exactly what gets passed to litellm.completion.
"""

import sys
import types
from types import SimpleNamespace
from unittest import mock

import pytest

# --- install a fake `litellm` before importing run_api -----------------------
_fake_litellm = types.ModuleType("litellm")
_fake_litellm.completion = mock.MagicMock(name="litellm.completion")
_fake_litellm.completion_cost = mock.MagicMock(
    name="litellm.completion_cost", return_value=0.01
)
_fake_litellm.get_model_info = mock.MagicMock(
    name="litellm.get_model_info", return_value={"max_input_tokens": 100_000}
)
_fake_litellm.token_counter = mock.MagicMock(
    name="litellm.token_counter", return_value=10
)


class _ContextWindowExceededError(Exception):
    pass


_fake_litellm.ContextWindowExceededError = _ContextWindowExceededError
sys.modules["litellm"] = _fake_litellm

# run_api also imports tiktoken at module scope, which ships in the optional
# `datasets`/`inference` extras -- skip rather than fail collection without them
pytest.importorskip("tiktoken")

from swebench.inference import run_api  # noqa: E402


def _response(content="hello", prompt_tokens=20, completion_tokens=5):
    """An OpenAI-shaped response like litellm.completion returns."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    )


class _FakeDataset:
    """Minimal stand-in for a HF Dataset (filter/iterate/len)."""

    def __init__(self, rows):
        self.rows = rows

    def filter(self, fn, **kwargs):
        return _FakeDataset([r for r in self.rows if fn(r)])

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)


def test_call_litellm_passes_expected_kwargs():
    _fake_litellm.completion.reset_mock(return_value=True, side_effect=True)
    _fake_litellm.completion.return_value = _response()

    _, cost = run_api.call_litellm(
        "anthropic/claude-3-5-sonnet-20240620",
        "system line\nuser body line",
        0.2,
        0.95,
    )

    kwargs = _fake_litellm.completion.call_args.kwargs
    assert kwargs["model"] == "anthropic/claude-3-5-sonnet-20240620"
    assert kwargs["drop_params"] is True
    assert kwargs["temperature"] == 0.2
    assert kwargs["top_p"] == 0.95
    # First line is the system message, the rest is the user message.
    assert kwargs["messages"] == [
        {"role": "system", "content": "system line"},
        {"role": "user", "content": "user body line"},
    ]
    assert cost == 0.01


def test_call_litellm_returns_none_on_context_window():
    _fake_litellm.completion.reset_mock(return_value=True, side_effect=True)
    _fake_litellm.completion.side_effect = _ContextWindowExceededError("too long")

    result = run_api.call_litellm("gpt-4o", "sys\nuser", 0.0, 1.0)
    assert result is None


def test_call_litellm_raises_when_pricing_is_missing():
    _fake_litellm.completion.reset_mock(return_value=True, side_effect=True)
    _fake_litellm.completion.return_value = _response()
    _fake_litellm.completion_cost.side_effect = ValueError("pricing unavailable")

    try:
        with pytest.raises(ValueError, match="pricing unavailable"):
            run_api.call_litellm.__wrapped__("gpt-4o", "sys\nuser", 0.0, 1.0)
    finally:
        _fake_litellm.completion_cost.side_effect = None


def test_litellm_inference_writes_output(tmp_path):
    _fake_litellm.completion.reset_mock(return_value=True, side_effect=True)
    _fake_litellm.completion.return_value = _response(content="```diff\n+patch\n```")
    out = tmp_path / "out.jsonl"
    dataset = _FakeDataset(
        [{"instance_id": "repo__x-1", "text": "system\nuser prompt"}]
    )

    run_api.litellm_inference(
        test_dataset=dataset,
        model_name_or_path="gemini/gemini-2.5-flash",
        output_file=str(out),
        model_args={},
        existing_ids=set(),
        max_cost=None,
    )

    import json

    lines = out.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["instance_id"] == "repo__x-1"
    assert record["model_name_or_path"] == "gemini/gemini-2.5-flash"
    assert "full_output" in record and "model_patch" in record
    # token_counter is consulted for length filtering against the model window.
    _fake_litellm.token_counter.assert_called()


def test_litellm_inference_skips_existing_ids(tmp_path):
    _fake_litellm.completion.reset_mock(return_value=True, side_effect=True)
    _fake_litellm.completion.return_value = _response()
    out = tmp_path / "out.jsonl"
    dataset = _FakeDataset([{"instance_id": "dup-1", "text": "s\nu"}])

    run_api.litellm_inference(
        test_dataset=dataset,
        model_name_or_path="gpt-4o",
        output_file=str(out),
        model_args={},
        existing_ids={"dup-1"},
        max_cost=None,
    )

    assert not out.exists() or out.read_text().strip() == ""
    _fake_litellm.completion.assert_not_called()
