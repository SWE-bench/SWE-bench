from swebench.harness.constants.kotlin_base import SPECS_KOTLIN_ANDROID

REPO = "wireapp/wire-android"

# The repo uses a `kalium` git submodule that must be initialized after clone.
SPECS = {
    "1.0.0": {
        **SPECS_KOTLIN_ANDROID["1.0.0"],
        "pre_install": [
            "git submodule update --init --recursive || true",
            *SPECS_KOTLIN_ANDROID["1.0.0"]["pre_install"],
        ],
    }
}
