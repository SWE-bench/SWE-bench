# Constants - Task Instance Installation Environment
SPECS_RIPGREP = {
    "2576": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ripgrep --test integration --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package ripgrep --test integration -- regression"
        ],
    },
    "2209": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ripgrep --test integration --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package ripgrep --test integration -- regression::r2208 --exact"
        ],
    },
}

SPECS_BAT = {
    "3108": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests pag --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests pag"
        ],
    },
    "2835": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests header --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests header"
        ],
    },
    "2650": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests map_syntax --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests map_syntax"
        ],
    },
    "2393": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests cache_ --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests cache_"
        ],
    },
    "2201": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests pag --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests pag"
        ],
    },
    "2260": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests syntax --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests syntax"
        ],
    },
    "1892": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests ignored_suffix_arg --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests ignored_suffix_arg"
        ],
    },
    "562": {
        "docker_specs": {"rust_version": "1.81"},
        # Any fetch or build command makes the gold patch fail for some reason
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package bat --test integration_tests cache"
        ],
    },
}

SPECS_RUFF = {
    "15626": {
        "docker_specs": {"rust_version": "1.84"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ruff_linter --lib rules::flake8_simplify::tests --no-run"
        ],
        "test_cmd": [
            "cargo test --package ruff_linter --lib rules::flake8_simplify::tests",
        ],
    },
    "15543": {
        "docker_specs": {"rust_version": "1.84"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ruff_linter --lib rules::pyupgrade --no-run"
        ],
        "test_cmd": [
            "cargo test --package ruff_linter --lib rules::pyupgrade",
        ],
    },
    "15443": {
        "docker_specs": {"rust_version": "1.84"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ruff_linter --lib rules::flake8_bandit --no-run"
        ],
        "test_cmd": [
            "cargo test --package ruff_linter --lib rules::flake8_bandit",
        ],
    },
    "15394": {
        "docker_specs": {"rust_version": "1.83"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ruff_linter --lib rules::flake8_pie --no-run"
        ],
        "test_cmd": [
            "cargo test --package ruff_linter --lib rules::flake8_pie",
        ],
    },
    "15356": {
        "docker_specs": {"rust_version": "1.83"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ruff_linter --lib rules::pycodestyle --no-run"
        ],
        "test_cmd": [
            "cargo test --package ruff_linter --lib rules::pycodestyle",
        ],
    },
    "15330": {
        "docker_specs": {"rust_version": "1.83"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package ruff_linter --lib rules::eradicate --no-run"
        ],
        "test_cmd": [
            "cargo test --package ruff_linter --lib rules::eradicate",
        ],
    },
    "15309": {
        "docker_specs": {"rust_version": "1.83"},
        "install": ["RUSTFLAGS=-Awarnings cargo test --package ruff_linter --no-run"],
        "test_cmd": [
            "cargo test --package ruff_linter 'f52'",
        ],
    },
}

TOKIO_SPECS = {
    "6724": {
        "docker_specs": {"rust_version": "1.81"},
        # install only as much as needed to run the tests
        "install": ["cargo test --test io_write_all_buf --no-fail-fast --no-run"],
        # no build step, cargo test will build the relevant packages
        "test_cmd": ["cargo test --test io_write_all_buf --no-fail-fast"],
    },
    "6838": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test --test uds_stream --no-fail-fast --no-run"],
        "test_cmd": ["cargo test --test uds_stream --no-fail-fast"],
    },
    "6752": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test --test time_delay_queue --no-fail-fast --no-run"],
        "test_cmd": ["cargo test --test time_delay_queue --no-fail-fast"],
    },
    "4867": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test --test sync_broadcast --no-fail-fast --no-run"],
        "test_cmd": ["cargo test --test sync_broadcast --no-fail-fast"],
    },
    "4898": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            'RUSTFLAGS="--cfg tokio_unstable" cargo test --features full --test rt_metrics --no-run'
        ],
        "test_cmd": [
            'RUSTFLAGS="--cfg tokio_unstable" cargo test --features full --test rt_metrics'
        ],
    },
    "6603": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test --test sync_mpsc --no-fail-fast --no-run"],
        "test_cmd": ["cargo test --test sync_mpsc --no-fail-fast"],
    },
    "6551": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            'RUSTFLAGS="--cfg tokio_unstable" cargo test --features full --test rt_metrics --no-fail-fast --no-run'
        ],
        "test_cmd": [
            'RUSTFLAGS="--cfg tokio_unstable" cargo test --features full --test rt_metrics --no-fail-fast'
        ],
    },
    "4384": {
        "docker_specs": {"rust_version": "1.81"},
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package tokio --test net_types_unwind --features full --no-fail-fast"
        ],
    },
    "7139": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            'RUSTFLAGS="--cfg tokio_unstable" cargo test --test fs_file --no-fail-fast --no-run'
        ],
        "test_cmd": [
            'RUSTFLAGS="--cfg tokio_unstable" cargo test --test fs_file --no-fail-fast'
        ],
    },
}

COREUTILS_SPECS = {
    "6690": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "cargo test --no-run -- test_cp_cp test_cp_same_file test_cp_multiple_files test_cp_single_file test_cp_no_file",
        ],
        "test_cmd": [
            "cargo test --no-fail-fast -- test_cp_cp test_cp_same_file test_cp_multiple_files test_cp_single_file test_cp_no_file",
        ],
    },
    "6731": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test backslash --no-run"],
        "test_cmd": ["cargo test backslash --no-fail-fast"],
    },
    "6575": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test cksum --no-run"],
        "test_cmd": ["cargo test cksum --no-fail-fast"],
    },
    "6682": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test mkdir --no-run"],
        "test_cmd": ["cargo test mkdir --no-fail-fast"],
    },
    "6377": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["cargo test test_env --no-run"],
        "test_cmd": ["cargo test test_env --no-fail-fast"],
    },
}

NUSHELL_SPECS = {
    "13246": {
        "docker_specs": {"rust_version": "1.77"},
        "install": ["cargo test -p nu-command --no-run --test main find::"],
        "build": ["cargo build"],
        "test_cmd": ["cargo test -p nu-command --no-fail-fast --test main find::"],
    },
    "12950": {
        "docker_specs": {"rust_version": "1.77"},
        "install": ["cargo test external_arguments --no-run"],
        "test_cmd": ["cargo test external_arguments --no-fail-fast"],
    },
    "12901": {
        "docker_specs": {"rust_version": "1.77"},
        "install": ["cargo test --no-run shell::env"],
        "test_cmd": ["cargo test --no-fail-fast shell::env"],
    },
    "13831": {
        "docker_specs": {"rust_version": "1.79"},
        "install": ["cargo test -p nu-command --no-run split_column"],
        "build": ["cargo build"],
        "test_cmd": ["cargo test -p nu-command --no-fail-fast split_column"],
    },
    "13605": {
        "docker_specs": {"rust_version": "1.78"},
        "install": ["cargo test -p nu-command --no-run ls::"],
        "build": ["cargo build"],
        "test_cmd": ["cargo test -p nu-command --no-fail-fast ls::"],
    },
}

AXUM_SPECS = {
    "2096": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["RUSTFLAGS=-Awarnings cargo test --package axum --lib --no-run"],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib -- routing::tests::fallback"
        ],
    },
    "1934": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["RUSTFLAGS=-Awarnings cargo test --package axum --lib --no-run"],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib -- routing::tests::fallback"
        ],
    },
    # All tests for 1730 are PASS_TO_PASS since it tests compilation
    "1730": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["RUSTFLAGS=-Awarnings cargo test --package axum --lib --no-run"],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib -- routing::tests::mod state"
        ],
    },
    "1119": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib slash --no-run"
        ],
        "test_cmd": ["RUSTFLAGS=-Awarnings cargo test --package axum --lib slash"],
    },
    "734": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["RUSTFLAGS=-Awarnings cargo test --package axum --lib --no-run"],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib -- routing::tests::head"
        ],
    },
    "691": {
        "docker_specs": {"rust_version": "1.81"},
        "install": ["RUSTFLAGS=-Awarnings cargo test --package axum --lib --no-run"],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib -- routing::tests::nest::nesting_router_at_root --exact"
        ],
    },
    "682": {
        "docker_specs": {"rust_version": "1.81"},
        "install": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib trailing --no-run"
        ],
        "test_cmd": [
            "RUSTFLAGS=-Awarnings cargo test --package axum --lib trailing -- with_trailing_slash_post without_trailing_slash_post"
        ],
    },
}

MAP_REPO_VERSION_TO_SPECS_RUST = {
    "burntsushi/ripgrep": SPECS_RIPGREP,
    "sharkdp/bat": SPECS_BAT,
    "astral-sh/ruff": SPECS_RUFF,
    "tokio-rs/tokio": TOKIO_SPECS,
    "uutils/coreutils": COREUTILS_SPECS,
    "nushell/nushell": NUSHELL_SPECS,
    "tokio-rs/axum": AXUM_SPECS,
}

# Constants - Repository Specific Installation Instructions
MAP_REPO_TO_INSTALL_RUST = {}
