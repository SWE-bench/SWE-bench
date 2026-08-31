"""Git and `gh` plumbing shared by `publish` and `register`.

Both commands create a repo or a branch, commit a tree, and push it, so the shell-outs
live here rather than being written twice. Nothing here is SWE-bench specific.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class GitError(RuntimeError):
    pass


def git(cwd: Path, *args: str, check: bool = True) -> str:
    """Run one git command in ``cwd`` and return its stdout."""
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def gh(cwd: Path, *args: str, check: bool = True) -> str:
    """Run one `gh` command. Raises GitError if gh is not installed."""
    if not has_gh():
        raise GitError("the GitHub CLI (`gh`) is not installed")
    proc = subprocess.run(["gh", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise GitError(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def has_gh() -> bool:
    return shutil.which("gh") is not None


def to_https(url: str) -> str:
    """A git remote (``git@host:owner/repo.git`` or https) as a browsable https URL."""
    url = url.strip().removesuffix(".git")
    if url.startswith("git@"):
        host, _, path = url[4:].partition(":")
        return f"https://{host}/{path}"
    return url


def slug(url: str) -> str:
    """``https://github.com/Owner/Repo`` -> ``Owner/Repo`` (what `gh` expects)."""
    return to_https(url).removeprefix("https://github.com/").strip("/")


def origin(repo: Path) -> Optional[str]:
    """This checkout's origin as an https URL, or None if it has no origin."""
    try:
        return to_https(git(repo, "remote", "get-url", "origin"))
    except GitError:
        return None


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD")


def gh_login() -> Optional[str]:
    """The authenticated GitHub account, or None if gh is absent or logged out."""
    if not has_gh():
        return None
    proc = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True
    )
    return proc.stdout.strip() or None if proc.returncode == 0 else None


def init_commit(repo: Path, message: str) -> None:
    """Make ``repo`` a git repo with a single commit holding everything in it.

    Supplies a fallback identity when git has none configured, which would otherwise
    fail in a fresh container.
    """
    if not (repo / ".git").is_dir():
        git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    if not git(repo, "status", "--porcelain"):
        return  # nothing staged; an unchanged tree is not an error
    ident = []
    if (
        subprocess.run(
            ["git", "config", "user.email"], cwd=str(repo), capture_output=True
        ).returncode
        != 0
    ):
        ident = [
            "-c",
            "user.name=SWE-bench",
            "-c",
            "user.email=support@swebench.com",
        ]
    git(repo, *ident, "commit", "-q", "-m", message)
