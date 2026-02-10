"""Tests for the --arch parameter that enables ARM64 Docker image builds."""

import collections

from swebench.harness.constants import (
    FAIL_TO_PASS,
    PASS_TO_PASS,
    KEY_INSTANCE_ID,
)
from swebench.harness.test_spec.test_spec import (
    make_test_spec,
    get_test_specs_from_dataset,
    TestSpec,
)


# Minimal test instance matching existing test patterns
def _make_instance(**overrides):
    instance = collections.defaultdict(lambda: "test")
    instance[PASS_TO_PASS] = "[]"
    instance[FAIL_TO_PASS] = "[]"
    instance["repo"] = "pvlib/pvlib-python"
    instance["version"] = "0.1"
    instance.update(overrides)
    return instance


class TestMakeTestSpecArch:
    """Test that make_test_spec correctly handles the arch parameter."""

    def test_default_arch_is_x86_64(self):
        spec = make_test_spec(_make_instance())
        assert spec.arch == "x86_64"

    def test_x86_64_platform(self):
        spec = make_test_spec(_make_instance(), arch="x86_64")
        assert spec.platform == "linux/x86_64"

    def test_arm64_platform(self):
        spec = make_test_spec(_make_instance(), arch="arm64")
        assert spec.platform == "linux/arm64/v8"

    def test_arm64_arch_stored(self):
        spec = make_test_spec(_make_instance(), arch="arm64")
        assert spec.arch == "arm64"

    def test_invalid_arch_raises(self):
        spec = make_test_spec(_make_instance(), arch="mips")
        try:
            _ = spec.platform
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "Invalid architecture" in str(e)


class TestImageKeysArch:
    """Test that image keys correctly include the architecture."""

    def test_instance_image_key_x86_64(self):
        spec = make_test_spec(_make_instance(), arch="x86_64")
        assert "x86_64" in spec.instance_image_key
        assert "arm64" not in spec.instance_image_key

    def test_instance_image_key_arm64(self):
        spec = make_test_spec(_make_instance(), arch="arm64")
        assert "arm64" in spec.instance_image_key
        assert "x86_64" not in spec.instance_image_key

    def test_base_image_key_contains_arch(self):
        spec_x86 = make_test_spec(_make_instance(), arch="x86_64")
        spec_arm = make_test_spec(_make_instance(), arch="arm64")
        assert "x86_64" in spec_x86.base_image_key
        assert "arm64" in spec_arm.base_image_key

    def test_env_image_key_contains_arch(self):
        spec_x86 = make_test_spec(_make_instance(), arch="x86_64")
        spec_arm = make_test_spec(_make_instance(), arch="arm64")
        assert "x86_64" in spec_x86.env_image_key
        assert "arm64" in spec_arm.env_image_key

    def test_different_arch_different_keys(self):
        spec_x86 = make_test_spec(_make_instance(), arch="x86_64")
        spec_arm = make_test_spec(_make_instance(), arch="arm64")
        assert spec_x86.instance_image_key != spec_arm.instance_image_key
        assert spec_x86.base_image_key != spec_arm.base_image_key
        assert spec_x86.env_image_key != spec_arm.env_image_key


class TestGetTestSpecsFromDatasetArch:
    """Test that get_test_specs_from_dataset forwards arch correctly."""

    def test_default_arch(self):
        dataset = [_make_instance()]
        specs = get_test_specs_from_dataset(dataset)
        assert specs[0].arch == "x86_64"

    def test_arm64_forwarded(self):
        dataset = [_make_instance()]
        specs = get_test_specs_from_dataset(dataset, arch="arm64")
        assert specs[0].arch == "arm64"
        assert specs[0].platform == "linux/arm64/v8"

    def test_idempotent_with_test_specs(self):
        """If dataset already contains TestSpec objects, return them as-is."""
        spec = make_test_spec(_make_instance(), arch="arm64")
        result = get_test_specs_from_dataset([spec], arch="x86_64")
        # Should return existing specs unchanged (idempotent)
        assert result[0].arch == "arm64"

    def test_multiple_instances(self):
        dataset = [_make_instance(), _make_instance()]
        specs = get_test_specs_from_dataset(dataset, arch="arm64")
        assert all(s.arch == "arm64" for s in specs)
        assert all(s.platform == "linux/arm64/v8" for s in specs)
