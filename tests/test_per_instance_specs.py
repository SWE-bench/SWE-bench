import unittest
from unittest.mock import patch

from swebench.harness.test_spec.test_spec import (
    MAP_INSTANCE_TO_SPECS,
    make_test_spec,
)
from swebench.harness.test_spec.utils import get_test_cmds


def _python_instance(instance_id="test__per-instance-1"):
    """Minimal SWE-bench instance for a known Python repo/version.

    make_test_spec() builds its script lists purely from the spec constants,
    so no Docker or network access is required to exercise this.
    """
    return {
        "instance_id": instance_id,
        "repo": "astropy/astropy",
        "version": "3.1",
        "base_commit": "0" * 40,
        "test_patch": "diff --git a/astropy/foo/test_bar.py b/astropy/foo/test_bar.py\n",
    }


class PerInstanceSpecOverrideTests(unittest.TestCase):
    """MAP_INSTANCE_TO_SPECS overrides must reach the generated scripts."""

    def test_install_override_reaches_repo_script(self):
        inst = _python_instance()
        sentinel = "echo INSTALL_OVERRIDE_SENTINEL"
        with patch.dict(
            MAP_INSTANCE_TO_SPECS, {inst["instance_id"]: {"install": sentinel}}
        ):
            spec = make_test_spec(inst)
        self.assertIn(sentinel, "\n".join(spec.repo_script_list))

    def test_test_cmd_override_reaches_eval_script(self):
        # Regression guard: test_cmd was previously read from
        # MAP_REPO_VERSION_TO_SPECS directly, so this override was ignored.
        inst = _python_instance()
        sentinel = "echo TEST_CMD_OVERRIDE_SENTINEL"
        with patch.dict(
            MAP_INSTANCE_TO_SPECS, {inst["instance_id"]: {"test_cmd": sentinel}}
        ):
            spec = make_test_spec(inst)
        self.assertIn(sentinel, "\n".join(spec.eval_script_list))

    def test_no_override_uses_repo_version_spec(self):
        inst = _python_instance()
        # Guard the test itself: the fake id must not collide with a real entry.
        self.assertNotIn(inst["instance_id"], MAP_INSTANCE_TO_SPECS)
        spec = make_test_spec(inst)
        # astropy 3.1's default test_cmd (TEST_PYTEST) must still be used.
        self.assertIn("pytest -rA", "\n".join(spec.eval_script_list))


class GetTestCmdsTests(unittest.TestCase):
    """get_test_cmds() reads test_cmd from the (merged) specs it is given."""

    def test_string_test_cmd_wrapped_in_list(self):
        self.assertEqual(get_test_cmds({"test_cmd": "pytest -x"}), ["pytest -x"])

    def test_list_test_cmd_passed_through(self):
        self.assertEqual(
            get_test_cmds({"test_cmd": ["make build", "pytest"]}),
            ["make build", "pytest"],
        )


if __name__ == "__main__":
    unittest.main()
