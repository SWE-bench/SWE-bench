from pathlib import Path

from swebench.harness.test_spec.test_spec import EVAL_SCRIPT_STRICT_MODE_HEADER


def validate_modal_credentials():
    """
    Validate that Modal credentials exist by checking for ~/.modal.toml file.
    Raises an exception if credentials are not configured.
    """
    modal_config_path = Path.home() / ".modal.toml"
    if not modal_config_path.exists():
        raise RuntimeError(
            "~/.modal.toml not found - it looks like you haven't configured credentials for Modal.\n"
            "Run 'modal token new' in your terminal to configure credentials."
        )


def prepare_modal_eval_script(eval_script: str) -> str:
    """Apply Modal eval-script fixes: django locale + xtrace->stdout for marker ordering. See #447."""
    eval_script = eval_script.replace("locale-gen", "locale-gen en_US.UTF-8")

    target = f"{EVAL_SCRIPT_STRICT_MODE_HEADER}\n"
    replacement = f"BASH_XTRACEFD=1\n{target}"
    if replacement in eval_script:
        return eval_script
    return eval_script.replace(target, replacement, 1)
