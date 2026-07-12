"""Regression tests for pre/post-test reset in the common eval-script builder.

#539 fixed new-file-only test patches for the Python builder (test_spec/python.py)
by removing new files with `rm -f` instead of a bare `git checkout {base_commit}`.
The common builder (test_spec/utils.make_eval_script_list_common), used by the
JavaScript / Go / Java / etc. builders, still only reset via get_modified_files(),
so a new-file-only test patch produced no reset for the new files — letting a
submitted patch's file at a gold-added test path survive grading (#538). These
tests pin the ported behaviour and the ordering it must preserve.
"""

import json
import unittest
from unittest.mock import patch

from swebench.harness.test_spec import javascript as js_builder
from swebench.harness.test_spec.utils import make_eval_script_list_common
from swebench.harness.utils import get_modified_files, get_new_files

_NEW_ONLY = (
    "diff --git a/tests/test_new.py b/tests/test_new.py\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/tests/test_new.py\n"
    "@@ -0,0 +1,1 @@\n"
    "+def test_x():\n"
)
_MODIFIED_ONLY = (
    "diff --git a/tests/test_mod.py b/tests/test_mod.py\n"
    "--- a/tests/test_mod.py\n"
    "+++ b/tests/test_mod.py\n"
    "@@ -1,1 +1,2 @@\n"
    " a\n"
    "+b\n"
)
_MIXED = _MODIFIED_ONLY + _NEW_ONLY

_BASE = "BASECOMMIT"


def _common_cmds(test_patch):
    # get_test_cmds() reads the global MAP_REPO_VERSION_TO_SPECS; stub it so the
    # test exercises the reset/apply ordering without a real repo+version entry.
    with patch(
        "swebench.harness.test_spec.utils.get_test_cmds", return_value=["run-tests"]
    ):
        return make_eval_script_list_common(
            {"repo": "o/r", "version": "1"}, {}, "env", "/testbed", _BASE, test_patch
        )


def _apply_idx(cmds):
    return next(i for i, c in enumerate(cmds) if c.startswith("git apply"))


def _checkout_cmd(patch_text):
    return f"git checkout {_BASE} {' '.join(get_modified_files(patch_text))}"


def _rm_cmd(patch_text):
    return f"rm -f {' '.join(get_new_files(patch_text))}"


class CommonResetTests(unittest.TestCase):
    def test_new_only_is_removed_not_checked_out(self):
        cmds = _common_cmds(_NEW_ONLY)
        rm = _rm_cmd(_NEW_ONLY)
        pre = cmds[: _apply_idx(cmds)]
        self.assertIn(rm, pre, "new file must be rm -f'd before the official apply")
        self.assertFalse(
            any(c.startswith(f"git checkout {_BASE}") for c in cmds),
            "new-file-only patch must not emit a bare `git checkout {base}` reset",
        )
        self.assertFalse(
            any("No test files to reset" in c for c in cmds),
            "new-file-only patch must reset (rm) the new file, not no-op",
        )
        # Reset runs before apply AND again after the test-output block.
        self.assertEqual(cmds.count(rm), 2)

    def test_mixed_checkout_then_rm_before_apply(self):
        cmds = _common_cmds(_MIXED)
        co, rm, ai = _checkout_cmd(_MIXED), _rm_cmd(_MIXED), _apply_idx(cmds)
        pre = cmds[:ai]
        self.assertIn(co, pre)
        self.assertIn(rm, pre)
        self.assertLess(
            pre.index(co), pre.index(rm), "modified checkout must precede new-file rm"
        )
        self.assertLess(pre.index(rm), ai, "all resets must precede the official apply")
        self.assertEqual(cmds.count(co), 2)
        self.assertEqual(cmds.count(rm), 2)

    def test_modified_only_behaviour_unchanged(self):
        cmds = _common_cmds(_MODIFIED_ONLY)
        co = _checkout_cmd(_MODIFIED_ONLY)
        self.assertEqual(cmds.count(co), 2)
        self.assertFalse(any(c.startswith("rm -f") for c in cmds))


class JsDownloadOrderingTests(unittest.TestCase):
    def test_downloads_after_all_resets_before_apply(self):
        instance = {
            "repo": "o/r",
            "version": "1",
            "test_patch": _MIXED,
            "image_assets": json.dumps(
                {"test_patch": [{"path": "assets/img.png", "url": "http://x/img.png"}]}
            ),
        }
        with patch(
            "swebench.harness.test_spec.utils.get_test_cmds", return_value=["run-tests"]
        ):
            cmds = js_builder.make_eval_script_list_js(
                instance, {}, "env", "/testbed", _BASE, _MIXED
            )
        ai = _apply_idx(cmds)
        co_idx = cmds.index(_checkout_cmd(_MIXED))
        rm_idx = cmds.index(_rm_cmd(_MIXED))
        dl_idx = next(i for i, c in enumerate(cmds) if c.startswith("curl -o"))
        self.assertLess(co_idx, rm_idx, "resets stay ordered")
        self.assertLess(rm_idx, dl_idx, "downloads come after all pre-test resets")
        self.assertLess(dl_idx, ai, "downloads come before the official apply")


if __name__ == "__main__":
    unittest.main()
