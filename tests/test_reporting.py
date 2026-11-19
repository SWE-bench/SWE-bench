"""Where make_run_report writes its results.json.

Always the run's own log directory. It used to land relative to the CWD, which meant a
run report appeared wherever the command happened to be invoked from (#498).
"""

import json

import pytest

from swebench.harness import reporting
from swebench.harness.reporting import make_run_report


def _fixture():
    predictions = {
        "x__x-1": {
            "instance_id": "x__x-1",
            "model_name_or_path": "gold",
            "model_patch": "diff",
        }
    }
    full_dataset = [{"instance_id": "x__x-1"}]
    return predictions, full_dataset


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    """RUN_EVALUATION_LOG_DIR is CWD-relative; point it somewhere disposable."""
    root = tmp_path / "logs" / "evaluation"
    monkeypatch.setattr(reporting, "RUN_EVALUATION_LOG_DIR", root)
    return root


def test_report_is_named_results_json(log_dir):
    predictions, full_dataset = _fixture()
    out = make_run_report(predictions, full_dataset, "run-a")
    assert out == log_dir / "run-a" / "results.json"
    assert out.exists()


def test_the_log_directory_is_created_if_absent(log_dir):
    predictions, full_dataset = _fixture()
    assert not log_dir.exists()
    out = make_run_report(predictions, full_dataset, "run-b")
    assert out.exists()


def test_defaults_into_the_runs_log_directory(log_dir):
    predictions, full_dataset = _fixture()
    out = make_run_report(predictions, full_dataset, "run-c")
    assert out == log_dir / "run-c" / "results.json"
    assert out.exists()


def test_two_runs_do_not_collide(log_dir):
    predictions, full_dataset = _fixture()
    a = make_run_report(predictions, full_dataset, "run-a")
    b = make_run_report(predictions, full_dataset, "run-b")
    assert a != b and a.exists() and b.exists()


def test_default_does_not_write_into_the_cwd(log_dir, tmp_path, monkeypatch):
    # the old default dropped gold.<run_id>.json wherever the command was invoked
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    predictions, full_dataset = _fixture()
    make_run_report(predictions, full_dataset, "run-d")
    assert list(cwd.iterdir()) == []


@pytest.mark.parametrize(
    "report",
    [
        pytest.param(None, id="null-report"),
        pytest.param([], id="list-report"),
        pytest.param("report", id="string-report"),
        pytest.param(1, id="number-report"),
        pytest.param(True, id="boolean-report"),
        pytest.param({}, id="missing-instance"),
        pytest.param({"x__x-1": None}, id="null-instance"),
        pytest.param({"x__x-1": []}, id="list-instance"),
        pytest.param({"x__x-1": "result"}, id="string-instance"),
        pytest.param({"x__x-1": 1}, id="number-instance"),
        pytest.param({"x__x-1": {}}, id="missing-resolved"),
        *[
            pytest.param({"x__x-1": {"resolved": value}}, id=f"resolved-{name}")
            for name, value in [
                ("null", None),
                ("string-false", "false"),
                ("empty-string", ""),
                ("zero", 0),
                ("one", 1),
                ("empty-list", []),
                ("list", [False]),
                ("empty-object", {}),
                ("object", {"value": False}),
            ]
        ],
    ],
)
def test_invalid_report_is_an_error_without_losing_other_results(log_dir, report):
    predictions, full_dataset = _fixture()
    other_id = "x__x-2"
    predictions[other_id] = {**predictions["x__x-1"], "instance_id": other_id}
    full_dataset.append({"instance_id": other_id})
    for iid, payload in [
        ("x__x-1", report),
        (other_id, {other_id: {"resolved": True}}),
    ]:
        path = log_dir / "run-a" / "gold" / iid / reporting.LOG_REPORT
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    out = make_run_report(predictions, full_dataset, "run-a")
    summary = json.loads(out.read_text(encoding="utf-8"))
    assert summary["error_ids"] == ["x__x-1"]
    assert summary["resolved_ids"] == [other_id]
    assert summary["unresolved_ids"] == []
    assert summary["completed_ids"] == ["x__x-1", other_id]
    assert summary["error_instances"] == 1
    assert summary["resolved_instances"] == 1
    assert summary["unresolved_instances"] == 0


@pytest.mark.parametrize("resolved", [True, False])
def test_boolean_report_result_is_preserved(log_dir, resolved):
    predictions, full_dataset = _fixture()
    iid = "x__x-1"
    path = log_dir / "run-a" / "gold" / iid / reporting.LOG_REPORT
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({iid: {"resolved": resolved, "patch_successfully_applied": True}}),
        encoding="utf-8",
    )

    out = make_run_report(predictions, full_dataset, "run-a")
    summary = json.loads(out.read_text(encoding="utf-8"))
    assert summary["resolved_ids"] == ([iid] if resolved else [])
    assert summary["unresolved_ids"] == ([] if resolved else [iid])
    assert summary["error_ids"] == []
    assert summary["completed_ids"] == [iid]
