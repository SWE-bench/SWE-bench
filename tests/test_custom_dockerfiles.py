"""
Unit tests for custom Dockerfile functionality.

Tests the ability to specify custom Dockerfiles per task, with support for:
- File paths
- Direct contents
- Template variable substitution
- Backward compatibility
- Error handling
"""

import tempfile
import unittest
from pathlib import Path

from swebench.harness.constants import (
    MAP_REPO_TO_EXT,
    MAP_REPO_VERSION_TO_SPECS,
)
from swebench.harness.test_spec.test_spec import (
    load_dockerfile_content,
    make_test_spec,
)


class TestLoadDockerfileContent(unittest.TestCase):
    """Tests for the load_dockerfile_content helper function."""

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = load_dockerfile_content(None)
        self.assertIsNone(result)

    def test_direct_contents(self):
        """Test loading direct contents."""
        contents = "FROM ubuntu:22.04\nRUN apt install -y git"
        result = load_dockerfile_content({"contents": contents})
        self.assertEqual(result, contents)

    def test_path_loading(self):
        """Test loading from file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.Dockerfile', delete=False) as f:
            dockerfile_content = "FROM alpine:latest\nRUN apk add git"
            f.write(dockerfile_content)
            temp_path = f.name

        try:
            result = load_dockerfile_content({"path": temp_path})
            self.assertEqual(result, dockerfile_content)
        finally:
            Path(temp_path).unlink()

    def test_error_both_path_and_contents(self):
        """Test that specifying both path and contents raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            load_dockerfile_content({"path": "test.txt", "contents": "FROM ubuntu"})
        self.assertIn("cannot specify both", str(cm.exception).lower())

    def test_error_neither_path_nor_contents(self):
        """Test that specifying neither path nor contents raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            load_dockerfile_content({"something": "else"})
        self.assertIn("must specify either", str(cm.exception).lower())

    def test_error_not_a_dict(self):
        """Test that non-dict input raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            load_dockerfile_content("not a dict")
        self.assertIn("must be a dict", str(cm.exception).lower())

    def test_error_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError) as cm:
            load_dockerfile_content({"path": "/nonexistent/path/to/file.txt"})
        self.assertIn("not found", str(cm.exception).lower())

    def test_error_path_is_directory(self):
        """Test that path to directory raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError) as cm:
                load_dockerfile_content({"path": tmpdir})
            self.assertIn("not a file", str(cm.exception).lower())

    def test_error_contents_not_string(self):
        """Test that non-string contents raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            load_dockerfile_content({"contents": 123})
        self.assertIn("must be a string", str(cm.exception).lower())


class TestCustomDockerfilesBackwardCompatibility(unittest.TestCase):
    """Tests for backward compatibility without custom dockerfiles."""

    def test_no_custom_dockerfiles(self):
        """Test that existing configs without dockerfile fields still work."""
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-backward-compat",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test problem",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
        }

        spec = make_test_spec(instance)

        # Verify custom dockerfiles are None
        self.assertIsNone(spec.custom_dockerfile_base)
        self.assertIsNone(spec.custom_dockerfile_env)
        self.assertIsNone(spec.custom_dockerfile_instance)

        # Verify dockerfiles are generated from language-based templates
        self.assertIsNotNone(spec.base_dockerfile)
        self.assertIsNotNone(spec.env_dockerfile)
        self.assertIsNotNone(spec.instance_dockerfile)

        # Verify they contain expected content
        self.assertIn("FROM", spec.base_dockerfile)
        self.assertIn("FROM", spec.env_dockerfile)
        self.assertIn("FROM", spec.instance_dockerfile)


class TestCustomDockerfilesContents(unittest.TestCase):
    """Tests for custom dockerfiles with direct contents."""

    def test_custom_base_contents(self):
        """Test custom base dockerfile with direct contents."""
        custom_base = "FROM ubuntu:20.04\nRUN apt-get update"
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-custom-base",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": custom_base},
        }

        spec = make_test_spec(instance)

        self.assertEqual(spec.custom_dockerfile_base, custom_base)
        self.assertIn("FROM ubuntu:20.04", spec.base_dockerfile)
        # For hardcoded repos like psf/requests, should use actual language (py)
        self.assertIn("sweb.base.py.", spec.base_image_key)

    def test_custom_env_contents(self):
        """Test custom env dockerfile with direct contents."""
        custom_env = "FROM {base_image_key}\nRUN pip install pytest"
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-custom-env",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_env": {"contents": custom_env},
        }

        spec = make_test_spec(instance)

        self.assertEqual(spec.custom_dockerfile_env, custom_env)
        # Template variable should be substituted
        self.assertNotIn("{base_image_key}", spec.env_dockerfile)
        self.assertIn("FROM sweb.base.", spec.env_dockerfile)

    def test_custom_instance_contents(self):
        """Test custom instance dockerfile with direct contents."""
        custom_instance = "FROM {env_image_name}\nWORKDIR /app"
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-custom-instance",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_instance": {"contents": custom_instance},
        }

        spec = make_test_spec(instance)

        self.assertEqual(spec.custom_dockerfile_instance, custom_instance)
        # Template variable should be substituted
        self.assertNotIn("{env_image_name}", spec.instance_dockerfile)
        self.assertIn("FROM sweb.env.", spec.instance_dockerfile)

    def test_all_custom_contents(self):
        """Test all three custom dockerfiles together."""
        custom_base = "FROM ubuntu:20.04\nRUN apt install -y git"
        custom_env = "FROM {base_image_key}\nRUN pip install pytest"
        custom_instance = "FROM {env_image_name}\nWORKDIR /testbed"

        instance = {
            "repo": "psf/requests",
            "instance_id": "test-all-custom",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": custom_base},
            "dockerfile_env": {"contents": custom_env},
            "dockerfile_instance": {"contents": custom_instance},
        }

        spec = make_test_spec(instance)

        self.assertEqual(spec.custom_dockerfile_base, custom_base)
        self.assertEqual(spec.custom_dockerfile_env, custom_env)
        self.assertEqual(spec.custom_dockerfile_instance, custom_instance)

        # Verify base
        self.assertIn("FROM ubuntu:20.04", spec.base_dockerfile)

        # Verify env has template substituted
        self.assertNotIn("{base_image_key}", spec.env_dockerfile)
        self.assertIn("FROM sweb.base.", spec.env_dockerfile)

        # Verify instance has template substituted
        self.assertNotIn("{env_image_name}", spec.instance_dockerfile)
        self.assertIn("FROM sweb.env.", spec.instance_dockerfile)


class TestCustomDockerfilesPath(unittest.TestCase):
    """Tests for custom dockerfiles loaded from file paths."""

    def test_custom_dockerfiles_from_paths(self):
        """Test loading custom dockerfiles from file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create temporary Dockerfile files
            base_file = tmpdir_path / "base.Dockerfile"
            env_file = tmpdir_path / "env.Dockerfile"
            instance_file = tmpdir_path / "instance.Dockerfile"

            custom_base = "FROM ubuntu:22.04\nRUN apt-get update"
            custom_env = "FROM {base_image_key}\nCOPY setup.sh /root/"
            custom_instance = "FROM {env_image_name}\nWORKDIR /testbed"

            base_file.write_text(custom_base)
            env_file.write_text(custom_env)
            instance_file.write_text(custom_instance)

            instance = {
                "repo": "psf/requests",
                "instance_id": "test-paths",
                "base_commit": "abc123",
                "patch": "",
                "test_patch": "",
                "problem_statement": "Test",
                "hints_text": "",
                "created_at": "2023-01-01",
                "version": "2.0",
                "FAIL_TO_PASS": "[]",
                "PASS_TO_PASS": "[]",
                "environment_setup_commit": "abc123",
                "dockerfile_base": {"path": str(base_file)},
                "dockerfile_env": {"path": str(env_file)},
                "dockerfile_instance": {"path": str(instance_file)},
            }

            spec = make_test_spec(instance)

            # Verify contents were loaded from files
            self.assertEqual(spec.custom_dockerfile_base, custom_base)
            self.assertEqual(spec.custom_dockerfile_env, custom_env)
            self.assertEqual(spec.custom_dockerfile_instance, custom_instance)

            # Verify formatting works
            self.assertIn("FROM ubuntu:22.04", spec.base_dockerfile)
            self.assertNotIn("{base_image_key}", spec.env_dockerfile)
            self.assertNotIn("{env_image_name}", spec.instance_dockerfile)


class TestTemplateVariableSubstitution(unittest.TestCase):
    """Tests for template variable substitution in custom dockerfiles."""

    def test_base_dockerfile_variables(self):
        """Test that base dockerfile template variables are substituted."""
        custom_base = (
            "FROM ubuntu:22.04\n"
            "# Platform: {platform}\n"
            "# Conda arch: {conda_arch}\n"
            "# Ubuntu: {ubuntu_version}"
        )
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-base-vars",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": custom_base},
        }

        spec = make_test_spec(instance)

        # Verify template variables were substituted
        self.assertNotIn("{platform}", spec.base_dockerfile)
        self.assertNotIn("{conda_arch}", spec.base_dockerfile)
        self.assertNotIn("{ubuntu_version}", spec.base_dockerfile)
        self.assertIn("linux/", spec.base_dockerfile)

    def test_env_dockerfile_variables(self):
        """Test that env dockerfile template variables are substituted."""
        custom_env = (
            "FROM {base_image_key}\n"
            "# Platform: {platform}\n"
            "# Arch: {arch}\n"
            "# Python: {python_version}"
        )
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-env-vars",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_env": {"contents": custom_env},
        }

        spec = make_test_spec(instance)

        # Verify template variables were substituted
        self.assertNotIn("{base_image_key}", spec.env_dockerfile)
        self.assertNotIn("{platform}", spec.env_dockerfile)
        self.assertNotIn("{arch}", spec.env_dockerfile)
        self.assertNotIn("{python_version}", spec.env_dockerfile)
        self.assertIn("FROM sweb.base.", spec.env_dockerfile)

    def test_instance_dockerfile_variables(self):
        """Test that instance dockerfile template variables are substituted."""
        custom_instance = "FROM {env_image_name}\n# Platform: {platform}"
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-instance-vars",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_instance": {"contents": custom_instance},
        }

        spec = make_test_spec(instance)

        # Verify template variables were substituted
        self.assertNotIn("{env_image_name}", spec.instance_dockerfile)
        self.assertNotIn("{platform}", spec.instance_dockerfile)
        self.assertIn("FROM sweb.env.", spec.instance_dockerfile)


class TestImageKeyGeneration(unittest.TestCase):
    """Tests for unique image key generation with custom dockerfiles."""

    def test_different_custom_dockerfiles_different_keys(self):
        """Test that different custom dockerfiles produce different image keys."""
        base1 = "FROM ubuntu:20.04"
        base2 = "FROM ubuntu:22.04"

        instance1 = {
            "repo": "psf/requests",
            "instance_id": "test-key-1",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": base1},
        }

        instance2 = {
            **instance1,
            "instance_id": "test-key-2",
            "dockerfile_base": {"contents": base2},
        }

        spec1 = make_test_spec(instance1)
        spec2 = make_test_spec(instance2)

        # Verify different dockerfiles produce different keys
        self.assertNotEqual(spec1.base_image_key, spec2.base_image_key)
        # For hardcoded repo (psf/requests), both should use "py" in their keys
        self.assertIn("sweb.base.py.", spec1.base_image_key)
        self.assertIn("sweb.base.py.", spec2.base_image_key)

    def test_same_custom_dockerfiles_same_keys(self):
        """Test that identical custom dockerfiles produce the same image keys."""
        base = "FROM ubuntu:20.04\nRUN apt install -y git"

        instance1 = {
            "repo": "psf/requests",
            "instance_id": "test-key-same-1",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": base},
        }

        instance2 = {
            **instance1,
            "instance_id": "test-key-same-2",
        }

        spec1 = make_test_spec(instance1)
        spec2 = make_test_spec(instance2)

        # Verify identical dockerfiles produce the same key
        self.assertEqual(spec1.base_image_key, spec2.base_image_key)

    def test_custom_vs_default_different_keys(self):
        """Test that custom dockerfile differs from default."""
        instance_default = {
            "repo": "psf/requests",
            "instance_id": "test-default",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
        }

        instance_custom = {
            **instance_default,
            "instance_id": "test-custom",
            "dockerfile_base": {"contents": "FROM ubuntu:20.04"},
        }

        spec_default = make_test_spec(instance_default)
        spec_custom = make_test_spec(instance_custom)

        # Verify custom dockerfile differs from default
        self.assertNotEqual(spec_default.base_image_key, spec_custom.base_image_key)
        # Both use language (py) since psf/requests is hardcoded
        self.assertIn("sweb.base.py.", spec_default.base_image_key)
        self.assertIn("sweb.base.py.", spec_custom.base_image_key)

    def test_custom_uses_custom_identifier(self):
        """Test that non-hardcoded repos use 'custom' identifier in image keys."""
        # Use a repo that's NOT in MAP_REPO_TO_EXT
        instance = {
            "repo": "unknown-org/unknown-repo",
            "instance_id": "test-custom-identifier",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "1.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "test_cmd": ["pytest"],
            "dockerfile_base": {"contents": "FROM ubuntu:22.04"},
            "dockerfile_env": {"contents": "FROM {base_image_key}\nRUN echo test"},
        }

        spec = make_test_spec(instance)

        # Both base and env should use "custom" since repo is not hardcoded
        self.assertIn("sweb.base.custom.", spec.base_image_key)
        self.assertIn("sweb.env.custom.", spec.env_image_key)


class TestHashingFormattedDockerfiles(unittest.TestCase):
    """Tests that image keys hash the formatted Dockerfile content, not templates."""

    def test_hash_includes_formatted_content(self):
        """Test that changing docker_specs changes the hash (because it changes the formatted Dockerfile)."""
        template = "FROM ubuntu:{ubuntu_version}\nRUN echo test"
        
        instance1 = {
            "repo": "test-org/test-repo",
            "instance_id": "test-hash-1",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "1.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "test_cmd": ["pytest"],
            "dockerfile_base": {"contents": template},
        }

        instance2 = {
            **instance1,
            "instance_id": "test-hash-2",
        }

        # Both instances have the same template, same default docker_specs
        spec1 = make_test_spec(instance1)
        spec2 = make_test_spec(instance2)
        
        # Should have the same hash since formatted content is identical
        self.assertEqual(spec1.base_image_key, spec2.base_image_key)
        
        # Now create an instance with different ubuntu_version
        spec3 = make_test_spec(instance1, cli_docker_specs={"ubuntu_version": "20.04"})
        spec4 = make_test_spec(instance2, cli_docker_specs={"ubuntu_version": "22.04"})
        
        # Should have different hashes since formatted content differs
        self.assertNotEqual(spec3.base_image_key, spec4.base_image_key)
        
        # Verify the formatted content actually differs
        self.assertIn("ubuntu:20.04", spec3.base_dockerfile)
        self.assertIn("ubuntu:22.04", spec4.base_dockerfile)


class TestPartialOverride(unittest.TestCase):
    """Tests for partial override of dockerfiles."""

    def test_only_base_custom(self):
        """Test overriding only base dockerfile."""
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-partial-base",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": "FROM ubuntu:20.04"},
        }

        spec = make_test_spec(instance)

        # Base should be custom
        self.assertIsNotNone(spec.custom_dockerfile_base)
        self.assertIn("FROM ubuntu:20.04", spec.base_dockerfile)

        # Env and instance should use defaults
        self.assertIsNone(spec.custom_dockerfile_env)
        self.assertIsNone(spec.custom_dockerfile_instance)

    def test_only_env_custom(self):
        """Test overriding only env dockerfile."""
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-partial-env",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_env": {"contents": "FROM {base_image_key}\nRUN echo test"},
        }

        spec = make_test_spec(instance)

        # Base and instance should use defaults
        self.assertIsNone(spec.custom_dockerfile_base)
        self.assertIsNone(spec.custom_dockerfile_instance)

        # Env should be custom
        self.assertIsNotNone(spec.custom_dockerfile_env)
        self.assertIn("RUN echo test", spec.env_dockerfile)


class TestNonPyJsLanguages(unittest.TestCase):
    """Tests for languages without separate env Dockerfiles (Go, C, Java, etc.)"""

    def test_custom_base_go_reuses_base_for_env(self):
        """Test that Go with custom base doesn't rebuild for env layer"""
        custom_base = "FROM alpine:3.18\nRUN apk add go git"
        
        instance = {
            "repo": "golang/go",  # Go repository
            "instance_id": "test-go-1",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "1.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": custom_base},
        }
        
        # Register the repo
        MAP_REPO_TO_EXT["golang/go"] = "go"
        MAP_REPO_VERSION_TO_SPECS["golang/go"] = {
            "1.0": {
                "install": "echo 'test'",
                "packages": "",
                "pip_packages": [],
                "test_cmd": ["echo 'test'"],
            }
        }
        
        spec = make_test_spec(instance)
        
        # Verify base uses custom dockerfile
        self.assertIn("FROM alpine:3.18", spec.base_dockerfile)
        
        # Verify env dockerfile is minimal and just references base
        self.assertIn(f"FROM --platform={spec.platform} {spec.base_image_key}", spec.env_dockerfile)
        self.assertIn("WORKDIR /testbed/", spec.env_dockerfile)
        # Should NOT rebuild everything from Ubuntu
        self.assertNotIn("ubuntu", spec.env_dockerfile.lower())
        
    def test_custom_base_python_still_uses_env(self):
        """Test that Python with custom base still uses proper env Dockerfile"""
        custom_base = "FROM alpine:3.18\nRUN apk add python3 git"
        
        instance = {
            "repo": "psf/requests",
            "instance_id": "test-py-custom-base",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "dockerfile_base": {"contents": custom_base},
        }
        
        spec = make_test_spec(instance)
        
        # Verify base uses custom dockerfile
        self.assertIn("FROM alpine:3.18", spec.base_dockerfile)
        
        # Verify env dockerfile uses the actual Python env Dockerfile
        # (not the minimal one) because Python HAS a separate env Dockerfile
        self.assertIn(f"FROM --platform={spec.platform} {spec.base_image_key}", spec.env_dockerfile)
        self.assertIn("setup_env.sh", spec.env_dockerfile)
        self.assertIn("conda activate testbed", spec.env_dockerfile)


if __name__ == "__main__":
    unittest.main()

