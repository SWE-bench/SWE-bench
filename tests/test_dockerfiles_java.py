"""Tests for Java Dockerfile generation, particularly ARM64 mvnd handling."""

from swebench.harness.dockerfiles import get_dockerfile_base, get_dockerfile_env
from swebench.harness.dockerfiles.java import (
    _MVND_INSTALL_AMD64,
    _MVND_INSTALL_ARM64,
)


class TestJavaMvndInstall:
    """Test that Java Dockerfiles use the correct mvnd installation for each arch."""

    def test_amd64_base_downloads_mvnd_binary(self):
        dockerfile = get_dockerfile_base(
            platform="linux/x86_64",
            arch="x86_64",
            language="java",
            java_version="17",
        )
        assert "maven-mvnd-1.0.2-linux-amd64.zip" in dockerfile
        assert "curl -fsSL" in dockerfile
        assert "ln -s" not in dockerfile  # no symlink on x86_64

    def test_arm64_base_uses_mvn_symlink(self):
        dockerfile = get_dockerfile_base(
            platform="linux/arm64/v8",
            arch="arm64",
            language="java",
            java_version="17",
        )
        assert "maven-mvnd-1.0.2-linux-amd64.zip" not in dockerfile
        assert "ln -s" in dockerfile
        assert "$(which mvn)" in dockerfile
        assert "/usr/local/mvnd/bin/mvnd" in dockerfile

    def test_arm64_base_sets_mvnd_env(self):
        dockerfile = get_dockerfile_base(
            platform="linux/arm64/v8",
            arch="arm64",
            language="java",
            java_version="17",
        )
        assert "MVND_HOME=/usr/local/mvnd" in dockerfile
        assert "PATH=$MVND_HOME/bin:$PATH" in dockerfile

    def test_amd64_base_sets_mvnd_env(self):
        dockerfile = get_dockerfile_base(
            platform="linux/x86_64",
            arch="x86_64",
            language="java",
            java_version="17",
        )
        assert "MVND_HOME=/usr/local/mvnd" in dockerfile
        assert "PATH=$MVND_HOME/bin:$PATH" in dockerfile

    def test_arm64_base_has_comment_explaining_why(self):
        dockerfile = get_dockerfile_base(
            platform="linux/arm64/v8",
            arch="arm64",
            language="java",
            java_version="17",
        )
        assert "no Linux ARM64 release" in dockerfile

    def test_base_image_uses_java_version(self):
        dockerfile = get_dockerfile_base(
            platform="linux/arm64/v8",
            arch="arm64",
            language="java",
            java_version="11",
        )
        assert "maven:3.9-eclipse-temurin-11" in dockerfile

    def test_different_arch_different_output(self):
        arm64 = get_dockerfile_base(
            platform="linux/arm64/v8",
            arch="arm64",
            language="java",
            java_version="17",
        )
        amd64 = get_dockerfile_base(
            platform="linux/x86_64",
            arch="x86_64",
            language="java",
            java_version="17",
        )
        assert arm64 != amd64
        # Both should have the same base structure
        assert "maven:3.9-eclipse-temurin-17" in arm64
        assert "maven:3.9-eclipse-temurin-17" in amd64


class TestJavaMvndEnvFallback:
    """Test that get_dockerfile_env falls back to base template for Java
    and still applies the correct mvnd install."""

    def test_arm64_env_uses_mvn_symlink(self):
        dockerfile = get_dockerfile_env(
            platform="linux/arm64/v8",
            arch="arm64",
            language="java",
            base_image_key="sweb.base.java.arm64.test:latest",
            java_version="17",
        )
        assert "ln -s" in dockerfile
        assert "$(which mvn)" in dockerfile
        assert "maven-mvnd-1.0.2-linux-amd64.zip" not in dockerfile

    def test_amd64_env_downloads_mvnd_binary(self):
        dockerfile = get_dockerfile_env(
            platform="linux/x86_64",
            arch="x86_64",
            language="java",
            base_image_key="sweb.base.java.x86_64.test:latest",
            java_version="17",
        )
        assert "maven-mvnd-1.0.2-linux-amd64.zip" in dockerfile


class TestMvndInstallConstants:
    """Test the mvnd install constant strings themselves."""

    def test_amd64_constant_has_curl_download(self):
        assert "curl -fsSL" in _MVND_INSTALL_AMD64
        assert "linux-amd64" in _MVND_INSTALL_AMD64

    def test_arm64_constant_has_symlink(self):
        assert "ln -s" in _MVND_INSTALL_ARM64
        assert "$(which mvn)" in _MVND_INSTALL_ARM64

    def test_both_set_mvnd_home(self):
        assert "MVND_HOME=/usr/local/mvnd" in _MVND_INSTALL_AMD64
        assert "MVND_HOME=/usr/local/mvnd" in _MVND_INSTALL_ARM64

    def test_both_update_path(self):
        assert "PATH=$MVND_HOME/bin:$PATH" in _MVND_INSTALL_AMD64
        assert "PATH=$MVND_HOME/bin:$PATH" in _MVND_INSTALL_ARM64


class TestNonJavaLanguagesUnaffected:
    """Verify the mvnd change doesn't affect other languages."""

    def test_c_dockerfile_unchanged(self):
        dockerfile = get_dockerfile_base(
            platform="linux/arm64/v8",
            arch="arm64",
            language="c",
        )
        assert "mvnd" not in dockerfile
