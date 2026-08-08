from pathlib import Path


def validate_beam_credentials():
    """
    Validate that Beam credentials exist by checking for ~/.beam/config.ini file.
    Raises an exception if credentials are not configured.
    """
    beam_config_path = Path.home() / ".beam/config.ini"
    if not beam_config_path.exists():
        raise RuntimeError(
            "~/.beam/config.ini not found - it looks like you haven't configured credentials for Beam.\n"
            "Run 'beam login' in your terminal to configure credentials."
        )
