REPO = "gradle/gradle"

# gradle/gradle is a self-building Gradle project, not an Android app.
# The standard assembleDebug verification task does not exist — use
# sanityCheck, which validates the build without running the full test suite.
VERIFICATION_COMMAND = "./gradlew sanityCheck"
