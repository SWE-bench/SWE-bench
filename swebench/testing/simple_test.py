#!/usr/bin/env python3
"""
Simple test to verify the swebench.testing module works correctly.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from swebench.testing import (
    run_command_with_monitoring,
    run_test,
    CommandFailedError,
)


def test_echo():
    """Test simple echo command."""
    stdout, stderr = run_command_with_monitoring(["echo", "test"], timeout=5)
    assert stdout == "test", f"Expected 'test', got '{stdout}'"
    print("✅ Echo test passed")


def test_python_calculation():
    """Test Python calculation."""
    stdout, stderr = run_command_with_monitoring(
        ["python", "-c", "print(2 + 2)"], timeout=5
    )
    assert stdout == "4", f"Expected '4', got '{stdout}'"
    print("✅ Python calculation test passed")


def test_runner_success():
    """Test the run_test function with a passing test."""

    def passing_test():
        assert 1 + 1 == 2

    result = run_test(passing_test)
    assert result["success"] is True, "Expected test to pass"
    print("✅ Test runner (success case) passed")


def test_runner_failure():
    """Test the run_test function with a failing test."""

    def failing_test():
        raise ValueError("Expected failure")

    result = run_test(failing_test)
    assert result["success"] is False, "Expected test to fail"
    assert "error" in result, "Expected error in result"
    print("✅ Test runner (failure case) passed")


def test_command_failed_error():
    """Test that failed commands raise appropriate errors."""
    try:
        run_command_with_monitoring(["python", "-c", "import sys; sys.exit(1)"], timeout=5)
        assert False, "Expected CommandFailedError"
    except CommandFailedError:
        print("✅ Command failed error test passed")


if __name__ == "__main__":
    print("Running swebench.testing module tests...\n")
    
    test_echo()
    test_python_calculation()
    test_runner_success()
    test_runner_failure()
    test_command_failed_error()
    
    print("\n✅ All tests passed!")

