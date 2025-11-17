import json
import tempfile
import unittest
import yaml
from pathlib import Path

from swebench.versioning.utils import get_instances


class YAMLSupportTests(unittest.TestCase):
    """Tests for YAML format support across the codebase"""

    def test_get_instances_yaml(self):
        """Test get_instances function with YAML format"""
        instances = [
            {"instance_id": "test-1", "repo": "test/repo1"},
            {"instance_id": "test-2", "repo": "test/repo2"},
        ]
        
        # Test with .yaml extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(instances, f)
            yaml_path = f.name
        
        try:
            loaded = get_instances(yaml_path)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["instance_id"], "test-1")
            self.assertEqual(loaded[1]["instance_id"], "test-2")
        finally:
            Path(yaml_path).unlink()
        
        # Test with .yml extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(instances, f)
            yml_path = f.name
        
        try:
            loaded = get_instances(yml_path)
            self.assertEqual(len(loaded), 2)
        finally:
            Path(yml_path).unlink()

    def test_get_instances_yaml_invalid_format(self):
        """Test get_instances raises error for non-list YAML"""
        instances = {"key1": {"instance_id": "test-1"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(instances, f)
            yaml_path = f.name
        
        try:
            with self.assertRaises(ValueError) as context:
                get_instances(yaml_path)
            self.assertIn("YAML file must contain a list", str(context.exception))
        finally:
            Path(yaml_path).unlink()

    def test_yaml_json_compatibility(self):
        """Test that YAML and JSON produce the same results"""
        data = [
            {"instance_id": "test-1", "repo": "test/repo", "patch": "patch1"},
            {"instance_id": "test-2", "repo": "test/repo", "patch": "patch2"},
        ]
        
        # Create JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            json_path = f.name
        
        # Create YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(data, f)
            yaml_path = f.name
        
        try:
            json_loaded = get_instances(json_path)
            yaml_loaded = get_instances(yaml_path)
            
            # Both should produce the same data
            self.assertEqual(json_loaded, yaml_loaded)
        finally:
            Path(json_path).unlink()
            Path(yaml_path).unlink()


if __name__ == '__main__':
    unittest.main()

