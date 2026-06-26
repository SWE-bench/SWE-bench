# --add-exports/--add-opens for KAPT + JDK 17+: KAPT accesses internal
# com.sun.tools.javac.* APIs encapsulated by the module system; without these,
# KAPT tasks fail with IllegalAccessError on jdk.compiler packages.
_KAPT_JAVAC_PACKAGES = [
    "com.sun.tools.javac.api",
    "com.sun.tools.javac.code",
    "com.sun.tools.javac.comp",
    "com.sun.tools.javac.file",
    "com.sun.tools.javac.jvm",
    "com.sun.tools.javac.main",
    "com.sun.tools.javac.model",
    "com.sun.tools.javac.parser",
    "com.sun.tools.javac.processing",
    "com.sun.tools.javac.tree",
    "com.sun.tools.javac.util",
]

# Additional JDK internal packages needed by the Kotlin compiler itself
# (not just KAPT). FileChannelUtil needs sun.nio.ch.FileChannelImpl.
_KOTLIN_JDK_PACKAGES = [
    ("java.base", "sun.nio.ch"),
]

_KAPT_MODULE_FLAGS = " ".join(
    [
        f"--add-exports=jdk.compiler/{pkg}=ALL-UNNAMED "
        f"--add-opens=jdk.compiler/{pkg}=ALL-UNNAMED"
        for pkg in _KAPT_JAVAC_PACKAGES
    ]
    + [
        f"--add-exports={mod}/{pkg}=ALL-UNNAMED --add-opens={mod}/{pkg}=ALL-UNNAMED"
        for mod, pkg in _KOTLIN_JDK_PACKAGES
    ]
)

# Writes /root/.gradle/gradle.properties with KAPT module-access flags. Runs in
# setup_repo.sh (instance build) to avoid stale cached env layers.
# Heap limits: Gradle + Kotlin daemons at -Xmx6g each cap combined use at ~14 GB,
# avoiding OOM kills seen at -Xmx12g each. workers.max=2 further limits peak.
GRADLE_PROPERTIES_SCRIPT = (
    "mkdir -p /root/.gradle && "
    'printf "%s\\n"'
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

# Smaller heaps for a few very large Kotlin/JVM builds that were OOM-killed (exit 137) in
# gradle-bench image builds. Scoped to those repos only — not a global behavior change.
GRADLE_PROPERTIES_SCRIPT_LOW_MEM = (
    "mkdir -p /root/.gradle && "
    'printf "%s\\n"'
    ' "org.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=768m -XX:+HeapDumpOnOutOfMemoryError '
    + _KAPT_MODULE_FLAGS
    + '"'
    ' "org.gradle.java.installations.auto-detect=true"'
    ' "org.gradle.java.installations.auto-download=true"'
    ' "org.gradle.caching=true"'
    ' "org.gradle.parallel=true"'
    ' "org.gradle.workers.max=1"'
    ' "org.gradle.vfs.watch=false"'
    ' "kotlin.daemon.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=384m -XX:+HeapDumpOnOutOfMemoryError '
    + _KAPT_MODULE_FLAGS
    + '"'
    " > /root/.gradle/gradle.properties"
)

# pinterest/ktlint :build-logic requires a Java 24+ toolchain (see gradle-bench logs).
# Installed via openjdk-24-jdk-headless in the Dockerfile; Ubuntu names it java-24-openjdk-<arch>.
_GRADLE_JAVA24_HOME = "/usr/lib/jvm/java-24-openjdk-amd64"

# slackhq/circuit requires JDK 23 toolchain. Installed as Eclipse Temurin 23.
_GRADLE_JAVA23_HOME = "/usr/lib/jvm/temurin-23-jdk"

# Shell commands to install Eclipse Temurin 23, for repos that require JDK 23 toolchains.
# Not available via Ubuntu apt on Jammy, so downloaded from the Adoptium API.
INSTALL_TEMURIN_23_COMMANDS = [
    'ARCH="$(dpkg --print-architecture)" && '
    'case "$ARCH" in '
    "amd64) EA=x64 ;; "
    "arm64) EA=aarch64 ;; "
    '*) echo "unsupported arch for Temurin 23: $ARCH" && exit 1 ;; '
    "esac && "
    'curl -fsSL "https://api.adoptium.net/v3/binary/latest/23/ga/linux/${EA}/jdk/hotspot/normal/eclipse?project=jdk" '
    "-o /tmp/temurin23.tar.gz && "
    "mkdir -p /usr/lib/jvm && "
    "tar -xzf /tmp/temurin23.tar.gz -C /usr/lib/jvm && "
    "JDK_DIR=\"$(find /usr/lib/jvm -maxdepth 1 -mindepth 1 -type d -name 'jdk-23*' | head -1)\" && "
    'test -n "$JDK_DIR" && mv "$JDK_DIR" /usr/lib/jvm/temurin-23-jdk && '
    "rm -f /tmp/temurin23.tar.gz",
]

KOTLIN_LOGS_COLLECTOR_SCRIPT = r"""cat > /root/kotlin_logs_collector.sh << 'KOTLIN_LOGS_EOF'
#!/usr/bin/env bash

set -euo pipefail

ROOT="."
OUTPUT_FILE="reports/junit/all-testsuites.xml"

usage() {
  cat <<'EOF'
Usage: kotlin_logs_collector.sh [options]

Options:
  -r, --root DIR       Repository root to search for JUnit XML (default .)
  -o, --output FILE    Path for merged all-testsuites.xml (default reports/junit/all-testsuites.xml)
  -h, --help           Show help

Example:
  ./kotlin_logs_collector.sh --root detekt --output artifacts_jb/junit/all-testsuites.xml
EOF
}

# ---------- Argument parsing ----------
while [ $# -gt 0 ]; do
  case "$1" in
    -r|--root)
      ROOT="$2"; shift 2 ;;
    -o|--output)
      OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$ROOT" && pwd)"

MERGED_PATH="$OUTPUT_FILE"
mkdir -p "$(dirname "$MERGED_PATH")"


mapfile -t junit_files < <(
  cd "$ROOT_DIR" && find . -type f -path '*/build/test-results/*/TEST*.xml'
)

if [ ${#junit_files[@]} -eq 0 ]; then
  echo "No JUnit XML files found"
  {
    printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>'
    printf '%s\n' '<testsuites>'
    printf '%s\n' '</testsuites>'
  } > "$MERGED_PATH"
  exit 0
fi

{
  printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>'
  printf '%s\n' '<testsuites>'

  for rel in "${junit_files[@]}"; do
    rel="${rel#./}"
    file="$ROOT_DIR/$rel"
#    printf '<!-- %s -->\n' "$rel"

    skip=1
    while IFS= read -r line; do
      if [ $skip -eq 1 ] && [[ $line =~ ^\<\?xml ]]; then
        continue
      fi
      skip=0
      printf '%s\n' "$line"
    done < "$file"
  done

  printf '%s\n' '</testsuites>'
} > "$MERGED_PATH"

echo "Merged ${#junit_files[@]} files → $MERGED_PATH"
KOTLIN_LOGS_EOF
"""

STATIC_VERIFICATION_SCRIPT = r"""cat > /root/static_verification.sh << 'STATIC_VERIFICATION_EOF'
#!/usr/bin/env bash

set -euo pipefail

./gradlew tasks

echo "STATIC VERIFICATION SUCCESS"
STATIC_VERIFICATION_EOF
"""

# Gradle init script: pre-resolves ALL resolvable configurations at image-build time via a
# `projectsEvaluated` hook + lenient artifactView. Warms every config (not just test*) because
# compile/KSP/KAPT classpaths need warming too. Lenient mode skips unresolvable Android variant
# configs without failing. Applied via `-I` to `test --dry-run` so config-time dep resolution
# by plugins (e.g. AboutLibraries) is also covered — see WARM_TEST_DEPENDENCIES_CMD.
WARM_TEST_DEPENDENCIES_SCRIPT = r"""cat > /root/gradle_resolve_all.init.gradle << 'WARM_DEPS_EOF'
gradle.projectsEvaluated {
    rootProject.allprojects { proj ->
        // Snapshot configs before resolving: resolving lazily creates new Android variant
        // configs (DependenciesMetadata, KSP/KAPT classpaths, etc.) that mutate
        // ConfigurationContainer mid-iteration, throwing ConcurrentModificationException.
        def resolvable = new ArrayList(proj.configurations.matching { it.canBeResolved })
        resolvable.each { cfg ->
            try {
                // Lenient artifactView downloads everything resolvable and ignores
                // unresolvable variants instead of throwing on the whole config.
                cfg.incoming.artifactView { it.lenient = true }.files.each { f -> f }
            } catch (Exception e) {
                proj.logger.lifecycle("resolve-all: skipped ${proj.path}:${cfg.name} - ${e.message}")
            }
        }
    }
}
WARM_DEPS_EOF
"""

# Best-effort warm-up (see WARM_TEST_DEPENDENCIES_SCRIPT): `test --dry-run` + init script in
# one pass. Downloads the Gradle wrapper dist, configures the real `test` task graph
# (triggering config-time dep resolution by plugins like AboutLibraries), and executes no
# tasks. The `-I` init script forces all resolvable artifact downloads.
# `--continue || true` ensures per-project failures and warming errors never break the build.
WARM_TEST_DEPENDENCIES_CMD = (
    "./gradlew --no-daemon --continue test --dry-run "
    "-I /root/gradle_resolve_all.init.gradle || true"
)

# ---------- Generic spec categories ----------

# All Kotlin library / multiplatform builds are pinned to x86_64.
#
# Why: Kotlin/Native ships prebuilt toolchain binaries
# (kotlin-native-prebuilt-<version>-<host>.tar.gz) that the Kotlin Gradle
# plugin downloads during :commonizeNativeDistribution and similar tasks.
# JetBrains publishes the linux-x86_64 prebuilt to Maven Central, but the
# linux-aarch64 prebuilt is NOT on Maven Central — so the build fails on
# arm64 hosts (Apple Silicon, ARM Linux runners) with:
#   "Could not find kotlin-native-prebuilt-<v>-linux-aarch64.tar.gz"
# This affects every Kotlin Multiplatform project we've tested in the
# benchmark, regardless of Kotlin version (we've reproduced it on 2.1.0).
#
# Pinning to x86_64 here means Docker uses QEMU emulation transparently
# on arm64 hosts; the Gradle plugin then downloads the linux-x86_64
# prebuilt (which Maven Central does have) and the build proceeds.
SPECS_JVM_LIBRARY_17 = {
    "1.0.0": {
        "docker_specs": {"java_version": "17", "arch": "x86_64"},
        "pre_install": [
            GRADLE_PROPERTIES_SCRIPT,
            KOTLIN_LOGS_COLLECTOR_SCRIPT,
            "chmod +x /root/kotlin_logs_collector.sh",
            STATIC_VERIFICATION_SCRIPT,
            "chmod +x /root/static_verification.sh",
            WARM_TEST_DEPENDENCIES_SCRIPT,
        ],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew build -x test",
        ],
        "test_cmd": [
            "chmod +x gradlew",
            "./gradlew test",
        ],
    }
}

SPECS_ANDROID_17 = {
    "1.0.0": {
        "docker_specs": {"java_version": "17"},
        "pre_install": [
            GRADLE_PROPERTIES_SCRIPT,
            KOTLIN_LOGS_COLLECTOR_SCRIPT,
            "chmod +x /root/kotlin_logs_collector.sh",
            STATIC_VERIFICATION_SCRIPT,
            "chmod +x /root/static_verification.sh",
            WARM_TEST_DEPENDENCIES_SCRIPT,
            "mkdir -p ~/.android && touch ~/.android/repositories.cfg",
            'rm -f debug.keystore && keytool -genkey -v -keystore debug.keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"',
        ],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew assembleDebug -Pandroid.base.ignoreExtraTranslations=true -Pandroid.lintOptions.abortOnError=false",
        ],
        "test_cmd": [
            "chmod +x gradlew",
            "./gradlew test",
        ],
    }
}

SPECS_ANDROID_21 = {
    "1.0.0": {
        "docker_specs": {"java_version": "21"},
        "pre_install": [
            GRADLE_PROPERTIES_SCRIPT,
            KOTLIN_LOGS_COLLECTOR_SCRIPT,
            "chmod +x /root/kotlin_logs_collector.sh",
            STATIC_VERIFICATION_SCRIPT,
            "chmod +x /root/static_verification.sh",
            WARM_TEST_DEPENDENCIES_SCRIPT,
            "mkdir -p ~/.android && touch ~/.android/repositories.cfg",
            'rm -f debug.keystore && keytool -genkey -v -keystore debug.keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"',
        ],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew assembleDebug -Pandroid.base.ignoreExtraTranslations=true -Pandroid.lintOptions.abortOnError=false",
        ],
        "test_cmd": [
            "chmod +x gradlew",
            "./gradlew test",
        ],
    }
}

# Android repos that bring in Kotlin/Native via Kotlin Multiplatform with
# iOS or Native targets, hitting the same missing linux-aarch64 prebuilt
# issue documented above SPECS_JVM_LIBRARY_17. SPECS_ANDROID_17 itself
# stays host-arch (most pure-Android builds work fine on arm64); use this
# variant for the few Android repos that need x86_64 + QEMU emulation.
SPECS_ANDROID_17_X86 = {
    "1.0.0": {
        **SPECS_ANDROID_17["1.0.0"],
        "docker_specs": {
            **SPECS_ANDROID_17["1.0.0"]["docker_specs"],
            "arch": "x86_64",
        },
    }
}

# kotest, sqldelight, ktor — Kotlin Multiplatform projects whose `build` triggers
# JS/Wasm browser tests that fail without a headless Chrome.  Use `assemble` in the
# install step to avoid running tests, and skip browser test tasks in test_cmd.
SPECS_JVM_LIBRARY_17_KMP_BROWSER = {
    "1.0.0": {
        **SPECS_JVM_LIBRARY_17["1.0.0"],
        "install": [
            "chmod +x gradlew",
            "echo '=== GRADLE_USER_HOME ===' && echo \"GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}\" && echo '=== gradle.properties ===' && cat ${GRADLE_USER_HOME:-/root/.gradle}/gradle.properties && echo '=== END gradle.properties ==='",
            WARM_TEST_DEPENDENCIES_CMD,
            "./gradlew assemble",
        ],
    }
}

# Smaller heaps for a few very large Kotlin/JVM builds that were OOM-killed.
SPECS_JVM_LIBRARY_17_LOW_MEM = {
    "1.0.0": {
        **SPECS_JVM_LIBRARY_17["1.0.0"],
        "pre_install": [
            GRADLE_PROPERTIES_SCRIPT_LOW_MEM,
            *SPECS_JVM_LIBRARY_17["1.0.0"]["pre_install"][1:],
        ],
    }
}
