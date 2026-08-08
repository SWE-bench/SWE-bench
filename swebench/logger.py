import logging
import sys
from pathlib import Path


def setup_logger(
    instance_id: str, log_file: Path = None, mode="w", add_stdout: bool = False
):
    """
    Set up a logger for evaluation and build processes.

    This logger is used for logging the evaluation process, build process of images and containers,
    and other operations that require file-based logging with optional console output.

    If `log_file` is provided, logs will be written to the specified file.
    If `log_file` is None, only stdout logging will be used (requires add_stdout=True).
    If `add_stdout` is True, logs will also be sent to stdout, which can be used for
    streaming ephemeral output from Modal containers or other real-time monitoring needs.

    Args:
        instance_id: Unique identifier for the instance being processed
        log_file: Path to the log file where logs will be written (optional)
        mode: File mode for opening the log file (default: "w")
        add_stdout: Whether to also output logs to stdout (default: False)

    Returns:
        logging.Logger: Configured logger instance with log_file attribute (if provided)

    Raises:
        ValueError: If both log_file is None and add_stdout is False (no output destination)
    """
    if log_file is None and not add_stdout:
        raise ValueError("Either log_file must be provided or add_stdout must be True")
    logger_name = (
        f"{instance_id}.{log_file.name}" if log_file else f"{instance_id}.stdout"
    )
    logger = logging.getLogger(logger_name)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file, mode=mode, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        setattr(logger, "log_file", log_file)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if add_stdout:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            f"%(asctime)s - {instance_id} - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def close_logger(logger):
    """
    Close all handlers associated with a logger and remove them.

    Args:
        logger: The logger instance to close
    """
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
