"""Tests for Java spec constants, particularly Lucene Maven resource bundle fix."""

from swebench.harness.constants.java import SPECS_LUCENE


class TestLuceneMavenResourceBundleFix:
    """Test that Lucene instances with Maven resource bundle SNAPSHOT reference
    have an install step to fix it.

    Fresh ARM64 Docker images don't have cached Maven artifacts, so the
    1.5-SNAPSHOT version of apache-jar-resource-bundle fails to resolve.
    The fix replaces 1.5-SNAPSHOT with the released 1.5 version.
    """

    SED_PATTERN = "apache-jar-resource-bundle:1.5-SNAPSHOT"
    SED_REPLACEMENT = "apache-jar-resource-bundle:1.5"

    def test_lucene_13170_has_install_with_maven_fix(self):
        spec = SPECS_LUCENE["13170"]
        assert "install" in spec, "Lucene 13170 must have install step for Maven fix"
        install_cmds = " ".join(spec["install"])
        assert self.SED_PATTERN in install_cmds
        assert self.SED_REPLACEMENT in install_cmds

    def test_lucene_13704_has_install_with_maven_fix(self):
        spec = SPECS_LUCENE["13704"]
        assert "install" in spec, "Lucene 13704 must have install step for Maven fix"
        install_cmds = " ".join(spec["install"])
        assert self.SED_PATTERN in install_cmds
        assert self.SED_REPLACEMENT in install_cmds

    def test_maven_fix_targets_pom_xml(self):
        """Verify the sed command targets pom.xml (root-level Maven config)."""
        for instance_id in ("13170", "13704"):
            spec = SPECS_LUCENE[instance_id]
            install_cmds = " ".join(spec["install"])
            assert "pom.xml" in install_cmds

    def test_maven_fix_uses_sed_inplace(self):
        """Verify the fix uses in-place sed (no temp file issues in Docker)."""
        for instance_id in ("13170", "13704"):
            spec = SPECS_LUCENE[instance_id]
            install_cmds = " ".join(spec["install"])
            assert "sed -i" in install_cmds

    def test_other_lucene_instances_unaffected(self):
        """Verify instances that don't need the fix don't have it."""
        unaffected = ["13494", "13301", "12626", "12212", "12196", "12022", "11760"]
        for instance_id in unaffected:
            spec = SPECS_LUCENE[instance_id]
            assert "install" not in spec, (
                f"Lucene {instance_id} should not have install step"
            )

    def test_affected_instances_still_have_pre_install(self):
        """Verify the fix didn't accidentally remove pre_install."""
        for instance_id in ("13170", "13704"):
            spec = SPECS_LUCENE[instance_id]
            assert "pre_install" in spec
            assert len(spec["pre_install"]) > 0

    def test_affected_instances_still_have_test_cmd(self):
        """Verify the fix didn't accidentally remove test_cmd."""
        for instance_id in ("13170", "13704"):
            spec = SPECS_LUCENE[instance_id]
            assert "test_cmd" in spec
            assert len(spec["test_cmd"]) > 0
