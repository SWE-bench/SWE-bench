from swebench.harness.constants.kotlin_base import (
    SPECS_KOTLIN_ANDROID,
    _KAPT_MODULE_FLAGS,
)

REPO = "ReVanced/revanced-manager"

# Needs gpr.user and gpr.key properties set (GitHub Packages auth).
# Inject dummy values so settings.gradle.kts doesn't crash on missing extra properties.
_GRADLE_PROPERTIES_SCRIPT = (
    "mkdir -p /root/.gradle && "
    'printf "%s\\n"'
    ' "org.gradle.jvmargs=-Xmx6g -XX:MaxMetaspaceSize=1g -XX:+HeapDumpOnOutOfMemoryError '
    + _KAPT_MODULE_FLAGS
    + '"'
    ' "org.gradle.java.installations.auto-detect=true"'
    ' "org.gradle.java.installations.auto-download=true"'
    ' "org.gradle.caching=true"'
    ' "org.gradle.parallel=true"'
    ' "org.gradle.workers.max=2"'
    ' "org.gradle.vfs.watch=false"'
    ' "kotlin.daemon.jvmargs=-Xmx6g -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError '
    + _KAPT_MODULE_FLAGS
    + '"'
    ' "gpr.user=nobody"'
    ' "gpr.key=none"'
    " > /root/.gradle/gradle.properties"
)

SPECS = {
    "1.0.0": {
        **SPECS_KOTLIN_ANDROID["1.0.0"],
        "pre_install": [
            _GRADLE_PROPERTIES_SCRIPT,
            *SPECS_KOTLIN_ANDROID["1.0.0"]["pre_install"][1:],
        ],
    }
}
