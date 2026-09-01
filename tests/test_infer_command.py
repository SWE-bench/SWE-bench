"""`swebench infer` -- assembling a mini-SWE-agent invocation."""

import sys

import pytest

from swebench.inference import mini_swe_agent as msa


@pytest.fixture
def bundled_config(tmp_path, monkeypatch):
    """Stub mini's bundled config so no real install is needed."""
    cfg = tmp_path / "swebench.yaml"
    cfg.write_text("agent: {}\n")
    monkeypatch.setattr(msa, "default_config", lambda python=None: cfg)
    return cfg


def test_command_shape(bundled_config, tmp_path):
    cmd = msa.build_command(
        "SWE-bench/SWE-bench_Verified", output=tmp_path / "out", workers=12
    )
    assert cmd[:3] == [sys.executable, "-m", msa.RUNNER_MODULE]
    assert cmd[3:9] == [
        "--subset",
        "SWE-bench/SWE-bench_Verified",
        "--split",
        "test",
        "-w",
        "12",
    ]
    assert "-o" in cmd and str(tmp_path / "out") in cmd


def test_bundled_config_is_passed_explicitly(bundled_config, tmp_path):
    # mini drops its own default as soon as any -c is given, so ours must come first
    cmd = msa.build_command("d", output=tmp_path, configs=("model.yaml",))
    idx = [i for i, a in enumerate(cmd) if a == "-c"]
    assert cmd[idx[0] + 1] == str(bundled_config)
    assert cmd[idx[1] + 1] == "model.yaml"


def test_extra_args_are_appended_last(bundled_config, tmp_path):
    cmd = msa.build_command(
        "d", output=tmp_path, extra=("--filter", "astropy.*"), model="gpt-5"
    )
    assert cmd[-2:] == ["--filter", "astropy.*"]
    assert "-m" in cmd and "gpt-5" in cmd


def test_model_omitted_when_not_given(bundled_config, tmp_path):
    # "-m" also introduces the module, so count rather than test membership
    assert msa.build_command("d", output=tmp_path).count("-m") == 1
    assert msa.build_command("d", output=tmp_path, model="gpt-5").count("-m") == 2


def test_python_override_selects_the_interpreter(bundled_config, tmp_path):
    cmd = msa.build_command("d", output=tmp_path, python="/venv/bin/python")
    assert cmd[0] == "/venv/bin/python"


def test_probe_returns_last_line_ignoring_banner():
    # mini prints a version banner on import; only the snippet's own output matters
    got = msa._probe(sys.executable, "print('banner line'); print('the-real-answer')")
    assert got == "the-real-answer"


def test_probe_returns_none_on_failure():
    assert msa._probe(sys.executable, "raise SystemExit(3)") is None


def test_probe_returns_none_for_missing_interpreter():
    assert msa._probe("/definitely/not/a/python", "print(1)") is None


def test_is_available_false_for_interpreter_without_mini():
    assert msa.is_available("/definitely/not/a/python") is False


def test_default_config_errors_when_interpreter_lacks_mini():
    with pytest.raises(msa.InferenceError, match="cannot import mini-SWE-agent"):
        msa.default_config(python="/definitely/not/a/python")


def test_run_rejects_missing_interpreter():
    with pytest.raises(msa.InferenceError, match="interpreter not found"):
        msa.run(["/definitely/not/a/python", "-m", "whatever"])


def test_cli_reports_missing_mini(monkeypatch):
    from typer.testing import CliRunner

    from swebench.cli.cli import app

    monkeypatch.setattr(msa, "is_available", lambda python=None: False)
    result = CliRunner().invoke(app, ["infer", "verified", "--dry-run"])
    assert result.exit_code == 1
    assert "not installed" in result.output


def test_cli_resolves_dataset_alias(monkeypatch, bundled_config):
    from typer.testing import CliRunner

    from swebench.cli.cli import app

    monkeypatch.setattr(msa, "is_available", lambda python=None: True)
    result = CliRunner().invoke(app, ["infer", "verified", "--dry-run"])
    assert result.exit_code == 0
    assert "SWE-bench/SWE-bench_Verified" in result.output


def test_cli_forwards_unknown_options(monkeypatch, bundled_config):
    from typer.testing import CliRunner

    from swebench.cli.cli import app

    monkeypatch.setattr(msa, "is_available", lambda python=None: True)
    result = CliRunner().invoke(
        app, ["infer", "lite", "--dry-run", "--filter", "astropy.*"]
    )
    assert result.exit_code == 0
    assert "--filter astropy.*" in result.output


def test_output_defaults_under_logs_inference(monkeypatch, bundled_config):
    from typer.testing import CliRunner

    from swebench.cli.cli import app

    monkeypatch.setattr(msa, "is_available", lambda python=None: True)
    result = CliRunner().invoke(
        app, ["infer", "verified", "--run-id", "g5", "--dry-run"]
    )
    assert "logs/inference/g5" in result.output


def test_explicit_output_wins(monkeypatch, bundled_config):
    from typer.testing import CliRunner

    from swebench.cli.cli import app

    monkeypatch.setattr(msa, "is_available", lambda python=None: True)
    result = CliRunner().invoke(
        app, ["infer", "verified", "-o", "/custom/dir", "--dry-run"]
    )
    assert "/custom/dir" in result.output and "logs/inference" not in result.output
