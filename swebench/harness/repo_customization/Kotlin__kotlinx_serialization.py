from swebench.harness.constants.kotlin_base import (
    SPECS_JVM_LIBRARY_17,
    WARM_TEST_DEPENDENCIES_CMD,
)

REPO = "Kotlin/kotlinx.serialization"

# kover verification tasks must be excluded from both build and test.
SPECS = {
    "1.0.0": {
        **SPECS_JVM_LIBRARY_17["1.0.0"],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew build -x test -x koverVerify -x koverCachedVerify -x koverVerifyHocon",
        ],
        "test_cmd": [
            "chmod +x gradlew",
            "./gradlew test -x koverVerify -x koverCachedVerify -x koverVerifyHocon",
        ],
    }
}
