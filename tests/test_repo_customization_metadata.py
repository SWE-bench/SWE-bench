"""Every customization module must declare its repo slug via a top-level
REPO constant so jvm.py's auto-discovery can wire it into the registry."""
import importlib
import pkgutil

import pytest

import swebench.harness.repo_customization as customization_pkg


def _customization_modules():
    for info in pkgutil.iter_modules(customization_pkg.__path__):
        if info.name in {"common"}:
            continue
        yield info.name


@pytest.mark.parametrize("module_name", list(_customization_modules()))
def test_module_declares_repo_constant(module_name):
    mod = importlib.import_module(
        f"swebench.harness.repo_customization.{module_name}"
    )
    assert hasattr(mod, "REPO"), (
        f"{module_name} is missing required top-level REPO = 'owner/name' constant"
    )
    assert "/" in mod.REPO, (
        f"{module_name} REPO must be 'owner/name' shape, got {mod.REPO!r}"
    )
