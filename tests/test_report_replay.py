from types import SimpleNamespace

import pytest

from swebench.harness import run_evaluation


def _write_model_log(run_dir, model_dir, instance_id, patch="diff"):
    instance_dir = run_dir / model_dir / instance_id
    instance_dir.mkdir(parents=True)
    (instance_dir / "patch.diff").write_text(patch)
    (instance_dir / "test_output.txt").write_text("saved test output")
    return instance_dir


def test_saved_predictions_auto_select_single_model(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evaluation, "RUN_EVALUATION_LOG_DIR", tmp_path)
    _write_model_log(tmp_path / "run", "my-agent", "repo__issue-1")

    predictions = run_evaluation.get_saved_predictions("run")

    assert predictions == [
        {
            "instance_id": "repo__issue-1",
            "model_name_or_path": "my-agent",
            "model_patch": "diff",
        }
    ]


def test_saved_predictions_accept_model_name_with_slash(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evaluation, "RUN_EVALUATION_LOG_DIR", tmp_path)
    _write_model_log(tmp_path / "run", "org__model", "repo__issue-1")

    predictions = run_evaluation.get_saved_predictions("run", "org/model")

    assert predictions[0]["model_name_or_path"] == "org/model"
    assert predictions[0]["model_patch"] == "diff"


def test_saved_predictions_require_model_when_run_is_ambiguous(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(run_evaluation, "RUN_EVALUATION_LOG_DIR", tmp_path)
    _write_model_log(tmp_path / "run", "agent-a", "repo__issue-1")
    _write_model_log(tmp_path / "run", "agent-b", "repo__issue-1")

    with pytest.raises(ValueError, match="multiple models.*--model"):
        run_evaluation.get_saved_predictions("run")


def test_saved_predictions_keep_gold_replay_as_default(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evaluation, "RUN_EVALUATION_LOG_DIR", tmp_path)
    (tmp_path / "run" / "gold").mkdir(parents=True)

    assert run_evaluation.get_saved_predictions("run") is None


def test_report_replay_does_not_connect_to_docker(tmp_path, monkeypatch):
    instance = {"instance_id": "repo__issue-1"}
    predictions = [
        {
            "instance_id": "repo__issue-1",
            "model_name_or_path": "my-agent",
            "model_patch": "diff",
        }
    ]
    monkeypatch.setattr(run_evaluation, "RUN_EVALUATION_LOG_DIR", tmp_path)
    monkeypatch.setattr(run_evaluation, "_docker_client", lambda: pytest.fail("Docker is not needed"))
    monkeypatch.setattr(run_evaluation, "write_run_metadata", lambda *args: None)
    monkeypatch.setattr(run_evaluation, "get_dataset_from_preds", lambda *args, **kwargs: [])
    monkeypatch.setattr(run_evaluation, "load_instances", lambda *args: [instance])

    report_call = {}

    def make_report(*args):
        report_call["args"] = args
        return tmp_path / "results.json"

    monkeypatch.setattr(run_evaluation, "make_run_report", make_report)
    result = run_evaluation.main(
        dataset_name="local.json",
        split="test",
        instance_ids=None,
        predictions_path="gold",
        max_workers=1,
        open_file_limit=4096,
        run_id="run",
        timeout=60,
        rewrite_reports=True,
        modal=False,
        predictions_override=predictions,
    )

    assert result == tmp_path / "results.json"
    assert report_call["args"][0]["repo__issue-1"] == predictions[0]
    assert report_call["args"][3] is None


def test_run_instances_replay_does_not_connect_to_docker(monkeypatch):
    instance_id = "repo__issue-1"
    prediction = {
        "instance_id": instance_id,
        "model_name_or_path": "my-agent",
        "model_patch": "diff",
    }
    monkeypatch.setattr(run_evaluation, "_docker_client", lambda: pytest.fail("Docker is not needed"))
    monkeypatch.setattr(run_evaluation, "make_test_spec", lambda instance: instance)

    def capture_payloads(func, payloads, max_workers):
        assert max_workers == 1
        assert len(payloads) == 1
        assert payloads[0][2] is None

    monkeypatch.setattr(run_evaluation, "run_threadpool", capture_payloads)
    run_evaluation.run_instances(
        predictions={instance_id: prediction},
        instances=[SimpleNamespace(instance_id=instance_id)],
        max_workers=1,
        run_id="run",
        timeout=60,
        rewrite_reports=True,
    )
