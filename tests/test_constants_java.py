"""Tests for Java spec constants, particularly Druid Maven resource bundle fix."""

from swebench.harness.constants.java import SPECS_DRUID, SPECS_LUCENE


class TestDruidMavenResourceBundleFix:
    """Test that all Druid instances have the Maven resource bundle SNAPSHOT fix.

    Fresh ARM64 Docker images lack cached Maven artifacts. Druid's root pom.xml
    references apache-jar-resource-bundle:1.5-SNAPSHOT which can't be resolved
    from public repos. The fix replaces 1.5-SNAPSHOT with the released 1.5 version.
    """

    SED_PATTERN = "apache-jar-resource-bundle:1.5-SNAPSHOT"
    SED_REPLACEMENT = "apache-jar-resource-bundle:1.5"
    ALL_DRUID_INSTANCES = ["13704", "14092", "14136", "15402", "16875"]

    def test_all_druid_instances_have_maven_fix(self):
        for instance_id in self.ALL_DRUID_INSTANCES:
            spec = SPECS_DRUID[instance_id]
            assert "install" in spec, (
                f"Druid {instance_id} must have install step"
            )
            install_cmds = " ".join(spec["install"])
            assert self.SED_PATTERN in install_cmds, (
                f"Druid {instance_id} missing Maven resource bundle fix"
            )

    def test_maven_fix_replaces_snapshot_with_release(self):
        for instance_id in self.ALL_DRUID_INSTANCES:
            install_cmds = " ".join(SPECS_DRUID[instance_id]["install"])
            assert self.SED_REPLACEMENT in install_cmds

    def test_maven_fix_targets_pom_xml(self):
        for instance_id in self.ALL_DRUID_INSTANCES:
            install_cmds = " ".join(SPECS_DRUID[instance_id]["install"])
            assert "pom.xml" in install_cmds

    def test_maven_fix_runs_before_mvn_install(self):
        """The sed fix must run before 'mvn clean install' to be effective."""
        for instance_id in self.ALL_DRUID_INSTANCES:
            install = SPECS_DRUID[instance_id]["install"]
            sed_idx = next(
                i for i, cmd in enumerate(install)
                if "sed" in cmd and "resource-bundle" in cmd
            )
            mvn_idx = next(
                i for i, cmd in enumerate(install) if "mvn clean install" in cmd
            )
            assert sed_idx < mvn_idx, (
                f"Druid {instance_id}: sed fix must run before mvn install"
            )

    def test_druid_instances_still_have_test_cmd(self):
        for instance_id in self.ALL_DRUID_INSTANCES:
            spec = SPECS_DRUID[instance_id]
            assert "test_cmd" in spec
            assert len(spec["test_cmd"]) > 0


class TestLuceneInstancesUnaffected:
    """Verify Lucene instances don't have the Druid-specific Maven fix."""

    def test_no_lucene_instance_has_install(self):
        for instance_id in SPECS_LUCENE:
            spec = SPECS_LUCENE[instance_id]
            assert "install" not in spec, (
                f"Lucene {instance_id} should not have install step "
                "(Lucene uses Gradle, not Maven)"
            )
