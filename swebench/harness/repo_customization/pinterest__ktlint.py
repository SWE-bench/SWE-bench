from swebench.harness.constants.jvm_base import (
    KOTLIN_LOGS_COLLECTOR_SCRIPT,
    SPECS_JVM_LIBRARY_17,
    WARM_TEST_DEPENDENCIES_CMD,
    WARM_TEST_DEPENDENCIES_SCRIPT,
    _GRADLE_JAVA24_HOME,
    _KAPT_MODULE_FLAGS,
)

REPO = "pinterest/ktlint"

_GRADLE_PROPERTIES_SCRIPT = (
    "mkdir -p /root/.gradle && "
    'printf "%s\\n"'
    f' "org.gradle.java.home={_GRADLE_JAVA24_HOME}"'
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
    " > /root/.gradle/gradle.properties"
)

_STATIC_VERIFICATION_SCRIPT = (
    r"""cat > /root/static_verification.sh << 'STATIC_VERIFICATION_KTLINT_EOF'
#!/usr/bin/env bash

set -euo pipefail

export JAVA_HOME="""
    + _GRADLE_JAVA24_HOME
    + r"""
export PATH="${JAVA_HOME}/bin:${PATH}"
./gradlew tasks

echo "STATIC VERIFICATION SUCCESS"
STATIC_VERIFICATION_KTLINT_EOF
"""
)

SPECS = {
    "1.0.0": {
        **SPECS_JVM_LIBRARY_17["1.0.0"],
        "pre_install": [
            f'export JAVA_HOME={_GRADLE_JAVA24_HOME} && export PATH="$JAVA_HOME/bin:$PATH"',
            _GRADLE_PROPERTIES_SCRIPT,
            KOTLIN_LOGS_COLLECTOR_SCRIPT,
            "chmod +x /root/kotlin_logs_collector.sh",
            _STATIC_VERIFICATION_SCRIPT,
            "chmod +x /root/static_verification.sh",
            WARM_TEST_DEPENDENCIES_SCRIPT,
        ],
        "install": [
            f'export JAVA_HOME={_GRADLE_JAVA24_HOME} && export PATH="$JAVA_HOME/bin:$PATH" && chmod +x gradlew',
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== JAVA_HOME ===' && echo \"JAVA_HOME=${JAVA_HOME:-not set}\" && java -version 2>&1 | head -1 && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            f'export JAVA_HOME={_GRADLE_JAVA24_HOME} && export PATH="$JAVA_HOME/bin:$PATH" && '
            + WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew build -x test",
        ],
        "test_cmd": [
            f'export JAVA_HOME={_GRADLE_JAVA24_HOME} && export PATH="$JAVA_HOME/bin:$PATH" && chmod +x gradlew',
            f'export JAVA_HOME={_GRADLE_JAVA24_HOME} && export PATH="$JAVA_HOME/bin:$PATH" && ./gradlew test',
        ],
    }
}
