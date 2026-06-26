from swebench.harness.constants.kotlin_base import (
    GRADLE_PROPERTIES_SCRIPT,
    KOTLIN_LOGS_COLLECTOR_SCRIPT,
    SPECS_KOTLIN_LIBRARY,
    WARM_TEST_DEPENDENCIES_CMD,
    WARM_TEST_DEPENDENCIES_SCRIPT,
)

REPO = "InsertKoinIO/koin"

# Koin keeps the Gradle wrapper under projects/ (no root gradlew).
_STATIC_VERIFICATION_SCRIPT = r"""cat > /root/static_verification.sh << 'STATIC_VERIFICATION_KOIN_EOF'
#!/usr/bin/env bash

set -euo pipefail

cd projects
./gradlew tasks

echo "STATIC VERIFICATION SUCCESS"
STATIC_VERIFICATION_KOIN_EOF
"""

SPECS = {
    "1.0.0": {
        **SPECS_KOTLIN_LIBRARY["1.0.0"],
        "pre_install": [
            GRADLE_PROPERTIES_SCRIPT,
            KOTLIN_LOGS_COLLECTOR_SCRIPT,
            "chmod +x /root/kotlin_logs_collector.sh",
            _STATIC_VERIFICATION_SCRIPT,
            "chmod +x /root/static_verification.sh",
            WARM_TEST_DEPENDENCIES_SCRIPT,
        ],
        "install": [
            "cd projects",
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew assemble",
        ],
        "test_cmd": [
            "cd projects && chmod +x gradlew",
            "cd projects && ./gradlew test",
        ],
    }
}
