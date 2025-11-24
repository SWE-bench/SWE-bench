#!/usr/bin/env python3
"""
Test runner utilities for integration tests inside containers.

This module provides functions for running commands with real-time monitoring,
timeout handling, and exception detection.

DESIGN PRINCIPLE: This module is intentionally stdlib-only and will remain that way.
It uses only standard library imports (subprocess, time, threading, typing) to ensure
zero external dependencies. This makes it perfect for lightweight container testing
where minimal installation overhead is critical.

If future features are needed that require dependencies, they should be added as
optional extensions (e.g., swebench.testing.contrib) rather than breaking this
core design constraint.
"""

import subprocess
import time
import threading
from typing import Callable, Tuple, List, Dict, Any, Awaitable


class CommandTimeoutError(Exception):
    """Raised when a command times out"""

    pass


class CommandExceptionError(Exception):
    """Raised when a command has an exception on stderr"""

    pass


class CommandFailedError(Exception):
    """Raised when a command returns a non-zero exit code"""

    pass


def run_command_with_monitoring(
    command: List[str], timeout: int = 5
) -> Tuple[str, str]:
    """
    Run a command with real-time stderr monitoring for exceptions.

    This function executes a command in a subprocess and monitors both stdout
    and stderr in real-time. It can detect exceptions, handle timeouts, and
    capture the full output.

    Args:
        command: List of command arguments (e.g., ["python", "script.py"])
        timeout: Maximum time to wait in seconds (default: 5)

    Returns:
        tuple: (stdout, stderr) on success

    Raises:
        CommandTimeoutError: If command times out
        CommandExceptionError: If exception detected on stderr
        CommandFailedError: If command returns non-zero exit code

    Example:
        >>> stdout, stderr = run_command_with_monitoring(
        ...     ["python", "test.py"], timeout=10
        ... )
        >>> print(stdout)
    """
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Monitor stderr for exceptions
    stderr_lines = []
    stdout_lines = []
    exception_detected = False
    timeout_occurred = False

    def monitor_stderr():
        nonlocal exception_detected
        for line in process.stderr:
            stderr_lines.append(line)
            # Check for common exception indicators
            if not exception_detected and any(
                keyword in line
                for keyword in ["Traceback", "Error:", "Exception:", "raise "]
            ):
                exception_detected = True
                # Don't break - continue collecting stderr for full traceback

    def monitor_stdout():
        for line in process.stdout:
            stdout_lines.append(line)

    # Start monitoring threads
    stderr_thread = threading.Thread(target=monitor_stderr)
    stdout_thread = threading.Thread(target=monitor_stdout)
    stderr_thread.daemon = True
    stdout_thread.daemon = True
    stderr_thread.start()
    stdout_thread.start()

    # Wait for process with timeout, but check for exceptions
    start_time = time.time()
    while time.time() - start_time < timeout:
        if exception_detected:
            print("Exception detected on stderr, killing process...")
            process.kill()
            process.wait()
            break

        if process.poll() is not None:
            # Process has finished
            break

        time.sleep(0.1)
    else:
        # Timeout reached
        timeout_occurred = True
        print("Timeout reached, killing process...")
        process.kill()
        process.wait()

    # Wait for threads to finish reading
    stderr_thread.join(timeout=1)
    stdout_thread.join(timeout=1)

    # Get the output
    stdout = "".join(stdout_lines).strip()
    stderr = "".join(stderr_lines).strip()
    returncode = process.returncode

    # Check for errors and raise appropriate exceptions
    if timeout_occurred:
        raise CommandTimeoutError(
            f"Command timed out after {timeout} seconds. stdout: {stdout}, stderr: {stderr}"
        )

    if exception_detected:
        raise CommandExceptionError(
            f"Exception detected in command output. stdout: {stdout}, stderr: {stderr}"
        )

    if returncode != 0:
        raise CommandFailedError(
            f"Command failed with return code {returncode}. stdout: {stdout}, stderr: {stderr}"
        )

    return stdout, stderr


def run_test(test_fn: Callable[[], None]) -> Dict[str, Any]:
    """
    Run a test function and capture the result.

    This function wraps a test function and catches any exceptions,
    returning a dictionary with the test result and any error information.

    Args:
        test_fn: A callable test function that raises an exception on failure

    Returns:
        dict: A dictionary with 'success' key (bool) and optional 'error' key (str)

    Example:
        >>> def my_test():
        ...     assert 1 + 1 == 2
        >>> result = run_test(my_test)
        >>> assert result['success'] == True
    """
    try:
        test_fn()
        print(f"✅ Test passed!")
        return {"success": True}
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {"success": False, "error": str(e)}


async def run_async_test(test_fn: Callable[[], Awaitable[None]]) -> Dict[str, Any]:
    """
    Run an async test function and capture the result.

    This function wraps an async test function and catches any exceptions,
    returning a dictionary with the test result and any error information.

    Args:
        test_fn: An async callable test function that raises an exception on failure

    Returns:
        dict: A dictionary with 'success' key (bool) and optional 'error' key (str)

    Example:
        >>> async def my_async_test():
        ...     await some_async_operation()
        ...     assert result == expected
        >>> result = await run_async_test(my_async_test)
        >>> assert result['success'] == True
    """
    try:
        await test_fn()
        print(f"✅ Test passed!")
        return {"success": True}
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {"success": False, "error": str(e)}

