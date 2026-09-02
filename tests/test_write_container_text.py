"""Regression for Windows CRLF poisoning files copied into Linux eval containers."""

from pathlib import Path

from swebench.harness.utils import write_container_text


def test_write_container_text_keeps_lf_even_when_platform_uses_crlf(tmp_path: Path) -> None:
    script = "#!/bin/bash\nset -euo pipefail\ncd /testbed\n"
    patch = "diff --git a/x b/x\n+++ b/x\n+ok\n"
    eval_file = tmp_path / "eval.sh"
    patch_file = tmp_path / "patch.diff"

    write_container_text(eval_file, script)
    write_container_text(patch_file, patch)

    assert eval_file.read_bytes() == script.encode("utf-8")
    assert patch_file.read_bytes() == patch.encode("utf-8")
    assert b"\r" not in eval_file.read_bytes()
    assert b"\r" not in patch_file.read_bytes()
