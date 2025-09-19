from pathlib import Path

IMAGE_BUILDER_LOG_DIR = Path("logs/image_builder")

# Constants - Docker Image Building
CONTAINER_USER = "root"
CONTAINER_WORKDIR = "/testbed"
CONTAINER_ENV_NAME = "testbed"

# Constants - Installation Logging
INSTALL_FAIL = ">>>>> Init Failed"
INSTALL_PASS = ">>>>> Init Succeeded"
INSTALL_TIMEOUT = ">>>>> Init Timed Out"

REPO_BASE_COMMIT_BRANCH = {
    "sympy/sympy": {
        "cffd4e0f86fefd4802349a9f9b19ed70934ea354": "1.7",
        "70381f282f2d9d039da860e391fe51649df2779d": "sympy-1.5.1",
    },
    "pytest-dev/pytest": {
        "8aba863a634f40560e25055d179220f0eefabe9a": "4.6.x",
    },
}
