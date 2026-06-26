from swebench.harness.constants.kotlin_base import (
    INSTALL_TEMURIN_23_COMMANDS,
    SPECS_KOTLIN_LIBRARY,
    WARM_TEST_DEPENDENCIES_CMD,
    _GRADLE_JAVA23_HOME,
    _GRADLE_JAVA24_HOME,
    _KAPT_MODULE_FLAGS,
)

REPO = "slackhq/circuit"

# Tell Gradle where to find JDK 23 (Temurin) and JDK 24 (openjdk-24 from apt)
# so it can auto-detect them.  Disable auto-download since both are pre-installed.
_GRADLE_PROPERTIES_SCRIPT = (
    "mkdir -p /root/.gradle && "
    'printf "%s\\n"'
    ' "org.gradle.jvmargs=-Xmx6g -XX:MaxMetaspaceSize=1g -XX:+HeapDumpOnOutOfMemoryError '
    + _KAPT_MODULE_FLAGS
    + '"'
    f' "org.gradle.java.installations.paths={_GRADLE_JAVA23_HOME},{_GRADLE_JAVA24_HOME}"'
    ' "org.gradle.java.installations.auto-detect=true"'
    ' "org.gradle.java.installations.auto-download=false"'
    ' "org.gradle.caching=true"'
    ' "org.gradle.parallel=true"'
    ' "org.gradle.workers.max=2"'
    ' "org.gradle.vfs.watch=false"'
    ' "kotlin.daemon.jvmargs=-Xmx6g -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError '
    + _KAPT_MODULE_FLAGS
    + '"'
    " > /root/.gradle/gradle.properties"
)

SPECS = {
    "1.0.0": {
        **SPECS_KOTLIN_LIBRARY["1.0.0"],
        "pre_install": [
            *INSTALL_TEMURIN_23_COMMANDS,
            _GRADLE_PROPERTIES_SCRIPT,
            *SPECS_KOTLIN_LIBRARY["1.0.0"]["pre_install"][1:],
        ],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew assemble",
        ],
    }
}
