import yaml

from swebench.harness.publish_results import upload_run, write_eval_result


def test_upload_run_dry_run(tmp_path):
    f = tmp_path / "report.json"
    f.write_text("{}")
    plan = upload_run("me/bucket", "run-1", [f], dry_run=True)
    assert plan == {"bucket": "me/bucket", "files": ["run-1/report.json"]}


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
