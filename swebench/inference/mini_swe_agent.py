"""Build the command that runs mini-SWE-agent over a SWE-bench dataset.

mini-SWE-agent is a separate tool with its own CLI (``mini-extra swebench``); this only
assembles the invocation so a run can be started with SWE-bench's own dataset aliases
and without hand-typing the path to mini's bundled config inside site-packages.

Kept as a pure argv builder so it is testable without spawning anything.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

RUNNER_MODULE = "minisweagent.run.benchmarks.swebench"

# mini resolves an unknown --subset as a dataset path, so passing a full HuggingFace id
# works and we never have to track mini's own alias table (which points at the older
# princeton-nlp/* copies).
INSTALL_HINT = (
    "mini-SWE-agent is not installed in this interpreter. Install it with\n"
    "    pip install mini-swe-agent\n"
    "or run inference from an environment that has it."
)


class InferenceError(RuntimeError):
    pass


def _probe(python: str, expr: str) -> Optional[str]:
    """Evaluate a snippet in another interpreter, returning its last stdout line.

    Only the last line: importing mini prints a version banner to stdout, so anything
    the snippet prints comes after that noise.
    """
    try:
        out = subprocess.run(
            [python, "-c", expr], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    lines = [line for line in out.stdout.splitlines() if line.strip()]
    return lines[-1].strip() if lines else ""


def is_available(python: Optional[str] = None) -> bool:
    """Whether mini-SWE-agent is importable -- here, or in ``python`` if given."""
    if python:
        return _probe(python, "import minisweagent") is not None
    import importlib.util

    return importlib.util.find_spec("minisweagent") is not None


def default_config(python: Optional[str] = None) -> Path:
    """Path to mini's bundled SWE-bench config, in whichever install will run it.

    It lives inside mini's package directory, so it has to be read from the same
    interpreter that imports mini -- not from this one.
    """
    if python:
        found = _probe(
            python,
            "from minisweagent.config import builtin_config_dir as d; print(d)",
        )
        if not found:
            raise InferenceError(f"{python} cannot import mini-SWE-agent")
        path = Path(found) / "benchmarks" / "swebench.yaml"
    else:
        from minisweagent.config import builtin_config_dir

        path = Path(builtin_config_dir) / "benchmarks" / "swebench.yaml"
    if not path.is_file():
        raise InferenceError(f"mini-SWE-agent has no bundled config at {path}")
    return path


def build_command(
    dataset: str,
    *,
    output: Path,
    split: str = "test",
    workers: int = 1,
    model: Optional[str] = None,
    configs: tuple[str, ...] = (),
    extra: tuple[str, ...] = (),
    python: Optional[str] = None,
) -> list[str]:
    """Assemble the argv for one mini-SWE-agent batch run.

    ``configs`` are passed through in order after mini's bundled default, which is
    included explicitly because mini drops its default as soon as any -c is given.
    """
    cmd = [python or sys.executable, "-m", RUNNER_MODULE]
    cmd += ["--subset", dataset, "--split", split]
    cmd += ["-w", str(workers), "-o", str(output)]
    cmd += ["-c", str(default_config(python))]
    for config in configs:
        cmd += ["-c", config]
    if model:
        cmd += ["-m", model]
    return cmd + list(extra)


def run(cmd: list[str], cwd: Optional[Path] = None) -> int:
    """Run an assembled command, streaming its output. Returns the exit code."""
    if not shutil.which(cmd[0]) and not Path(cmd[0]).exists():
        raise InferenceError(f"interpreter not found: {cmd[0]}")
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None)
