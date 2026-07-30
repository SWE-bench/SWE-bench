REPO = "Tapadoo/Alerter"

# This project uses an old Kotlin compiler (< 1.6) whose bundled IntelliJ
# platform code cannot run on JDK 17+.  The base image ships JDK 17 but also
# has openjdk-11 installed via apt.  Switch JAVA_HOME to JDK 11 so that both
# the Gradle daemon and Kotlin daemon run on a compatible JVM.
COMMANDS = [
    "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-$(dpkg --print-architecture)",
]
