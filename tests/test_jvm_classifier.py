"""Unit tests for jvm_classifier.classify_dir (the pure-function core).
Live-clone behavior is exercised via the CLI test in a later task."""
from pathlib import Path

import pytest

from swebench.harness.jvm_classifier import ClassifyResult, classify_dir

FIXTURES = Path(__file__).parent / "fixtures" / "jvm_classifier"


def test_no_gradle_files_returns_error():
    result = classify_dir(FIXTURES / "empty_repo")
    assert result == ClassifyResult(
        bucket=None,
        signals={},
        error="no Gradle files found",
    )
