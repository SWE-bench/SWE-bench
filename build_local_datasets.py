"""
Build local parquet datasets with metadata and eval scripts from dockerfile generators.

Adds `log_parser`, `eval_type`, `eval_script`, and `image` fields to each datum.
Validates that every datum has all required fields with no missing/default values.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from datasets import load_dataset

# ---------------------------------------------------------------------------
# Eval script generation via subprocess (avoids namespace conflicts between
# the three sb_dockerfile_gen packages).
# ---------------------------------------------------------------------------

_CODE_ROOT = Path(os.environ.get("SWE_BENCH_CODE_ROOT", Path(__file__).resolve().parent.parent))
DOCKERFILE_REPOS = {
    "og": _CODE_ROOT / "swe-bench-dockerfiles",
    "multilingual": _CODE_ROOT / "swe-bench-multilingual-dockerfiles",
    "multimodal": _CODE_ROOT / "swe-bench-multimodal-dockerfiles",
}

# Inline script that loads a generator and produces eval scripts for a batch
_EVAL_GEN_SCRIPT = """\
import json, sys
sys.path.insert(0, sys.argv[1])
from sb_dockerfile_gen import _get_eval_script
instances = json.loads(sys.stdin.read())
results = {}
for inst in instances:
    results[inst["instance_id"]] = _get_eval_script(inst)
json.dump(results, sys.stdout)
"""


def generate_eval_scripts(
    generator_key: str,
    instances: list[dict],
) -> dict[str, str]:
    """Generate eval scripts for a batch of instances using the appropriate generator."""
    repo_path = DOCKERFILE_REPOS[generator_key]
    src_path = str(repo_path / "src")

    # Serialize instances to JSON for the subprocess
    input_data = json.dumps(instances)

    result = subprocess.run(
        [sys.executable, "-c", _EVAL_GEN_SCRIPT, src_path],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Eval script generation failed for {generator_key}:\n{result.stderr}"
        )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Constants extracted from the three dockerfile-gen packages.
# ---------------------------------------------------------------------------

MAP_REPO_TO_PARSER_NAME_OG = {
    "astropy/astropy": "parse_log_astropy",
    "django/django": "parse_log_django",
    "marshmallow-code/marshmallow": "parse_log_marshmallow",
    "matplotlib/matplotlib": "parse_log_matplotlib",
    "mwaskom/seaborn": "parse_log_seaborn",
    "pallets/flask": "parse_log_flask",
    "psf/requests": "parse_log_requests",
    "pvlib/pvlib-python": "parse_log_pvlib",
    "pydata/xarray": "parse_log_xarray",
    "pydicom/pydicom": "parse_log_pydicom",
    "pylint-dev/astroid": "parse_log_astroid",
    "pylint-dev/pylint": "parse_log_pylint",
    "pytest-dev/pytest": "parse_log_pytest",
    "pyvista/pyvista": "parse_log_pyvista",
    "scikit-learn/scikit-learn": "parse_log_scikit",
    "sqlfluff/sqlfluff": "parse_log_sqlfluff",
    "sphinx-doc/sphinx": "parse_log_sphinx",
    "sympy/sympy": "parse_log_sympy",
}
FAIL_ONLY_REPOS_OG: set[str] = set()

MAP_REPO_TO_PARSER_NAME_MULTILINGUAL = {
    "redis/redis": "parse_log_redis",
    "jqlang/jq": "parse_log_jq",
    "nlohmann/json": "parse_log_doctest",
    "micropython/micropython": "parse_log_micropython_test",
    "valkey-io/valkey": "parse_log_redis",
    "fmtlib/fmt": "parse_log_googletest",
    "caddyserver/caddy": "parse_log_gotest",
    "hashicorp/terraform": "parse_log_gotest",
    "prometheus/prometheus": "parse_log_gotest",
    "gohugoio/hugo": "parse_log_gotest",
    "gin-gonic/gin": "parse_log_gotest",
    "google/gson": "parse_log_maven",
    "apache/druid": "parse_log_maven",
    "javaparser/javaparser": "parse_log_maven",
    "projectlombok/lombok": "parse_log_ant",
    "apache/lucene": "parse_log_gradle_custom",
    "reactivex/rxjava": "parse_log_gradle_custom",
    "Automattic/wp-calypso": "parse_log_calypso",
    "chartjs/Chart.js": "parse_log_chart_js",
    "markedjs/marked": "parse_log_marked",
    "processing/p5.js": "parse_log_p5js",
    "diegomura/react-pdf": "parse_log_react_pdf",
    "babel/babel": "parse_log_jest",
    "vuejs/core": "parse_log_vitest",
    "facebook/docusaurus": "parse_log_jest",
    "immutable-js/immutable-js": "parse_log_immutable_js",
    "mrdoob/three.js": "parse_log_tap",
    "preactjs/preact": "parse_log_karma",
    "axios/axios": "parse_log_tap",
    "phpoffice/phpspreadsheet": "parse_log_phpunit",
    "laravel/framework": "parse_log_phpunit",
    "php-cs-fixer/php-cs-fixer": "parse_log_phpunit",
    "briannesbitt/carbon": "parse_log_phpunit",
    "jekyll/jekyll": "parse_log_jekyll",
    "fluent/fluentd": "parse_log_ruby_unit",
    "fastlane/fastlane": "parse_log_rspec_transformed_json",
    "jordansissel/fpm": "parse_log_rspec_transformed_json",
    "faker-ruby/faker": "parse_log_ruby_unit",
    "rubocop/rubocop": "parse_log_rspec_transformed_json",
    "burntsushi/ripgrep": "parse_log_cargo",
    "sharkdp/bat": "parse_log_cargo",
    "astral-sh/ruff": "parse_log_cargo",
    "tokio-rs/tokio": "parse_log_cargo",
    "uutils/coreutils": "parse_log_cargo",
    "nushell/nushell": "parse_log_cargo",
    "tokio-rs/axum": "parse_log_cargo",
}
FAIL_ONLY_REPOS_MULTILINGUAL: set[str] = set()

MAP_REPO_TO_PARSER_NAME_MULTIMODAL = {
    "Automattic/wp-calypso": "parse_log_calypso",
    "chartjs/Chart.js": "parse_log_chart_js",
    "markedjs/marked": "parse_log_marked",
    "processing/p5.js": "parse_log_p5js",
    "diegomura/react-pdf": "parse_log_react_pdf",
    "babel/babel": "parse_log_jest",
    "vuejs/core": "parse_log_vitest",
    "facebook/docusaurus": "parse_log_jest",
    "immutable-js/immutable-js": "parse_log_immutable_js",
    "mrdoob/three.js": "parse_log_tap",
    "preactjs/preact": "parse_log_karma",
    "axios/axios": "parse_log_tap",
}
FAIL_ONLY_REPOS_MULTIMODAL = {
    "chartjs/Chart.js",
    "processing/p5.js",
    "markedjs/marked",
}

# ---------------------------------------------------------------------------
# Image name helper
# ---------------------------------------------------------------------------


def get_image_name(instance_id: str) -> str:
    return f"amd64.{instance_id}:latest".lower()


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

METADATA_FIELDS = {"log_parser", "eval_type", "eval_script", "image"}

BASE_REQUIRED_FIELDS = {
    "repo",
    "instance_id",
    "base_commit",
    "patch",
    "test_patch",
    "problem_statement",
    "hints_text",
    "created_at",
    "version",
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
}


# ---------------------------------------------------------------------------
# Upstream dataset corrections
# ---------------------------------------------------------------------------
# Fixes for known issues in the HuggingFace dataset that can't be fixed in the
# dockerfile generator. Each entry maps instance_id to field overrides.
# See SWE-bench-v5_1/CHANGES.md for detailed root cause analysis.

UPSTREAM_FIXES = {
    # #505: pytest renders empty parametrize marker as [unit0], not [].
    # Grader does exact string match on P2P test names, so it fails.
    "astropy__astropy-7606": {
        "PASS_TO_PASS": lambda p2p: [
            t.replace("test_compose_roundtrip[]", "test_compose_roundtrip[unit0]")
            if "test_compose_roundtrip[]" in t else t
            for t in p2p
        ],
    },
    # #487: eval_script runs ALL Django tests (no test directive). F2P has 438
    # unrelated tests that pass regardless of the fix. The actual discriminating
    # tests are 6 URLValidator entries added by test_patch to invalid_urls.txt.
    "django__django-10097": {
        "FAIL_TO_PASS": lambda f2p: f2p + [
            "test_URLValidator_raises_error_352 (validators.tests.TestSimpleValidators)",
            "test_URLValidator_raises_error_353 (validators.tests.TestSimpleValidators)",
            "test_URLValidator_raises_error_354 (validators.tests.TestSimpleValidators)",
            "test_URLValidator_raises_error_355 (validators.tests.TestSimpleValidators)",
            "test_URLValidator_raises_error_356 (validators.tests.TestSimpleValidators)",
            "test_URLValidator_raises_error_357 (validators.tests.TestSimpleValidators)",
        ],
    },
    # #502: F2P has test_squashmigrations_initial_attribute — unrelated test that
    # passes regardless. The actual discriminating test is in the test_patch.
    "django__django-7530": {
        "FAIL_TO_PASS": lambda f2p: [
            "test_makemigrations_consistency_checks_respect_routers (migrations.test_commands.MakeMigrationsTests)"
        ],
    },
    # #484: Bug only manifests on Python 2 (builtin_str fix). F2P has 6 unrelated
    # tests that pass on any Python version. Correct F2P is the unicode method test.
    # Note: also requires Python 2.7 Docker image (fixed in swe-bench-dockerfiles).
    "psf__requests-1724": {
        "FAIL_TO_PASS": lambda f2p: [
            "test_requests.py::RequestsTestCase::test_unicode_method_name"
        ],
    },
}


def apply_upstream_fixes(ex: dict) -> dict:
    """Apply known upstream dataset corrections to an instance."""
    iid = ex["instance_id"]
    if iid not in UPSTREAM_FIXES:
        return ex
    fixes = UPSTREAM_FIXES[iid]
    for field, fix_fn in fixes.items():
        val = ex[field]
        if isinstance(val, str):
            val = json.loads(val)
        ex[field] = json.dumps(fix_fn(val))
    return ex


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def validate_no_missing(example: dict, all_required: set[str], dataset_label: str):
    """Raise if any required field is missing or None."""
    for field in all_required:
        if field not in example:
            raise ValueError(
                f"[{dataset_label}] instance {example.get('instance_id', '???')}: "
                f"missing field '{field}'"
            )
        val = example[field]
        if val is None:
            raise ValueError(
                f"[{dataset_label}] instance {example.get('instance_id', '???')}: "
                f"field '{field}' is None"
            )


def process_dataset(
    hf_name: str,
    parser_map: dict[str, str],
    fail_only_repos: set[str],
    generator_key: str,
    output_dir: Path,
    label: str,
    extra_required_fields: set[str] | None = None,
    splits: list[str] | None = None,
):
    print(f"\n{'='*60}")
    print(f"Processing: {hf_name} -> {output_dir}")
    print(f"{'='*60}")

    ds_dict = load_dataset(hf_name)
    all_required = BASE_REQUIRED_FIELDS | METADATA_FIELDS
    if extra_required_fields:
        all_required = all_required | extra_required_fields

    if splits is not None:
        ds_dict = {k: v for k, v in ds_dict.items() if k in splits}

    for split_name, ds in ds_dict.items():
        print(f"  Split '{split_name}': {len(ds)} instances")

        # Generate eval scripts in a subprocess (batch)
        instances = list(ds)
        print(f"    Generating eval scripts via {generator_key} generator...")
        eval_scripts = generate_eval_scripts(generator_key, instances)

        # Add all metadata columns
        def add_metadata(ex):
            repo = ex["repo"]
            if repo not in parser_map:
                raise ValueError(
                    f"[{label}/{split_name}] instance {ex['instance_id']}: "
                    f"repo '{repo}' not found in parser map"
                )
            ex["log_parser"] = parser_map[repo]
            ex["eval_type"] = "fail_only" if repo in fail_only_repos else "pass_and_fail"
            ex["eval_script"] = eval_scripts[ex["instance_id"]]
            ex["image"] = get_image_name(ex["instance_id"])
            return ex

        ds = ds.map(add_metadata)

        # Apply upstream dataset corrections
        ds = ds.map(apply_upstream_fixes)

        # Validate every row
        for i, ex in enumerate(ds):
            validate_no_missing(ex, all_required, f"{label}/{split_name}[{i}]")

        ds_dict[split_name] = ds

    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name, ds in ds_dict.items():
        out_path = output_dir / f"{split_name}.parquet"
        ds.to_parquet(str(out_path))
        print(f"  Saved {out_path} ({len(ds)} rows)")

    print(f"  Done: {label}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+",
                        choices=["verified", "multilingual", "multimodal", "swebench", "all"],
                        default=["all"])
    args = parser.parse_args()
    targets = set(args.datasets)
    if "all" in targets:
        targets = {"verified", "multilingual", "multimodal", "swebench"}

    base_output = Path(__file__).resolve().parent / "data"

    if "swebench" in targets:
        process_dataset(
            hf_name="SWE-bench/SWE-bench",
            parser_map=MAP_REPO_TO_PARSER_NAME_OG,
            fail_only_repos=FAIL_ONLY_REPOS_OG,
            generator_key="og",
            output_dir=base_output / "SWE-bench",
            label="SWE-bench",
            extra_required_fields={"environment_setup_commit"},
            splits=["dev", "test"],
        )

    if "verified" in targets:
        process_dataset(
            hf_name="SWE-bench/SWE-bench_Verified",
            parser_map=MAP_REPO_TO_PARSER_NAME_OG,
            fail_only_repos=FAIL_ONLY_REPOS_OG,
            generator_key="og",
            output_dir=base_output / "SWE-bench_Verified",
            label="SWE-bench_Verified",
            extra_required_fields={"environment_setup_commit", "difficulty"},
        )

    if "multilingual" in targets:
        process_dataset(
            hf_name="SWE-bench/SWE-bench_Multilingual",
            parser_map=MAP_REPO_TO_PARSER_NAME_MULTILINGUAL,
            fail_only_repos=FAIL_ONLY_REPOS_MULTILINGUAL,
            generator_key="multilingual",
            output_dir=base_output / "SWE-bench_Multilingual",
            label="SWE-bench_Multilingual",
        )

    if "multimodal" in targets:
        process_dataset(
            hf_name="SWE-bench/SWE-bench_Multimodal",
            parser_map=MAP_REPO_TO_PARSER_NAME_MULTIMODAL,
            fail_only_repos=FAIL_ONLY_REPOS_MULTIMODAL,
            generator_key="multimodal",
            output_dir=base_output / "SWE-bench_Multimodal",
            label="SWE-bench_Multimodal",
            extra_required_fields={"image_assets"},
            splits=["dev"],
        )

    print(f"\n{'='*60}")
    print("All datasets saved to:", base_output)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
