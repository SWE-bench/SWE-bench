"""
Unit tests for CLI docker specs override functionality.
"""

import unittest
from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS
from swebench.harness.test_spec.test_spec import make_test_spec


class TestCLIDockerSpecs(unittest.TestCase):
    """Test CLI docker specs override functionality"""
    
    def setUp(self):
        """Set up test instance"""
        self.sample_instance = {
            "repo": "psf/requests",
            "instance_id": "test-cli-specs-1",
            "base_commit": "abc123",
            "patch": "",
            "test_patch": "",
            "problem_statement": "Test problem",
            "hints_text": "",
            "created_at": "2024-01-01",
            "version": "2.0",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "environment_setup_commit": "abc123",
        }
    
    def test_cli_specs_override(self):
        """Test that CLI docker specs override config specs"""
        # Set some config specs
        MAP_REPO_VERSION_TO_SPECS[self.sample_instance["repo"]][self.sample_instance["version"]]["docker_specs"] = {
            "ubuntu_version": "20.04",
            "python_version": "3.9"
        }
        
        # Create spec without CLI override
        spec_no_cli = make_test_spec(self.sample_instance)
        self.assertEqual(spec_no_cli.docker_specs["ubuntu_version"], "20.04")
        self.assertEqual(spec_no_cli.docker_specs["python_version"], "3.9")
        
        # Create spec with CLI override
        cli_specs = {"ubuntu_version": "22.04", "python_version": "3.11"}
        spec_with_cli = make_test_spec(self.sample_instance, cli_docker_specs=cli_specs)
        self.assertEqual(spec_with_cli.docker_specs["ubuntu_version"], "22.04")
        self.assertEqual(spec_with_cli.docker_specs["python_version"], "3.11")
        
    def test_cli_specs_add_new(self):
        """Test that CLI docker specs can add new variables not in config"""
        # Set minimal config specs
        MAP_REPO_VERSION_TO_SPECS[self.sample_instance["repo"]][self.sample_instance["version"]]["docker_specs"] = {
            "ubuntu_version": "20.04"
        }
        
        # Create spec with CLI adding new specs
        cli_specs = {"python_version": "3.11", "nodejs_version": "18.0"}
        spec = make_test_spec(self.sample_instance, cli_docker_specs=cli_specs)
        
        # Config spec should still be there
        self.assertEqual(spec.docker_specs["ubuntu_version"], "20.04")
        # CLI specs should be added
        self.assertEqual(spec.docker_specs["python_version"], "3.11")
        self.assertEqual(spec.docker_specs["nodejs_version"], "18.0")
        
    def test_cli_specs_empty(self):
        """Test with empty CLI specs"""
        MAP_REPO_VERSION_TO_SPECS[self.sample_instance["repo"]][self.sample_instance["version"]]["docker_specs"] = {
            "ubuntu_version": "20.04"
        }
        
        spec = make_test_spec(self.sample_instance, cli_docker_specs={})
        self.assertEqual(spec.docker_specs["ubuntu_version"], "20.04")
        
    def test_cli_specs_none(self):
        """Test with None CLI specs"""
        MAP_REPO_VERSION_TO_SPECS[self.sample_instance["repo"]][self.sample_instance["version"]]["docker_specs"] = {
            "ubuntu_version": "20.04"
        }
        
        spec = make_test_spec(self.sample_instance, cli_docker_specs=None)
        self.assertEqual(spec.docker_specs["ubuntu_version"], "20.04")
        
    def test_cli_specs_image_key_changes(self):
        """Test that different CLI specs result in different image keys"""
        # Create specs with different CLI overrides
        spec1 = make_test_spec(self.sample_instance, cli_docker_specs={"ubuntu_version": "20.04"})
        spec2 = make_test_spec(self.sample_instance, cli_docker_specs={"ubuntu_version": "22.04"})
        
        # Image keys should be different because docker_specs are different
        self.assertNotEqual(spec1.base_image_key, spec2.base_image_key)
        
    def test_cli_specs_with_custom_dockerfile(self):
        """Test CLI specs work with custom Dockerfiles"""
        instance = {
            **self.sample_instance,
            "dockerfile_base": {
                "contents": "FROM ubuntu:{ubuntu_version}\nRUN apt-get update"
            }
        }
        
        cli_specs = {"ubuntu_version": "22.04"}
        spec = make_test_spec(instance, cli_docker_specs=cli_specs)
        
        # Check that the template variable is substituted
        self.assertIn("FROM ubuntu:22.04", spec.base_dockerfile)
        self.assertEqual(spec.docker_specs["ubuntu_version"], "22.04")


if __name__ == "__main__":
    unittest.main()

