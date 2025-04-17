from swebench.harness.log_parsers.javascript import MAP_REPO_TO_PARSER_JS
from swebench.harness.log_parsers.python import MAP_REPO_TO_PARSER_PY

MAP_REPO_TO_PARSER = {
    **MAP_REPO_TO_PARSER_JS,
    **MAP_REPO_TO_PARSER_PY,
}


__all__ = [
    "MAP_REPO_TO_PARSER",
]
