from swebench.harness.constants.jvm_base import (
    SPECS_JVM_LIBRARY_17,
    WARM_TEST_DEPENDENCIES_CMD,
)

REPO = "JetBrains/Exposed"

# Exposed starts Docker containers (MariaDB, MySQL, Postgres) for integration
# tests inside the Gradle build.  Docker-in-Docker is unavailable in our images.
SPECS = {
    "1.0.0": {
        **SPECS_JVM_LIBRARY_17["1.0.0"],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew assemble",
        ],
        "test_cmd": [
            "chmod +x gradlew",
            "./gradlew test -x mariadbComposeBuild -x mariadbComposeUp -x mysqlComposeBuild -x mysqlComposeUp -x postgresComposeBuild -x postgresComposeUp -x oracleComposeBuild -x oracleComposeUp -x sqlserverComposeBuild -x sqlserverComposeUp",
        ],
    }
}
