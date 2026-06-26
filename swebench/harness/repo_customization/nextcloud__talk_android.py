from swebench.harness.constants.jvm_base import SPECS_ANDROID_17

REPO = "nextcloud/talk-android"

# Dependency verification fails for several JitPack/GitHub artifacts whose checksums
# drifted from the committed verification-metadata.xml.
# Disable verification for both the install step and tests.
SPECS = {
    "1.0.0": {
        **SPECS_ANDROID_17["1.0.0"],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            # Warm test dependencies with verification disabled, matching the build/test steps.
            "./gradlew --no-daemon --version --dependency-verification=off && "
            "./gradlew --no-daemon --continue help "
            "-I /root/gradle_resolve_all.init.gradle --dependency-verification=off || true",
            "./gradlew assembleDebug --dependency-verification=off -Pandroid.base.ignoreExtraTranslations=true -Pandroid.lintOptions.abortOnError=false",
        ],
        "test_cmd": [
            "chmod +x gradlew",
            "./gradlew test --dependency-verification=off",
        ],
    }
}
