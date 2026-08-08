from hashlib import blake2b
import re
from unidiff import PatchSet


def _get_log_objects(logger):
    if not logger:
        # if logger is None, print to stdout
        log_info = print
        log_error = print
        raise_error = True
    elif logger == "quiet":
        # if logger is "quiet", don't print anything
        log_info = lambda x: None
        log_error = lambda x: None
        raise_error = True
    else:
        # if logger is a logger object, use it
        log_info = logger.info
        log_error = logger.info
        raise_error = False
    return (log_info, log_error, raise_error)


def generate_heredoc_delimiter(content: str) -> str:
    delimiter = f"EOF_{blake2b(content.encode()).hexdigest()[:12]}"
    while delimiter in content:
        delimiter = (
            f"EOF_{blake2b(content.encode() + delimiter.encode()).hexdigest()[:12]}"
        )
    return delimiter


def get_modified_files(patch: str) -> list[str]:
    """
    Get the list of modified files in a patch
    """
    source_files = []
    for file in PatchSet(patch):
        if file.source_file != "/dev/null":
            source_files.append(file.source_file)
    source_files = [x[2:] for x in source_files if x.startswith("a/")]
    return source_files


def ansi_escape(text: str) -> str:
    """
    Remove ANSI codes from text
    """
    return re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])").sub("", text)
