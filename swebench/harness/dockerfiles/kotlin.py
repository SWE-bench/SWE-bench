import os
import platform as _platform


def get_host_arch() -> str:
    """Detect the host CPU architecture.

    Returns:
        "x86_64" on Intel/AMD hosts, "arm64" on Apple Silicon / ARM hosts.
    """
    machine = _platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    elif machine in ("arm64", "aarch64"):
        return "arm64"
    else:
        raise ValueError(
            f"Unsupported host architecture: {machine}. "
            "Expected x86_64/amd64 or arm64/aarch64."
        )


_DOCKERFILE_BASE_KOTLIN = """FROM --platform={platform} gradle:9.3.1-jdk{java_version}-jammy

WORKDIR /home/
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  git \
  bash \
  ca-certificates \
  unzip \
  zip \
  libncurses5 \
  libvulkan1 \
  libpulse0 \
  libgl1 \
  libxml2 \
  patch \
  openjdk-11-jdk-headless \
  openjdk-17-jdk-headless \
  openjdk-21-jdk-headless \
  chromium-browser && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROMIUM_FLAGS="--no-sandbox --headless --disable-gpu"

# On ARM64 hosts, Android SDK build tools (aapt2, aidl, etc.) are x86-64-only
# Linux ELFs.  Docker Desktop intercepts them via Rosetta/binfmt_misc emulation,
# but fails immediately because the x86-64 dynamic linker is absent from the
# container.  Adding the amd64 foreign architecture and installing libc6:amd64
# provides /lib64/ld-linux-x86-64.so.2, which lets those binaries load and run.
# On ARM64 Ubuntu the default apt sources (ports.ubuntu.com) only serve ARM
# packages, so we must explicitly add archive.ubuntu.com for amd64 packages.
RUN dpkg --add-architecture amd64 && \
  sed -i 's|^deb http://ports\\.ubuntu\\.com|deb [arch=arm64] http://ports.ubuntu.com|g' /etc/apt/sources.list && \
  printf 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu jammy main restricted universe\\ndeb [arch=amd64] http://archive.ubuntu.com/ubuntu jammy-updates main restricted universe\\ndeb [arch=amd64] http://security.ubuntu.com/ubuntu jammy-security main restricted universe\\n' \
    >> /etc/apt/sources.list && \
  apt-get update && \
  apt-get install -y --no-install-recommends \
  libc6:amd64 \
  libstdc++6:amd64 \
  zlib1g:amd64 && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

RUN update-ca-certificates
{ca_install}
# Install SDKMAN and latest Gradle version (9.3.1)
# Update these commands as new Gradle versions are released
RUN curl -s "https://get.sdkman.io" | bash
RUN bash -c "source /root/.sdkman/bin/sdkman-init.sh && \
    sdk install gradle 9.3.1 && \
    sdk default gradle 9.3.1"

# Normalize GRADLE_USER_HOME before any Gradle warmup so that all wrapper
# distributions, module caches, and transform caches live under /root/.gradle.
ENV GRADLE_USER_HOME=/root/.gradle

# The gradle base image ships /root/.gradle as a symlink into the
# VOLUME /home/gradle/.gradle. Docker discards build-time writes to volume
# paths, so anything Gradle caches under GRADLE_USER_HOME during a RUN
# (wrapper dist, module/transform caches, gradle.properties) would be lost
# from the committed image. Replace the symlink with a real directory so the
# warmup and gradle.properties persist into the base/env/instance images.
RUN rm -f /root/.gradle && mkdir -p /root/.gradle

RUN $JAVA_HOME/bin/keytool -importkeystore -noprompt -trustcacerts \
  -srckeystore /etc/ssl/certs/java/cacerts \
  -destkeystore $JAVA_HOME/lib/security/cacerts \
  -srcstorepass changeit -deststorepass changeit || true

ENV ANDROID_SDK_ROOT=/opt/android-sdk \
    ANDROID_HOME=/opt/android-sdk \
    PATH=$PATH:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools

RUN mkdir -p ${{ANDROID_SDK_ROOT}}/cmdline-tools && \
  curl -o sdk-tools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip && \
  unzip sdk-tools.zip -d ${{ANDROID_SDK_ROOT}}/cmdline-tools && \
  mv ${{ANDROID_SDK_ROOT}}/cmdline-tools/cmdline-tools ${{ANDROID_SDK_ROOT}}/cmdline-tools/latest && \
  rm sdk-tools.zip

RUN yes | sdkmanager --licenses && \
  sdkmanager "platform-tools" \
  "platforms;android-30" "platforms;android-31" "platforms;android-32" \
  "platforms;android-33" "platforms;android-34" "platforms;android-35" "platforms;android-36" \
  "build-tools;30.0.3" "build-tools;31.0.0" "build-tools;32.0.0" \
  "build-tools;33.0.0" "build-tools;33.0.1" "build-tools;34.0.0" "build-tools;35.0.0" "build-tools;36.0.0"
"""

_CA_INSTALL_BLOCK = """
# ---- Local dep-cache CA install (SWEBENCH_CA_CERT was set at build time) ----
COPY ca.crt /usr/local/share/ca-certificates/gradle-swe-bench-cache.crt

RUN update-ca-certificates && \\
  for CACERTS in $JAVA_HOME/lib/security/cacerts /usr/lib/jvm/*/lib/security/cacerts; do \\
    if [ -f "$CACERTS" ]; then \\
      keytool -importcert -noprompt -trustcacerts \\
        -alias gradle-swe-bench-cache \\
        -file /usr/local/share/ca-certificates/gradle-swe-bench-cache.crt \\
        -keystore "$CACERTS" -storepass changeit || true; \\
    fi; \\
  done
# ---- end local dep-cache CA install ----
"""


def get_ca_install_block() -> str:
    """Return Dockerfile lines that install a local CA into system + JVM trust
    stores. Env-gated: returns empty string unless SWEBENCH_CA_CERT points to
    an existing file. Callers must also arrange for that file to appear in
    the build context as ``ca.crt`` (see docker_build.build_base_images)."""
    cert = os.environ.get("SWEBENCH_CA_CERT")
    if cert and os.path.isfile(cert):
        return _CA_INSTALL_BLOCK
    return ""


def make_gradle_warmup_script(distribution_urls: list[str]) -> str:
    """
    Returns the content of a shell script that pre-warms each Gradle distribution by:
      1. Creating a minimal Gradle project in /tmp/gradle-warmup
      2. Using the system Gradle (9.3.1) to generate a wrapper pointing to the URL
      3. Running ./gradlew --no-daemon help (downloads, extracts, primes tooling API)
      4. Deleting cached ZIPs to reclaim image space
    The script is self-contained with a shebang and set -euo pipefail, suitable
    for being COPY'd and RUN'd as a file in _DOCKERFILE_BASE_KOTLIN.
    """
    lines = [
        "#!/bin/bash",
        "set -euo pipefail",
        "",
        'echo "GRADLE_USER_HOME=${GRADLE_USER_HOME:-not set}"',
        "",
        "mkdir -p /tmp/gradle-warmup",
        "cd /tmp/gradle-warmup",
        "printf 'rootProject.name = \"warmup\"\\n' > settings.gradle",
        "",
    ]
    for url in sorted(set(distribution_urls)):
        lines += [
            f"gradle --no-daemon wrapper --gradle-distribution-url '{url}'",
            "./gradlew --no-daemon help",
            "",
        ]
    lines += [
        "find /root/.gradle/wrapper/dists -name '*.zip' -delete",
        "cd /",
        "rm -rf /tmp/gradle-warmup",
    ]
    return "\n".join(lines) + "\n"


_DOCKERFILE_INSTANCE_KOTLIN = r"""FROM --platform={platform} {env_image_name}

COPY ./setup_repo.sh /root/
RUN /bin/bash /root/setup_repo.sh

WORKDIR /testbed/
"""