from swebench.harness.test_spec.test_spec import make_test_spec
from swebench.harness.test_spec.utils import (
    parse_instance_list_field,
    resolve_repo_version_spec,
)


PRO_REPOS = [
    "NodeBB/NodeBB",
    "ansible/ansible",
    "element-hq/element-web",
    "flipt-io/flipt",
    "future-architect/vuls",
    "gravitational/teleport",
    "internetarchive/openlibrary",
    "navidrome/navidrome",
    "protonmail/webclients",
    "qutebrowser/qutebrowser",
    "tutao/tutanota",
]


def _instance_for_repo(repo: str) -> dict:
    return {
        "instance_id": f"instance_{repo.replace('/', '__')}-dummy",
        "repo": repo,
        "base_commit": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "patch": "",
        "test_patch": "",
        "problem_statement": "Dummy",
        "fail_to_pass": "['TestOne', 'TestTwo']",
        "pass_to_pass": "[]",
        "selected_test_files_to_run": '["tests/unit/test_dummy.py"]',
    }


def test_parse_instance_list_field_accepts_python_repr_list() -> None:
    parsed = parse_instance_list_field(
        {"fail_to_pass": "['a', 'b', 'c']"},
        "FAIL_TO_PASS",
        alt_keys=("fail_to_pass",),
    )
    assert parsed == ["a", "b", "c"]


def test_resolve_repo_version_spec_supports_versionless_default() -> None:
    resolved_version, specs = resolve_repo_version_spec("flipt-io/flipt", None)
    assert resolved_version == "default"
    assert "test_cmd" in specs


def test_make_test_spec_supports_all_swebench_pro_repos() -> None:
    for repo in PRO_REPOS:
        spec = make_test_spec(_instance_for_repo(repo), namespace="none")
        assert spec.repo == repo
        assert spec.version == "default"
        assert spec.eval_script_list
