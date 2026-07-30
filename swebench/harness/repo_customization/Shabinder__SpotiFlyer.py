REPO = "Shabinder/SpotiFlyer"

# This project uses Gradle 7.3.3 and an old AGP whose manifest merger
# reflectively accesses java.io.File.path, which is blocked on JDK 17+.
# The base image ships JDK 17 but also has openjdk-11 installed via apt.
# Switch JAVA_HOME to JDK 11 to avoid the JPMS access error.
COMMANDS = [
    "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-$(dpkg --print-architecture)",
]
