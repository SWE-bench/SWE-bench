# SWE-bench Testing Module

This module provides utilities for writing integration tests inside containers, with robust command execution monitoring, timeout handling, and exception detection.

## Features

- **Command Monitoring**: Execute commands with real-time stderr/stdout monitoring
- **Timeout Handling**: Automatically kill processes that exceed time limits
- **Exception Detection**: Detect and handle Python exceptions in subprocess output
- **Test Runners**: Simple wrappers for synchronous and asynchronous test functions
- **Type Hints**: Full type annotation support for better IDE integration
- **Zero Dependencies**: Uses only Python standard library - **stdlib-only by design principle**

## Design Principle

**`swebench.testing` is intentionally stdlib-only and will remain that way.** This is a core design constraint to ensure the module can be used in any environment without dependency conflicts, network access, or installation overhead. Perfect for container-based testing scenarios.

## Installation

### Default Installation (Backwards Compatible)

```bash
# Standard install (includes all SWE-bench features)
pip install swebench
```

This installs all SWE-bench dependencies. The `swebench.testing` module is included and works immediately.

### Minimal Installation (Testing Module Only)

If you **only** want to use the testing utilities in a lightweight environment (containers, CI/CD, etc.):

```bash
# Minimal install - testing module only, zero dependencies
pip install --no-deps swebench
```

This installs **only** the `swebench.testing` module with **zero external dependencies**. It uses only Python's standard library (`subprocess`, `threading`, `time`, `typing`).

**Important:** With `--no-deps`, only `swebench.testing` will work. Other modules (harness, collect, inference) require their dependencies.

### Feature-Specific Installation

```bash
# Install specific feature sets
pip install swebench[harness]    # For evaluation/harness functionality
pip install swebench[collect]    # For data collection
pip install swebench[inference]  # For model inference
```

### Usage

Once installed (either way), simply import the module:

```python
from swebench.testing import (
    run_command_with_monitoring,
    run_test,
    run_async_test,
    CommandTimeoutError,
    CommandExceptionError,
    CommandFailedError,
)
```

The testing module works identically whether you installed with full dependencies or `--no-deps`.

## Usage Examples

### Basic Command Execution

```python
from swebench.testing import run_command_with_monitoring

# Run a command with timeout
stdout, stderr = run_command_with_monitoring(
    ["python", "script.py", "arg1"],
    timeout=10
)
print(f"Output: {stdout}")
```

### Exception Handling

```python
from swebench.testing import (
    run_command_with_monitoring,
    CommandTimeoutError,
    CommandExceptionError,
    CommandFailedError,
)

try:
    stdout, stderr = run_command_with_monitoring(
        ["python", "might_fail.py"],
        timeout=5
    )
except CommandTimeoutError:
    print("Command timed out")
except CommandExceptionError:
    print("Command raised an exception")
except CommandFailedError:
    print("Command returned non-zero exit code")
```

### Test Runner Pattern

```python
import json
from swebench.testing import run_test, run_command_with_monitoring

def test_my_feature():
    """Test that my feature works correctly."""
    stdout, stderr = run_command_with_monitoring(
        ["python", "my_feature.py"],
        timeout=10
    )
    
    expected = "expected output"
    if stdout != expected:
        raise ValueError(f"Expected {expected}, got {stdout}")

# Run test and capture results
result = run_test(test_my_feature)

# Save results
with open("/eval_metrics.json", "w") as f:
    json.dump({"my_feature_test": result}, f, indent=2)
```

### Async Test Runner

```python
import asyncio
from swebench.testing import run_async_test

async def test_async_operation():
    """Test an async operation."""
    await some_async_function()
    assert result == expected

async def main():
    result = await run_async_test(test_async_operation)
    print(result)

asyncio.run(main())
```

## API Reference

### Exceptions

- **`CommandTimeoutError`**: Raised when a command exceeds the specified timeout
- **`CommandExceptionError`**: Raised when an exception is detected in stderr
- **`CommandFailedError`**: Raised when a command returns a non-zero exit code

### Functions

#### `run_command_with_monitoring(command, timeout=5)`

Execute a command with real-time monitoring.

**Parameters:**
- `command` (List[str]): Command and arguments as a list
- `timeout` (int): Maximum execution time in seconds (default: 5)

**Returns:**
- `Tuple[str, str]`: (stdout, stderr) on success

**Raises:**
- `CommandTimeoutError`: If timeout is exceeded
- `CommandExceptionError`: If exception detected in output
- `CommandFailedError`: If non-zero exit code

#### `run_test(test_fn)`

Run a synchronous test function and capture results.

**Parameters:**
- `test_fn` (Callable[[], None]): Test function to execute

**Returns:**
- `Dict[str, Any]`: Dictionary with 'success' (bool) and optional 'error' (str)

#### `run_async_test(test_fn)`

Run an asynchronous test function and capture results.

**Parameters:**
- `test_fn` (Callable[[], Awaitable[None]]): Async test function to execute

**Returns:**
- `Dict[str, Any]`: Dictionary with 'success' (bool) and optional 'error' (str)

## Integration Test Pattern

A typical integration test inside a container follows this pattern:

```python
#!/usr/bin/env python3
import json
from swebench.testing import run_test, run_command_with_monitoring

def test_feature_1():
    stdout, stderr = run_command_with_monitoring(
        ["python", "solution.py"],
        timeout=10
    )
    assert stdout == "expected output"

def test_feature_2():
    stdout, stderr = run_command_with_monitoring(
        ["./run_tests.sh"],
        timeout=30
    )
    assert "All tests passed" in stdout

if __name__ == "__main__":
    metrics = {
        "feature_1": run_test(test_feature_1),
        "feature_2": run_test(test_feature_2),
    }
    
    with open("/eval_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
```

## See Also

- See `examples.py` for more detailed usage examples
- Original implementation based on utilities from temporal tasks integration tests

