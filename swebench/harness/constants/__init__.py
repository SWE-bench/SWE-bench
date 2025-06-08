from enum import Enum
from pathlib import Path
from typing import TypedDict

# Language-specific constant imports
from .c import *
from .go import *
from .java import *
from .javascript import *
from .php import *
from .python import *
from .ruby import *
from .rust import *

print("swebench/harness/constants/__init__.py: DEBUG - TOP LEVEL EXECUTION (REVISED)")

KEY_INSTANCE_ID = "instance_id"
KEY_MODEL = "model_name_or_path"
KEY_PREDICTION = "prediction"
SWE_BENCH_URL_RAW = "https://api.swebench.com/tasks/raw" # Placeholder, confirm actual URL
START_TEST_OUTPUT = "⏳ Starting Test Output..."
END_TEST_OUTPUT = "✅ Finished Test Output!"
LATEST = "latest"
RUN_EVALUATION_LOG_DIR = "logs/run_evaluation" # Directory for evaluation logs
LOG_REPORT = "report.log" # Name of the report log file
INSTANCE_IMAGE_BUILD_DIR = "instance_images" # Directory for building instance-specific Docker images
LOG_INSTANCE = "instance.log" # Name for instance-specific log files
LOG_TEST_OUTPUT = "test_output.log" # Name for test output log files

# Patching
APPLY_PATCH_FAIL = "FAIL"
APPLY_PATCH_SUCCESS = "SUCCESS"
APPLY_PATCH_PASS = "PASS" # Represents a successful patch application (original name)
RESET_FAILED = "RESET_FAILED"

# Test outcomes
OUTCOME_SUCCESS = "SUCCESS"
OUTCOME_FAILURE = "FAILURE"
OUTCOME_ERROR = "ERROR"
TESTS_ERROR = "TESTS_ERROR" # Represents an error during test execution
OUTCOME_TIMEOUT = "TIMEOUT"
TESTS_TIMEOUT = "TESTS_TIMEOUT" # Represents a timeout during test execution
FAIL_TO_FAIL = "FAIL_TO_FAIL" # Represents a test that failed before and after the patch
FAIL_TO_PASS = "FAIL_TO_PASS" # Represents a test that failed before and passed after the patch
PASS_TO_FAIL = "PASS_TO_FAIL" # Represents a test that passed before and failed after the patch
PASS_TO_PASS = "PASS_TO_PASS" # Represents a test that passed before and passed after the patch

# Docker
DOCKER_TIMEOUT = 1800 # seconds
DOCKER_PATCH = "patch.diff" # Default name for patch file in Docker
DOCKER_USER = "swe-bench"  # Default username in Docker
DOCKER_WORKDIR = "/opt/swe-bench"  # Default working directory in Docker
UTF8 = "utf-8"

# Constants - File Extensions (from original)
NON_TEST_EXTS = {
    ".c", ".cpp", ".cc", ".h", ".hpp",  # C/C++
    ".cs",  # C#
    ".d",  # D
    ".erl", ".hrl",  # Erlang
    ".go",  # Go
    ".hs", ".lhs",  # Haskell
    ".java",  # Java
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",  # JavaScript/TypeScript
    ".kt", ".kts",  # Kotlin
    ".lisp", ".lsp", ".cl",  # Lisp
    ".lua",  # Lua
    ".m", ".mm",  # Objective-C
    ".pl", ".pm", ".t",  # Perl
    ".php", ".phtml", ".php3", ".php4", ".php5", ".php7", ".phps",  # PHP
    ".py", ".pyc", ".pyd", ".pyo", ".pyw", ".pyz",  # Python
    ".rb",  # Ruby
    ".rs",  # Rust
    ".scala",  # Scala
    ".sh", ".bash",  # Shell
    ".sql",  # SQL
    ".swift",  # Swift
    ".vb",  # Visual Basic
    ".html", ".htm", ".xhtml",  # HTML
    ".css", ".scss", ".less",  # CSS/Sass/Less
    ".xml", ".xsd", ".xsl", ".xslt",  # XML
    ".json", ".yaml", ".yml", ".toml",  # Data formats
    ".md", ".rst", ".txt", ".tex",  # Markup/Text
    ".ipynb", # Jupyter Notebooks
}
print(f"swebench/harness/constants/__init__.py: DEBUG - Defined NON_TEST_EXTS (size: {len(NON_TEST_EXTS)})")


# Constants - Repositories with specific evaluation handling (from original)
FAIL_ONLY_REPOS = {
    # Example: "pvlib/pvlib-python",
} # Populate if necessary, from original file
print(f"swebench/harness/constants/__init__.py: DEBUG - Defined FAIL_ONLY_REPOS (size: {len(FAIL_ONLY_REPOS)})")


# Constants - Task Instance Class (from original)
class SWEbenchInstance(TypedDict):
    repo: str
    instance_id: str
    base_commit: str
    patch: str
    test_patch: str
    problem_statement: str
    hints_text: str
    created_at: str
    version: str
    FAIL_TO_PASS: str
    PASS_TO_PASS: str
    environment_setup_commit: str


# Constants - Test Types, Statuses (from original)
class ResolvedStatus(Enum):
    NO = "RESOLVED_NO"
    PARTIAL = "RESOLVED_PARTIAL"
    FULL = "RESOLVED_FULL"


class TestStatus(Enum):
    FAILED = "FAILED"
    PASSED = "PASSED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    XFAIL = "XFAIL"


class EvalType(Enum):
    PASS_AND_FAIL = "pass_and_fail"
    FAIL_ONLY = "fail_only"


# Original Enum definitions (PatchType was here, ApplyPatchStatus was defined by user)
class PatchType(Enum):
    PATCH_GOLD = "gold"
    PATCH_PRED = "pred"
    PATCH_PRED_TRY = "pred_try"
    PATCH_PRED_MINIMAL = "pred_minimal"
    PATCH_PRED_MINIMAL_TRY = "pred_minimal_try"
    PATCH_TEST = "test"
    PATCH_FIX = "fix" # Keep if part of user's working set
    PATCH_FAIL_TO_PASS = "fail-to-pass" # Keep if part of user's working set
    PATCH_PASS_TO_PASS = "pass-to-pass" # Keep if part of user's working set
    PATCH_PASS_TO_FAIL = "pass-to-fail" # Keep if part of user's working set

    def __str__(self):
        return self.value

class ApplyPatchStatus(Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


# --- Start: Realigning with original swe-bench constants structure ---

# Initialize aggregate dictionaries
SWE_BENCH_SPECS_BY_REPO_VERSION = {}
MAP_REPO_TO_LANG = {}
MAP_REPO_TO_INSTALL = {}
print("swebench/harness/constants/__init__.py: DEBUG - Initialized aggregate dictionaries")

LANG_CONFIGS = [
    ("C", "C"),
    ("GO", "Go"),
    ("JAVA", "Java"),
    ("JS", "JavaScript"),
    ("PHP", "PHP"),
    ("PY", "Python"),
    ("RUBY", "Ruby"),
    ("RUST", "Rust"),
]

# Merge specs and populate MAP_REPO_TO_LANG
print("swebench/harness/constants/__init__.py: DEBUG - Starting merge of MAP_REPO_VERSION_TO_SPECS_LANG and populating MAP_REPO_TO_LANG...")
for suffix, lang_name in LANG_CONFIGS:
    specs_dict_name = f"MAP_REPO_VERSION_TO_SPECS_{suffix}"
    if specs_dict_name in globals():
        specs_dict = globals()[specs_dict_name]
        SWE_BENCH_SPECS_BY_REPO_VERSION.update(specs_dict)
        for repo_key in specs_dict.keys():
            if repo_key in MAP_REPO_TO_LANG and MAP_REPO_TO_LANG[repo_key] != lang_name:
                print(f"swebench/harness/constants/__init__.py: WARNING - Repo '{repo_key}' re-mapped: '{MAP_REPO_TO_LANG[repo_key]}' -> '{lang_name}' (from {specs_dict_name})")
            MAP_REPO_TO_LANG[repo_key] = lang_name
        print(f"swebench/harness/constants/__init__.py: DEBUG - Merged {specs_dict_name} ({len(specs_dict)} repos) into SWE_BENCH_SPECS_BY_REPO_VERSION.")
    else:
        print(f"swebench/harness/constants/__init__.py: WARNING - {specs_dict_name} not found in globals.")

# Alias for backward compatibility
MAP_REPO_VERSION_TO_SPECS = SWE_BENCH_SPECS_BY_REPO_VERSION
print(f"swebench/harness/constants/__init__.py: DEBUG - MAP_REPO_VERSION_TO_SPECS final size: {len(MAP_REPO_VERSION_TO_SPECS)}")
print(f"swebench/harness/constants/__init__.py: DEBUG - MAP_REPO_TO_LANG final size: {len(MAP_REPO_TO_LANG)}")

# Merge installation commands
print("swebench/harness/constants/__init__.py: DEBUG - Starting merge of MAP_REPO_TO_INSTALL_LANG...")
for suffix, lang_name in LANG_CONFIGS:
    install_dict_name = f"MAP_REPO_TO_INSTALL_{suffix}"
    if install_dict_name in globals():
        install_dict = globals()[install_dict_name]
        for repo_key in install_dict:
            if repo_key in MAP_REPO_TO_INSTALL and MAP_REPO_TO_INSTALL[repo_key] != install_dict[repo_key]:
                 print(f"swebench/harness/constants/__init__.py: WARNING - Repo '{repo_key}' install info already in MAP_REPO_TO_INSTALL. Overwriting with data from {install_dict_name}.")
        MAP_REPO_TO_INSTALL.update(install_dict)
        print(f"swebench/harness/constants/__init__.py: DEBUG - Merged {install_dict_name} ({len(install_dict)} repos) into MAP_REPO_TO_INSTALL.")
    else:
        print(f"swebench/harness/constants/__init__.py: WARNING - {install_dict_name} not found for MAP_REPO_TO_INSTALL.")
print(f"swebench/harness/constants/__init__.py: DEBUG - MAP_REPO_TO_INSTALL final size: {len(MAP_REPO_TO_INSTALL)}")


# Other constants from the original __init__.py can be added here as needed.
# For now, focusing on getting the spec dictionaries working.

# Example: Referencing one of the imported constants from python.py to ensure it's accessible
if 'USE_X86_PY' in globals():
    print(f"swebench/harness/constants/__init__.py: DEBUG - USE_X86_PY is accessible (sample size: {len(USE_X86_PY)})" )
else:
    print("swebench/harness/constants/__init__.py: DEBUG - USE_X86_PY not accessible")


print("swebench/harness/constants/__init__.py: DEBUG - END OF REVISED INIT SCRIPT")

# All other imports and definitions are commented out for this test.
# ... (rest of the commented out code remains the same)
