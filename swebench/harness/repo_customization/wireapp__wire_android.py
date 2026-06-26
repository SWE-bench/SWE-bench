from swebench.harness.constants.jvm_base import SPECS_ANDROID_17

REPO = "wireapp/wire-android"

# The repo uses a `kalium` git submodule that must be initialized after clone.
SPECS = {
    "1.0.0": {
        **SPECS_ANDROID_17["1.0.0"],
        "pre_install": [
            "git submodule update --init --recursive || true",
            *SPECS_ANDROID_17["1.0.0"]["pre_install"],
        ],
    }
}
