"""Tests for custom repositories not in the hardcoded MAP_REPO_TO_EXT and MAP_REPO_VERSION_TO_SPECS."""

import pytest
from swebench.harness.test_spec.test_spec import make_test_spec
from swebench.harness.constants import SWEbenchInstance


class TestCustomRepos:
    """Test that repos not in the hardcoded maps can still work with custom Dockerfiles."""

    def test_custom_repo_with_custom_dockerfiles(self):
        """Test that a custom repo works when providing custom dockerfiles."""
        instance: SWEbenchInstance = {
            "repo": "custom-org/custom-repo",
            "instance_id": "custom-org__custom-repo-1",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test problem",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "1.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "test_cmd": ["pytest test.py"],
            "dockerfile_base": {
                "contents": "FROM --platform={platform} ubuntu:{ubuntu_version}\nRUN echo 'custom base'"
            },
            "dockerfile_env": {
                "contents": "FROM --platform={platform} {base_image_key}\nRUN echo 'custom env'"
            },
            "dockerfile_instance": {
                "contents": "FROM --platform={platform} {env_image_name}\nRUN echo 'custom instance'"
            },
        }

        # Should not crash
        spec = make_test_spec(instance)
        
        assert spec.repo == "custom-org/custom-repo"
        assert spec.language == "custom"  # Falls back to "custom" for unknown repos
        assert spec.custom_dockerfile_base is not None
        assert "custom base" in spec.custom_dockerfile_base
        assert spec.custom_dockerfile_env is not None
        assert "custom env" in spec.custom_dockerfile_env
        assert spec.custom_dockerfile_instance is not None
        assert "custom instance" in spec.custom_dockerfile_instance

    def test_custom_repo_partial_dockerfiles(self):
        """Test that a custom repo works with partial custom dockerfiles."""
        instance: SWEbenchInstance = {
            "repo": "another-org/another-repo",
            "instance_id": "another-org__another-repo-1",
            "base_commit": "def456",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test problem",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "def456",
            "test_cmd": ["npm test"],
            "dockerfile_base": {
                "contents": "FROM --platform={platform} ubuntu:{ubuntu_version}\nRUN echo 'base'"
            },
            "dockerfile_env": None,
            "dockerfile_instance": None,
        }

        # Should not crash - language should default to "custom"
        spec = make_test_spec(instance)
        
        assert spec.repo == "another-org/another-repo"
        assert spec.language == "custom"
        assert spec.custom_dockerfile_base is not None
        assert "base" in spec.custom_dockerfile_base

    def test_custom_repo_without_custom_dockerfiles(self):
        """Test that a custom repo without custom dockerfiles uses agnostic dockerfiles."""
        instance: SWEbenchInstance = {
            "repo": "unconfigured-org/unconfigured-repo",
            "instance_id": "unconfigured-org__unconfigured-repo-1",
            "base_commit": "ghi789",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test problem",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "3.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "ghi789",
            "test_cmd": ["make test"],
            "dockerfile_base": None,
            "dockerfile_env": None,
            "dockerfile_instance": None,
        }

        # This should work - it will use agnostic dockerfiles with language="custom"
        spec = make_test_spec(instance)
        assert spec.language == "custom"
        
        # Should use agnostic dockerfiles (Ubuntu with basic build tools)
        assert "ubuntu:" in spec.base_dockerfile
        assert "build-essential" in spec.base_dockerfile
        assert spec.env_dockerfile is not None
        assert spec.instance_dockerfile is not None

    def test_hardcoded_repo_still_works(self):
        """Test that hardcoded repos still work as before (backward compatibility)."""
        instance: SWEbenchInstance = {
            "repo": "pytest-dev/pytest",
            "instance_id": "pytest-dev__pytest-1",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test problem",
            "hints_text": "",
            "created_at": "2023-01-01",
            "version": "5.4",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
            "test_cmd": None,  # Should use the hardcoded test_cmd
            "dockerfile_base": None,
            "dockerfile_env": None,
            "dockerfile_instance": None,
        }

        spec = make_test_spec(instance)
        
        assert spec.repo == "pytest-dev/pytest"
        assert spec.language == "py"  # From MAP_REPO_TO_EXT
        # Should use default Python dockerfiles
        assert spec.custom_dockerfile_base is None
        assert spec.custom_dockerfile_env is None
        assert spec.custom_dockerfile_instance is None

