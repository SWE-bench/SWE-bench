import tempfile
import unittest
import yaml
from pathlib import Path
from swebench.harness.utils import (
    run_threadpool,
    load_swebench_dataset,
)
from swebench.harness.test_spec.python import clean_environment_yml, clean_requirements


class UtilTests(unittest.TestCase):
    def test_run_threadpool_all_failures(self):
        def failing_func(_):
            raise ValueError("Test error")

        payloads = [(1,), (2,), (3,)]
        succeeded, failed = run_threadpool(failing_func, payloads, max_workers=2)
        self.assertEqual(len(succeeded), 0)
        self.assertEqual(len(failed), 3)

    def test_environment_yml_cleaner(self):
        """
        We want to make sure that our cleaner only modifies the pip section of the environment.yml
        and that it does not modify the other dependencies sections.

        We expect "types-pkg_resources" to be replaced with "types-setuptools" in the pip section.
        """
        env_yaml = (
            "# To set up a development environment using conda run:\n"
            "#\n"
            "#   conda env create -f environment.yml\n"
            "#   conda activate mpl-dev\n"
            '#   pip install --verbose --no-build-isolation --editable ".[dev]"\n'
            "#\n"
            "---\n"
            "name: matplotlib-master\n"
            "channels:\n"
            "  - conda-forge\n"
            "dependencies:\n"
            "  # runtime dependencies\n"
            "  - cairocffi\n"
            "  - c-compiler\n"
            "  - cxx-compiler\n"
            "  - contourpy>=1.0.1\n"
            "  - cycler>=0.10.0\n"
            "  - fonttools>=4.22.0\n"
            "  - pip\n"
            "  - pip:\n"
            "    - mpl-sphinx-theme~=3.8.0\n"
            "    - sphinxcontrib-video>=0.2.1\n"
            "    - types-pkg_resources\n"
            "    - pikepdf\n"
            "  # testing\n"
            "  - types-pkg_resources\n"
            "  - black<24\n"
            "  - coverage\n"
            "  - tox\n"
        )
        expected_env_yaml = (
            "# To set up a development environment using conda run:\n"
            "#\n"
            "#   conda env create -f environment.yml\n"
            "#   conda activate mpl-dev\n"
            '#   pip install --verbose --no-build-isolation --editable ".[dev]"\n'
            "#\n"
            "---\n"
            "name: matplotlib-master\n"
            "channels:\n"
            "  - conda-forge\n"
            "dependencies:\n"
            "  # runtime dependencies\n"
            "  - cairocffi\n"
            "  - c-compiler\n"
            "  - cxx-compiler\n"
            "  - contourpy>=1.0.1\n"
            "  - cycler>=0.10.0\n"
            "  - fonttools>=4.22.0\n"
            "  - pip\n"
            "  - pip:\n"
            "    - mpl-sphinx-theme~=3.8.0\n"
            "    - sphinxcontrib-video>=0.2.1\n"
            "    - types-setuptools\n"  # should be replaced
            "    - pikepdf\n"
            "  # testing\n"
            "  - types-pkg_resources\n"  # should not be modified
            "  - black<24\n"
            "  - coverage\n"
            "  - tox\n"
        )
        cleaned = clean_environment_yml(env_yaml)
        self.assertEqual(cleaned, expected_env_yaml)

    def test_environment_yml_cleaner_version_specifiers(self):
        """Test environment.yml cleaning with various version specifiers in pip section"""
        env_yaml = (
            "name: test-env\n"
            "dependencies:\n"
            "  - pip:\n"
            "    - types-pkg_resources==1.0.0\n"
            "    - test-package-1\n"
            "    - types-pkg_resources>=2.0.0\n"
            "    - test-package-2\n"
            "    - types-pkg_resources<=3.0.0\n"
            "    - test-package-3\n"
            "    - types-pkg_resources>1.5.0\n"
            "    - test-package-4\n"
            "    - types-pkg_resources<4.0.0\n"
            "    - test-package-5\n"
            "    - types-pkg_resources~=2.1.0\n"
            "    - test-package-6\n"
            "    - types-pkg_resources!=1.9.0\n"
            "    - test-package-7\n"
            "    - types-pkg_resources==1.0.0.dev0\n"
            "    - test-package-8\n"
            "    - types-pkg_resources\n"
            "    - test-package-9\n"
            "    - other-package==1.0.0\n"
        )
        expected_env_yaml = (
            "name: test-env\n"
            "dependencies:\n"
            "  - pip:\n"
            "    - types-setuptools\n"
            "    - test-package-1\n"
            "    - types-setuptools\n"
            "    - test-package-2\n"
            "    - types-setuptools\n"
            "    - test-package-3\n"
            "    - types-setuptools\n"
            "    - test-package-4\n"
            "    - types-setuptools\n"
            "    - test-package-5\n"
            "    - types-setuptools\n"
            "    - test-package-6\n"
            "    - types-setuptools\n"
            "    - test-package-7\n"
            "    - types-setuptools\n"
            "    - test-package-8\n"
            "    - types-setuptools\n"
            "    - test-package-9\n"
            "    - other-package==1.0.0\n"
        )
        cleaned = clean_environment_yml(env_yaml)
        self.assertEqual(cleaned, expected_env_yaml)

    def test_environment_yml_cleaner_no_pip_section(self):
        """Test environment.yml cleaning when there's no pip section"""
        env_yaml = (
            "name: test-env\n"
            "dependencies:\n"
            "  - types-pkg_resources==1.0.0\n"
            "  - python=3.9\n"
        )
        cleaned = clean_environment_yml(env_yaml)
        self.assertEqual(cleaned, env_yaml)

    def test_requirements_txt_cleaner_version_specifiers(self):
        """Test requirements.txt cleaning with various version specifiers"""
        requirements = (
            "types-pkg_resources==1.0.0\n"
            "test-package-1\n"
            "types-pkg_resources>=2.0.0\n"
            "test-package-2\n"
            "types-pkg_resources<=3.0.0\n"
            "test-package-3\n"
            "types-pkg_resources>1.5.0\n"
            "test-package-4\n"
            "types-pkg_resources<4.0.0\n"
            "test-package-5\n"
            "types-pkg_resources~=2.1.0\n"
            "test-package-6\n"
            "types-pkg_resources!=1.9.0\n"
            "test-package-7\n"
            "types-pkg_resources==1.0.0.dev0\n"
            "test-package-8\n"
            "types-pkg_resources\n"
            "test-package-9\n"
            "other-package==1.0.0\n"
        )
        expected_requirements = (
            "types-setuptools\n"
            "test-package-1\n"
            "types-setuptools\n"
            "test-package-2\n"
            "types-setuptools\n"
            "test-package-3\n"
            "types-setuptools\n"
            "test-package-4\n"
            "types-setuptools\n"
            "test-package-5\n"
            "types-setuptools\n"
            "test-package-6\n"
            "types-setuptools\n"
            "test-package-7\n"
            "types-setuptools\n"
            "test-package-8\n"
            "types-setuptools\n"
            "test-package-9\n"
            "other-package==1.0.0\n"
        )
        cleaned = clean_requirements(requirements)
        self.assertEqual(cleaned, expected_requirements)

    def test_load_swebench_dataset_from_yaml(self):
        """Test loading SWE-bench dataset from YAML file"""
        dataset = [
            {
                "instance_id": "test-1",
                "repo": "test/repo",
                "patch": "test patch 1",
                "problem_statement": "test problem 1",
            },
            {
                "instance_id": "test-2",
                "repo": "test/repo",
                "patch": "test patch 2",
                "problem_statement": "test problem 2",
            },
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(dataset, f)
            yaml_path = f.name
        
        try:
            loaded = load_swebench_dataset(yaml_path)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["instance_id"], "test-1")
            self.assertEqual(loaded[1]["instance_id"], "test-2")
        finally:
            Path(yaml_path).unlink()
        
        # Test with .yml extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(dataset, f)
            yml_path = f.name
        
        try:
            loaded = load_swebench_dataset(yml_path)
            self.assertEqual(len(loaded), 2)
        finally:
            Path(yml_path).unlink()

    def test_load_swebench_dataset_from_yaml_with_filter(self):
        """Test loading SWE-bench dataset from YAML file with instance_ids filter"""
        dataset = [
            {"instance_id": "test-1", "repo": "test/repo", "patch": "patch1"},
            {"instance_id": "test-2", "repo": "test/repo", "patch": "patch2"},
            {"instance_id": "test-3", "repo": "test/repo", "patch": "patch3"},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(dataset, f)
            yaml_path = f.name
        
        try:
            # Load only specific instances
            loaded = load_swebench_dataset(yaml_path, instance_ids=["test-1", "test-3"])
            self.assertEqual(len(loaded), 2)
            instance_ids = {inst["instance_id"] for inst in loaded}
            self.assertEqual(instance_ids, {"test-1", "test-3"})
        finally:
            Path(yaml_path).unlink()

    def test_load_swebench_dataset_from_yaml_invalid_format(self):
        """Test that loading non-list YAML raises appropriate error"""
        # Create a YAML file with a dict instead of a list
        dataset = {
            "key1": {"instance_id": "test-1"},
            "key2": {"instance_id": "test-2"},
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(dataset, f)
            yaml_path = f.name
        
        try:
            with self.assertRaises(ValueError) as context:
                load_swebench_dataset(yaml_path)
            self.assertIn("YAML file must contain a list", str(context.exception))
        finally:
            Path(yaml_path).unlink()

    def test_load_swebench_dataset_from_directory(self):
        """Test loading SWE-bench dataset from a directory of task.yaml files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create two instance directories
            instance1_dir = tmpdir / "test-instance-1"
            instance1_dir.mkdir()
            task1 = {
                "repo": "test/repo1",
                "base_commit": "abc123",
                "problem_statement": "Fix bug 1",
            }
            (instance1_dir / "task.yaml").write_text(yaml.dump(task1))
            
            instance2_dir = tmpdir / "test-instance-2"
            instance2_dir.mkdir()
            task2 = {
                "repo": "test/repo2",
                "base_commit": "def456",
                "problem_statement": "Fix bug 2",
            }
            (instance2_dir / "task.yaml").write_text(yaml.dump(task2))
            
            # Load the dataset
            loaded = load_swebench_dataset(str(tmpdir))
            
            self.assertEqual(len(loaded), 2)
            
            # Should be sorted by instance_id (directory name)
            self.assertEqual(loaded[0]["instance_id"], "test-instance-1")
            self.assertEqual(loaded[1]["instance_id"], "test-instance-2")
            
            # Check fields are populated correctly
            self.assertEqual(loaded[0]["repo"], "test/repo1")
            self.assertEqual(loaded[0]["base_commit"], "abc123")
            self.assertEqual(loaded[0]["problem_statement"], "Fix bug 1")
            self.assertEqual(loaded[0]["environment_setup_commit"], "abc123")  # Should match base_commit
            
            # Check defaults for excluded fields
            self.assertEqual(loaded[0]["patch"], "")
            self.assertEqual(loaded[0]["test_patch"], "")
            self.assertEqual(loaded[0]["FAIL_TO_PASS"], "[]")
            self.assertEqual(loaded[0]["PASS_TO_PASS"], "[]")

    def test_load_swebench_dataset_from_directory_sets_task_dir(self):
        """Test that task_dir is set correctly when loading from directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            instance_dir = tmpdir / "my-task"
            instance_dir.mkdir()
            task = {
                "repo": "test/repo",
                "base_commit": "abc123",
            }
            (instance_dir / "task.yaml").write_text(yaml.dump(task))
            
            loaded = load_swebench_dataset(str(tmpdir))
            
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["task_dir"], str(instance_dir.resolve()))

    def test_load_swebench_dataset_from_directory_with_optional_fields(self):
        """Test loading directory dataset with optional fields like cp, test_cmd, dockerfile_base"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            instance_dir = tmpdir / "task-with-extras"
            instance_dir.mkdir()
            
            # Create a dockerfile in the instance directory
            (instance_dir / "Dockerfile.base").write_text("FROM ubuntu:22.04")
            
            task = {
                "repo": "test/repo",
                "base_commit": "abc123",
                "problem_statement": "Test task",
                "test_cmd": ["pytest", "test.py"],
                "cp": {"local_file.py": "remote_file.py"},
                "dockerfile_base": {"path": "Dockerfile.base"},
            }
            (instance_dir / "task.yaml").write_text(yaml.dump(task))
            
            loaded = load_swebench_dataset(str(tmpdir))
            
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["test_cmd"], ["pytest", "test.py"])
            self.assertEqual(loaded[0]["cp"], {"local_file.py": "remote_file.py"})
            self.assertEqual(loaded[0]["dockerfile_base"], {"path": "Dockerfile.base"})

    def test_load_swebench_dataset_from_directory_skips_non_directories(self):
        """Test that files in the dataset directory are ignored"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a valid instance directory
            instance_dir = tmpdir / "valid-task"
            instance_dir.mkdir()
            task = {"repo": "test/repo", "base_commit": "abc123"}
            (instance_dir / "task.yaml").write_text(yaml.dump(task))
            
            # Create a file that should be ignored
            (tmpdir / "README.md").write_text("This should be ignored")
            
            loaded = load_swebench_dataset(str(tmpdir))
            
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["instance_id"], "valid-task")

    def test_load_swebench_dataset_from_directory_skips_dirs_without_task_yaml(self):
        """Test that directories without task.yaml are ignored"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a valid instance directory
            valid_dir = tmpdir / "valid-task"
            valid_dir.mkdir()
            task = {"repo": "test/repo", "base_commit": "abc123"}
            (valid_dir / "task.yaml").write_text(yaml.dump(task))
            
            # Create a directory without task.yaml
            invalid_dir = tmpdir / "invalid-task"
            invalid_dir.mkdir()
            (invalid_dir / "other_file.txt").write_text("No task.yaml here")
            
            loaded = load_swebench_dataset(str(tmpdir))
            
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["instance_id"], "valid-task")
