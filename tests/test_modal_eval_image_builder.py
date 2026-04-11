import importlib.util
import shutil
import sys
import types
import unittest

from dataclasses import dataclass, field
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "swebench"
    / "harness"
    / "modal_eval"
    / "run_evaluation_modal.py"
)


class FakeImage:
    last_from_registry = None
    last_dockerfile_commands = None
    last_add_local_file = None

    @classmethod
    def reset(cls):
        cls.last_from_registry = None
        cls.last_dockerfile_commands = None
        cls.last_add_local_file = None

    @staticmethod
    def debian_slim():
        return FakeImage()

    @staticmethod
    def from_registry(tag, **kwargs):
        FakeImage.last_from_registry = (tag, kwargs)
        return FakeImage()

    def pip_install(self, *_args):
        return self

    def dockerfile_commands(self, *commands, **kwargs):
        FakeImage.last_dockerfile_commands = (commands, kwargs)
        return self

    def add_local_file(self, local_path, remote_path, **kwargs):
        FakeImage.last_add_local_file = (Path(local_path), remote_path, kwargs)
        return self


class FakeApp:
    def __init__(self, _name):
        pass

    def function(self, **_kwargs):
        def decorator(fn):
            return fn

        return decorator


class FakeLogger:
    log_file = Path("run_instance.log")

    def info(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


@dataclass
class FakeTestSpec:
    instance_id: str
    language: str
    base_dockerfile: str
    env_dockerfile: str
    instance_dockerfile: str
    setup_env_script: str = "#!/bin/bash\n"
    install_repo_script: str = "#!/bin/bash\n"
    docker_specs: dict = field(default_factory=dict)


def _make_package(name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__path__ = []
    return module


def load_modal_module():
    fake_modal = types.ModuleType("modal")
    fake_modal.App = FakeApp
    fake_modal.Image = FakeImage
    fake_modal.Sandbox = types.SimpleNamespace(create=lambda **_kwargs: None)
    fake_modal.exception = types.SimpleNamespace(
        SandboxTimeoutError=type("SandboxTimeoutError", (Exception,), {})
    )
    fake_modal.enable_output = lambda: types.SimpleNamespace(
        __enter__=lambda self: None,
        __exit__=lambda self, exc_type, exc_val, exc_tb: False,
    )

    fake_modal_container_process = types.ModuleType("modal.container_process")
    fake_modal_container_process.ContainerProcess = object
    fake_modal_io_streams = types.ModuleType("modal.io_streams")
    fake_modal_io_streams.StreamReader = object

    fake_tenacity = types.ModuleType("tenacity")
    fake_tenacity.retry = lambda *args, **kwargs: (lambda fn: fn)
    fake_tenacity.stop_after_attempt = lambda attempts: attempts
    fake_tenacity.wait_exponential = lambda **kwargs: kwargs

    fake_docker_build = types.ModuleType("swebench.harness.docker_build")
    fake_docker_build.setup_logger = lambda *args, **kwargs: FakeLogger()

    fake_reporting = types.ModuleType("swebench.harness.reporting")
    fake_reporting.make_run_report = lambda *args, **kwargs: None

    fake_utils = types.ModuleType("swebench.harness.utils")

    class EvaluationError(Exception):
        pass

    fake_utils.EvaluationError = EvaluationError

    fake_constants = types.ModuleType("swebench.harness.constants")
    fake_constants.APPLY_PATCH_FAIL = "patch fail"
    fake_constants.APPLY_PATCH_PASS = "patch pass"
    fake_constants.RUN_EVALUATION_LOG_DIR = Path("logs/run_evaluation")

    fake_grading = types.ModuleType("swebench.harness.grading")
    fake_grading.get_eval_report = lambda *args, **kwargs: {}

    fake_test_spec = types.ModuleType("swebench.harness.test_spec.test_spec")
    fake_test_spec.make_test_spec = lambda instance: instance
    fake_test_spec.TestSpec = FakeTestSpec

    saved_modules = sys.modules.copy()
    try:
        sys.modules["modal"] = fake_modal
        sys.modules["modal.container_process"] = fake_modal_container_process
        sys.modules["modal.io_streams"] = fake_modal_io_streams
        sys.modules["tenacity"] = fake_tenacity
        sys.modules["swebench"] = _make_package("swebench")
        sys.modules["swebench.harness"] = _make_package("swebench.harness")
        sys.modules["swebench.harness.test_spec"] = _make_package(
            "swebench.harness.test_spec"
        )
        sys.modules["swebench.harness.docker_build"] = fake_docker_build
        sys.modules["swebench.harness.reporting"] = fake_reporting
        sys.modules["swebench.harness.utils"] = fake_utils
        sys.modules["swebench.harness.constants"] = fake_constants
        sys.modules["swebench.harness.grading"] = fake_grading
        sys.modules["swebench.harness.test_spec.test_spec"] = fake_test_spec

        spec = importlib.util.spec_from_file_location(
            "run_evaluation_modal_under_test", MODULE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.clear()
        sys.modules.update(saved_modules)


class ModalImageBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_modal_module()

    def tearDown(self):
        FakeImage.reset()

    def test_build_modal_image_definition_uses_env_dockerfile(self):
        spec = FakeTestSpec(
            instance_id="django__django-1",
            language="py",
            base_dockerfile="\nFROM python-base\nRUN base\n",
            env_dockerfile="\nFROM env-base\nCOPY ./setup_env.sh /root/\nRUN env\n",
            instance_dockerfile="\nFROM instance-base\nCOPY ./setup_repo.sh /root/\nRUN repo\n",
        )

        base_image_ref, dockerfile_commands = self.module._build_modal_image_definition(
            spec
        )

        self.assertEqual(base_image_ref, "python-base")
        self.assertEqual(
            dockerfile_commands,
            [
                "RUN base",
                "COPY ./setup_env.sh /root/",
                "RUN env",
                "COPY ./setup_repo.sh /root/",
                "RUN repo",
                "ENTRYPOINT []",
                'CMD ["/bin/sh", "-lc", "while true; do sleep 3600; done"]',
            ],
        )

    def test_build_modal_image_definition_skips_duplicate_env_stage(self):
        spec = FakeTestSpec(
            instance_id="google__gson-2061",
            language="java",
            base_dockerfile="\nFROM java-base\nRUN base\n",
            env_dockerfile="\nFROM java-base\nRUN base\n",
            instance_dockerfile="\nFROM instance-base\nRUN repo\n",
        )

        base_image_ref, dockerfile_commands = self.module._build_modal_image_definition(
            spec
        )

        self.assertEqual(base_image_ref, "java-base")
        self.assertEqual(len(dockerfile_commands), 4)
        self.assertEqual(dockerfile_commands[0], "RUN base")
        self.assertIn("RUN repo", dockerfile_commands[1])
        self.assertEqual(dockerfile_commands[-2], "ENTRYPOINT []")
        self.assertEqual(
            dockerfile_commands[-1],
            'CMD ["/bin/sh", "-lc", "while true; do sleep 3600; done"]',
        )

    def test_get_modal_sandbox_lifecycle_commands_override_entrypoint_and_cmd(self):
        self.assertEqual(
            self.module._get_modal_sandbox_lifecycle_commands(),
            [
                "ENTRYPOINT []",
                'CMD ["/bin/sh", "-lc", "while true; do sleep 3600; done"]',
            ],
        )

    def test_get_instance_image_patches_python_env_script_for_modal(self):
        spec = FakeTestSpec(
            instance_id="sympy__sympy-1",
            language="py",
            base_dockerfile="\nFROM python-base\nRUN base\n",
            env_dockerfile="\nFROM env-base\nCOPY ./setup_env.sh /root/\nRUN env\n",
            instance_dockerfile="\nFROM instance-base\nCOPY ./setup_repo.sh /root/\nRUN repo\n",
            setup_env_script=(
                "#!/bin/bash\n"
                "conda activate testbed && python -m pip install -r $HOME/requirements.txt\n"
            ),
        )

        self.module.ModalSandboxRuntime.get_instance_image(spec)
        tag, kwargs = FakeImage.last_from_registry
        commands, dockerfile_kwargs = FakeImage.last_dockerfile_commands
        build_dir = Path(dockerfile_kwargs["context_dir"])
        self.addCleanup(shutil.rmtree, build_dir, ignore_errors=True)

        self.assertEqual(tag, "python-base")
        self.assertNotIn("add_python", kwargs)
        self.assertIn("COPY ./setup_env.sh /root/", commands)
        self.assertIn(
            "--trusted-host pypi-mirror.modal.local",
            (build_dir / "setup_env.sh").read_text(encoding="utf-8"),
        )

    def test_get_instance_image_adds_python_when_base_image_needs_it(self):
        spec = FakeTestSpec(
            instance_id="google__gson-2061",
            language="java",
            base_dockerfile="\nFROM java-base\nRUN base\n",
            env_dockerfile="\nFROM java-base\nRUN base\n",
            instance_dockerfile="\nFROM instance-base\nRUN repo\n",
        )

        self.module.ModalSandboxRuntime.get_instance_image(spec)
        _, kwargs = FakeImage.last_from_registry
        _, dockerfile_kwargs = FakeImage.last_dockerfile_commands
        build_dir = Path(dockerfile_kwargs["context_dir"])
        self.addCleanup(shutil.rmtree, build_dir, ignore_errors=True)

        self.assertEqual(kwargs["add_python"], "3.11")

    def test_get_instance_image_skips_add_python_for_classic_js_images(self):
        spec = FakeTestSpec(
            instance_id="markedjs__marked-1",
            language="js",
            base_dockerfile="\nFROM js-base\nRUN base\n",
            env_dockerfile="\nFROM js-env\nCOPY ./setup_env.sh /root/\nRUN env\n",
            instance_dockerfile="\nFROM instance-base\nRUN repo\n",
            docker_specs={"node_version": "20"},
        )

        self.module.ModalSandboxRuntime.get_instance_image(spec)
        _, kwargs = FakeImage.last_from_registry
        _, dockerfile_kwargs = FakeImage.last_dockerfile_commands
        build_dir = Path(dockerfile_kwargs["context_dir"])
        self.addCleanup(shutil.rmtree, build_dir, ignore_errors=True)

        self.assertNotIn("add_python", kwargs)

    def test_get_instance_image_adds_python_for_js_2_variant(self):
        spec = FakeTestSpec(
            instance_id="babel__babel-14532",
            language="js",
            base_dockerfile="\nFROM js2-base\nRUN base\n",
            env_dockerfile="\nFROM js2-base\nRUN base\n",
            instance_dockerfile="\nFROM instance-base\nRUN repo\n",
            docker_specs={"node_version": "20", "_variant": "js_2"},
        )

        self.module.ModalSandboxRuntime.get_instance_image(spec)
        _, kwargs = FakeImage.last_from_registry
        _, dockerfile_kwargs = FakeImage.last_dockerfile_commands
        build_dir = Path(dockerfile_kwargs["context_dir"])
        self.addCleanup(shutil.rmtree, build_dir, ignore_errors=True)

        self.assertEqual(kwargs["add_python"], "3.11")

    def test_add_sandbox_entrypoint_uses_local_entrypoint_file(self):
        self.module._add_sandbox_entrypoint(FakeImage())

        local_path, remote_path, _ = FakeImage.last_add_local_file

        self.assertEqual(local_path, self.module.LOCAL_SANDBOX_ENTRYPOINT_PATH)
        self.assertEqual(remote_path, self.module.REMOTE_SANDBOX_ENTRYPOINT_PATH)

    def test_build_eval_run_command_only_sets_recursion_limit_for_python(self):
        py_spec = FakeTestSpec(
            instance_id="django__django-1",
            language="py",
            base_dockerfile="",
            env_dockerfile="",
            instance_dockerfile="",
        )
        java_spec = FakeTestSpec(
            instance_id="google__gson-2061",
            language="java",
            base_dockerfile="",
            env_dockerfile="",
            instance_dockerfile="",
        )

        py_command = self.module._build_eval_run_command(py_spec, "/root/eval.sh")
        java_command = self.module._build_eval_run_command(java_spec, "/root/eval.sh")

        self.assertIn("sys.setrecursionlimit(10000)", py_command)
        self.assertNotIn("sys.setrecursionlimit(10000)", java_command)
        self.assertTrue(java_command.endswith("&& /bin/bash /root/eval.sh"))


if __name__ == "__main__":
    unittest.main()
