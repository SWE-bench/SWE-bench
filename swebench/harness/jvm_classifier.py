"""Classify a JVM (Kotlin/Java Gradle) repo into one of the SPECS buckets.

Pure logic lives in classify_dir(); the CLI / clone wrapper sits at the bottom.
"""
from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


@dataclasses.dataclass
class ClassifyResult:
    bucket: str | None
    signals: dict
    error: str | None


_GRADLE_FILE_NAMES = {
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.properties",
}


def _gather_gradle_text(root: Path) -> str:
    """Concatenate all Gradle/build files (max depth 3 from root)."""
    chunks: list[str] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path.name not in _GRADLE_FILE_NAMES:
            continue
        depth = len(path.relative_to(root).parts)
        if depth > 3:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def classify_dir(root: Path) -> ClassifyResult:
    text = _gather_gradle_text(root)
    if not text.strip():
        return ClassifyResult(bucket=None, signals={}, error="no Gradle files found")
    return ClassifyResult(bucket=None, signals={}, error="not implemented")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m swebench.harness.jvm_classifier <owner/repo>", file=sys.stderr)
        return 2
    repo_slug = argv[1]
    tmp = Path(tempfile.mkdtemp(prefix="jvm_classifier_"))
    try:
        url = f"https://github.com/{repo_slug}.git"
        clone = subprocess.run(
            ["git", "clone", "--depth=1", url, str(tmp / "repo")],
            capture_output=True,
            text=True,
        )
        if clone.returncode != 0:
            result = ClassifyResult(
                bucket=None, signals={}, error=f"clone failed: {clone.stderr.strip()}"
            )
        else:
            result = classify_dir(tmp / "repo")
        payload = {
            "repo": repo_slug,
            "bucket": result.bucket,
            "signals": result.signals,
            "error": result.error,
        }
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
