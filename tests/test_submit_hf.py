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
