import json

import pytest
import yaml

from swebench.submit.hf import (
    DEFAULT_ENDPOINT,
    file_url,
    resolved_percent,
    upload_run,
    write_eval_result,
)


def _report(tmp_path, **fields):
    path = tmp_path / "report.json"
    path.write_text(
        json.dumps({"total_instances": 500, "resolved_instances": 210, **fields})
    )
    return path


def test_upload_run_dry_run_plans_paths_and_base_url(tmp_path):
    report = _report(tmp_path)
    plan = upload_run("me/bucket", "run-1", [report], dry_run=True)
    assert plan == {
        "bucket": "me/bucket",
        "files": ["run-1/report.json"],
        "base_url": f"{DEFAULT_ENDPOINT}/buckets/me/bucket",
    }


def test_upload_run_dry_run_honors_endpoint(tmp_path):
    plan = upload_run(
        "me/bucket",
        "run-1",
        [_report(tmp_path)],
        dry_run=True,
        endpoint="https://hub.internal/",
    )
    assert plan["base_url"] == "https://hub.internal/buckets/me/bucket"


def test_upload_run_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        upload_run("me/bucket", "run-1", [tmp_path / "nope.json"], dry_run=True)


def test_upload_run_rejects_colliding_basenames(tmp_path):
    # Distinct local files, same basename: both would map to run-1/report.json and the
    # second would silently overwrite the first.
    a = _report(tmp_path)
    other = tmp_path / "sub"
    other.mkdir()
    b = other / "report.json"
    b.write_text("{}")
    with pytest.raises(ValueError, match="collide"):
        upload_run("me/bucket", "run-1", [a, b], dry_run=True)


def test_file_url_uses_plan_base_url(tmp_path):
    plan = upload_run("me/bucket", "run-1", [_report(tmp_path)], dry_run=True)
    assert file_url(plan, "run-1/report.json") == (
        f"{DEFAULT_ENDPOINT}/buckets/me/bucket/resolve/run-1/report.json"
    )


def test_file_url_rejects_path_not_in_plan(tmp_path):
    plan = upload_run("me/bucket", "run-1", [_report(tmp_path)], dry_run=True)
    with pytest.raises(ValueError, match="not in this plan"):
        file_url(plan, "run-1/preds.jsonl")


def test_resolved_percent():
    assert resolved_percent({"total_instances": 500, "resolved_instances": 210}) == 42.0


@pytest.mark.parametrize(
    "report", [{}, {"total_instances": 0, "resolved_instances": 0}]
)
def test_resolved_percent_rejects_empty_report(report):
    # A report with no instances used to raise ZeroDivisionError from inside the CLI.
    with pytest.raises(ValueError, match="nothing to score"):
        resolved_percent(report)


def test_write_eval_result(tmp_path):
    out = write_eval_result(
        "SWE-bench/SWE-bench_Verified",
        "swe_bench_%_resolved",
        42.0,
        "https://example.com/report.json",
        tmp_path / "result.yaml",
    )
    assert yaml.safe_load(out.read_text()) == [
        {
            "dataset": {
                "id": "SWE-bench/SWE-bench_Verified",
                "task_id": "swe_bench_%_resolved",
            },
            "value": 42.0,
            "source": {"url": "https://example.com/report.json"},
        }
    ]


def test_write_eval_result_creates_parent_dirs(tmp_path):
    out = write_eval_result(
        "SWE-bench/SWE-bench_Verified",
        "swe_bench_%_resolved",
        1.0,
        "https://example.com/r.json",
        tmp_path / ".eval_results" / "result.yaml",
    )
    assert out.is_file()


# --- the CLI derives the report and the dataset from the run itself ------------


@pytest.fixture
def run(tmp_path, monkeypatch):
    """A finished run: logs/evaluation/<run_id>/{results.json,run.json}."""
    from swebench.harness import constants, run_evaluation
    from swebench.harness.constants import LOG_RUN_METADATA

    root = tmp_path / "logs" / "evaluation"
    monkeypatch.setattr(constants, "RUN_EVALUATION_LOG_DIR", root)
    monkeypatch.setattr(run_evaluation, "RUN_EVALUATION_LOG_DIR", root)

    def add(run_id="my-run", dataset="SWE-bench/SWE-bench_Verified", results=True):
        d = root / run_id
        d.mkdir(parents=True)
        if results:
            (d / "results.json").write_text(
                json.dumps({"total_instances": 500, "resolved_instances": 210})
            )
        if dataset:
            (d / LOG_RUN_METADATA).write_text(json.dumps({"dataset": dataset}))
        return d

    return add


def _invoke(*args):
    from typer.testing import CliRunner

    from swebench.cli.cli import app

    return CliRunner().invoke(app, ["submit", "hf", *args])


def test_report_and_dataset_come_from_the_run(run):
    run()
    result = _invoke("my-run", "-b", "me/bucket", "--dry-run")
    assert result.exit_code == 0, result.output
    assert "42.00" in result.output
    assert "SWE-bench/SWE-bench_Verified" in result.output


def test_missing_report_names_the_path_it_looked_in(run):
    run(results=False)
    result = _invoke("my-run", "-b", "me/bucket", "--dry-run")
    assert result.exit_code == 1
    assert "no report at" in result.output and "results.json" in result.output


def test_dataset_required_when_the_run_did_not_record_one(run):
    run(dataset=None)
    result = _invoke("my-run", "-b", "me/bucket", "--dry-run")
    assert result.exit_code == 1
    assert "did not record which dataset" in result.output


def test_explicit_dataset_overrides_the_run(run):
    run()
    result = _invoke("my-run", "-b", "me/bucket", "-d", "lite", "--dry-run")
    assert result.exit_code == 0
    assert "SWE-bench_Lite" in result.output
