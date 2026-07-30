import importlib


def _repo_to_module_name(repo: str) -> str:
    """Convert 'owner/repo-name' to 'owner__repo_name'."""
    return repo.replace("/", "__").replace("-", "_").replace(".", "_")


def _load_customization_module(repo: str):
    """Load the customization module for a repo, or return None."""
    module_name = _repo_to_module_name(repo)
    try:
        return importlib.import_module(f".{module_name}", package=__name__)
    except ModuleNotFoundError:
        return None


def get_customization_commands(repo: str) -> list[str]:
    """Return per-repo customization commands, or empty list if none exist."""
    mod = _load_customization_module(repo)
    return getattr(mod, "COMMANDS", []) if mod else []


def get_verification_command(repo: str) -> str | None:
    """Return a per-repo verification command, or None for the default."""
    mod = _load_customization_module(repo)
    return getattr(mod, "VERIFICATION_COMMAND", None) if mod else None


def get_spec_override(repo: str) -> dict | None:
    """Return per-repo spec override, or None to use the default from constants."""
    mod = _load_customization_module(repo)
    return getattr(mod, "SPECS", None) if mod else None
