from swebench.harness.constants.kotlin_base import (
    GRADLE_PROPERTIES_SCRIPT_LOW_MEM,
    SPECS_KOTLIN_LIBRARY,
    WARM_TEST_DEPENDENCIES_CMD,
)

REPO = "arrow-kt/arrow"

# `build` triggers animalsnifferAndroidMain (missing androidMainClasses task),
# kotlinStoreYarnLock (stale lock), and OOM on large multiplatform builds.
# `assemble` skips all check-phase tasks.  Low-mem to avoid OOM.
SPECS = {
    "1.0.0": {
        **SPECS_KOTLIN_LIBRARY["1.0.0"],
        "pre_install": [
            GRADLE_PROPERTIES_SCRIPT_LOW_MEM,
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
