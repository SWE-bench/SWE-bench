import json
import re

from pathlib import Path
from swebench.harness.constants import (
    END_TEST_OUTPUT,
    MAP_REPO_VERSION_TO_SPECS,
    SET_OPENSSL_TO_LEGACY,
    SET_PUPPETEER_ENV_VAR,
    START_TEST_OUTPUT,
    TEST_XVFB_PREFIX,
)
from swebench.harness.test_spec.utils import make_eval_script_list_common
from unidiff import PatchSet


# MARK: Test Command Creation Functions
# Note - This design ended up being necessary for JS (but not for Python) because
# JS testing frameworks tend *not* to accept direct file paths as arguments, unlike Python.
# Instead, they usually require patterns that match test names or directories, which can
# be tricky to discern consistently from the test patch.

def get_test_cmds_prism(instance) -> list:
    directives = []
    test_cmd = MAP_REPO_VERSION_TO_SPECS[instance["repo"]][instance["version"]]["test_cmd"]
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    for test_path in test_paths:
        if test_path.startswith("tests/languages"):
            directives.append(test_cmd + f" --language {test_path.split('/')[2]}")
        elif test_path == "tests/core/greedy.js":
            directives.append("./node_modules/.bin/mocha tests/core/**/*.js --reporter json")
        elif test_path == "test.html":
            continue
    return sorted(list(set(directives)))


def get_test_cmds_insomnia(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    packages = set()
    new_test_cmd = []
    for path in test_paths:
        if path.startswith("packages/"):
            packages.add(path.split('/')[1])
    for package in packages:
        new_test_cmd.append((
            f"(cd packages/{package} && npm install && "
            "npm run build && npm run test; exit_code=$?; "
            "cd ../..; exit $exit_code)"
        ))
    return new_test_cmd


def get_test_cmds_openlayers(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    cmds = []
    for test_path in test_paths:
        # Tests usually are formatted as 'tests/<type>/...'
        test_type = test_path.split('/')[1]
        if test_type == "browser":
            if instance["version"] in ['6.9', '6.12', '6.14', '7.0', '7.1', '7.2', '7.3', '7.5']:
                # Browser testing moved from chrome to chrome headless at some point
                cmds.append(f'su chromeuser -c "npm run test-browser"')
            else:
                cmds.append(
                    f'{SET_PUPPETEER_ENV_VAR} {TEST_XVFB_PREFIX} '
                    'su chromeuser -c "npm run test-browser"'
                )
        elif test_type == "rendering":
            # CI=true -> puppeteer headless; headed Chrome under Xvfb hangs on WebGL
            cmds.append(
                f'{SET_PUPPETEER_ENV_VAR} {TEST_XVFB_PREFIX} '
                'su chromeuser -c "CI=true npm run test-rendering"'
            )
        elif test_type == "spec":
            cmds.append(
                f"{SET_PUPPETEER_ENV_VAR} {TEST_XVFB_PREFIX} "
                'su chromeuser -c "npm run karma -- --single-run --log-level error"'
            )                
        elif test_type == "node":
            cmds.append(f"npm run test-node")
        else:
            cmds.append("npm run test")
        if test_type in ['spec', 'rendering', 'browser'] and instance['version'] in [
                '6.1', '6.2', '6.3', '6.4', '6.5', '6.5.1', '6.6',
                '4.3', '4.4', '4.5', '4.6', '5.1', '5.2', '5.3'
            ]:
            cmds[-1] = f"{SET_OPENSSL_TO_LEGACY} {cmds[-1]}"
    return list(set(cmds))


def get_test_cmds_plotly(instance) -> list:
    # get the basenames of the tests files
    # for files that end in _test, remove the _test suffix
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_files = [Path(x).stem for x in test_paths]
    test_files = [x[:-5] if x.endswith("_test") else x for x in test_files]
    test_files = list(set(test_files))
    test_cmd = MAP_REPO_VERSION_TO_SPECS[instance["repo"]][instance["version"]]["test_cmd"]
    test_directives = ' '.join(test_files)
    test_cmd += f" -- {test_directives}"
    return [test_cmd]


def get_test_cmds_next(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_cmds = list(set([
        f'timeout 2m bash -c \'{SET_PUPPETEER_ENV_VAR} {TEST_XVFB_PREFIX} '
        f'su chromeuser -c "npm run test {test_path.split("/")[1]}"\''
        for test_path in test_paths
    ]))
    return test_cmds 


def get_test_cmds_cypress(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_cmds = []
    for test_file in test_paths:
        if any([
            test_file.startswith(x)
            for x in ["packages/driver", "packages/extension"]
        ]):
            test_folder = '/'.join(test_file.split('/')[:2])
            test_path = '/'.join(test_file.split('/')[2:])
            test_cmds.extend([
                f"cd {test_folder}",
                f"yarn workspace @{test_folder} cypress:run --spec {test_path} --reporter json",
                f"cd ../.."
            ])
        else:
            # Applies to packages/server, packages/launchpad
            test_folder = '/'.join(test_file.split('/')[:2])
            test_path = '/'.join(test_file.split('/')[2:])
            test_cmds.extend([
                f"cd {test_folder}",
                f"{TEST_XVFB_PREFIX} su chromeuser -c \"yarn test {test_path} --reporter json\"",
                f"cd ../.."
            ])
        # TODO: Handling for system-tests
    return test_cmds


def get_test_cmds_carbon(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_cmds = []
    for test_path in test_paths:
        if re.search(r"__snapshots__/(.*).js.snap$", test_path):
            # Jest snapshots are not run directly
            test_path = "/".join(test_path.split("/")[:-2])
        if "__tests__" in test_path:
            test_path = test_path.split("__tests__")[0]
        test_cmds.append(f"yarn test {test_path}")
    return list(set(test_cmds))


def get_test_cmds_scratch_gui(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_prefix = MAP_REPO_VERSION_TO_SPECS[instance['repo']][instance['version']]["test_cmd"]
    test_cmds = []
    for test_path in test_paths:
        if "__snapshots__" in test_path:
            test_path = test_path.split("__snapshots__")[0]
        test_cmds.append(f"{test_prefix} {test_path}")
    return list(set(test_cmds))


def get_test_cmds_lighthouse(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_cmds = []

    SUBDIRS = ["report", "cli", "report", "treemap", "viewer"]
    LH_PREFIX = "lighthouse-"

    for test_path in test_paths:
        # Skip non-test files and smoke tests
        if any([
            test_path.endswith(ext)
            for ext in [".html", ".json", ".md", ".txt"]
        ]) or "smokehouse" in test_path:
            continue

        parent_folder = test_path.split("/")[0]
        if instance["version"] in ['9.5', '10.0', '10.2']:
            if parent_folder == "flow-report":
                test_cmds.append("yarn unit-flow")
            elif parent_folder in SUBDIRS + [LH_PREFIX + x for x in SUBDIRS]:
                if parent_folder.startswith(LH_PREFIX):
                    parent_folder = parent_folder[len(LH_PREFIX):]
                test_cmds.append(f"yarn unit-{parent_folder} {test_path}")
            else:
                test_cmds.append(f"yarn mocha {test_path}")
        elif '3.0' <= instance['version'] and instance['version'] <= '8.6':
            test_cmds.append(f"yarn jest --no-colors {test_path}")
        else:
            test_cmds.append(f"./node_modules/.bin/mocha --reporter json {test_path}")

    return list(set(test_cmds))


def get_test_cmds_prettier(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_cmds = []
    for test_path in test_paths:
        if "__snapshots__" in test_path:
            test_path = test_path.split("__snapshots__")[0]
        if test_path.endswith(".md"):
            test_path = "/".join(test_path.split("/")[:-1])
        test_cmds.append(f"yarn test {test_path}")
    return sorted(set(test_cmds))


def get_test_cmds_react_pdf(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance['test_patch'])]
    test_cmds = []
    test_prefix = MAP_REPO_VERSION_TO_SPECS[instance['repo']][instance['version']]["test_cmd"]
    for test_path in test_paths:
        if any([test_path.endswith(x) for x in [".png"]]):
            continue
        elif test_path.startswith("packages/"):
            test_path = "/".join(test_path.split("/")[:2])
            test_cmds.append(f"{test_prefix} {test_path}")
        elif test_path.startswith("tests/"):
            test_cmds.append(test_prefix)
    return list(set(test_cmds))


def get_test_cmds_calypso(instance) -> list:
    test_paths = [x.path for x in PatchSet(instance["test_patch"])]
    test_cmds = []
    for test_path in test_paths:
        if re.search(r"__snapshots__/(.*).js.snap$", test_path):
            # Jest snapshots are not run directly
            test_path = "/".join(test_path.split("/")[:-2])

        # Determine which testing script to use
        if any([test_path.startswith(x) for x in ["client", "packages"]]):
            pkg = test_path.split("/")[0]
            if instance["version"] in [
                "10.10.0",
                "10.12.0",
                "10.13.0",
                "10.14.0",
                "10.15.2",
                "10.16.3",
            ]:
                test_cmds.append(
                    f"./node_modules/.bin/jest --verbose -c=test/{pkg}/jest.config.js '{test_path}'"
                )
            elif instance["version"] in [
                "6.11.5",
                "8.9.1",
                "8.9.3",
                "8.9.4",
                "8.11.0",
                "8.11.2",
                "10.4.1",
                "10.5.0",
                "10.6.0",
                "10.9.0",
            ]:
                test_cmds.append(
                    f"./node_modules/.bin/jest --verbose -c=test/{pkg}/jest.config.json '{test_path}'"
                )
            else:
                test_cmds.append(f"npm run test-{pkg} --verbose '{test_path}'")
        elif any([test_path.startswith(x) for x in ["test/e2e"]]):
            test_cmds.extend(
                [
                    "cd test/e2e",
                    f"NODE_CONFIG_ENV=test npm run test {test_path}",
                    "cd ../..",
                ]
            )

    return test_cmds


MAP_REPO_TO_TEST_CMDS = {
    "alibaba-fusion/next": get_test_cmds_next,
    "carbon-design-system/carbon": get_test_cmds_carbon,
    "cypress-io/cypress": get_test_cmds_cypress,
    "GoogleChrome/lighthouse": get_test_cmds_lighthouse,
    "Kong/insomnia": get_test_cmds_insomnia,
    "openlayers/openlayers": get_test_cmds_openlayers,
    "plotly/plotly.js": get_test_cmds_plotly,
    "prettier/prettier": get_test_cmds_prettier,
    "PrismJS/prism": get_test_cmds_prism,
    "scratchfoundation/scratch-gui": get_test_cmds_scratch_gui,
    "Automattic/wp-calypso": get_test_cmds_calypso,
}


def get_test_cmds(instance) -> list:
    if instance["repo"] in MAP_REPO_TO_TEST_CMDS:
        return MAP_REPO_TO_TEST_CMDS[instance["repo"]](instance)
    test_cmd = MAP_REPO_VERSION_TO_SPECS[instance["repo"]][instance["version"]][
        "test_cmd"
    ]
    return [test_cmd] if isinstance(test_cmd, str) else test_cmd


# MARK: Utility Functions
def get_download_img_commands(instance) -> list:
    cmds = []
    image_assets = {}
    if "image_assets" in instance:
        if isinstance(instance["image_assets"], str):
            image_assets = json.loads(instance["image_assets"])
        else:
            image_assets = instance["image_assets"]
    for i in image_assets.get("test_patch", []):
        folder = Path(i["path"]).parent
        cmds.append(f"mkdir -p {folder}")
        cmds.append(f"curl -o {i['path']} {i['url']}")
        cmds.append(f"chmod 777 {i['path']}")
    return cmds


_SYNC_DEPS_IF_MANIFEST_CHANGED = (
    'if ! git diff --quiet HEAD -- package.json 2>/dev/null; then '
    'echo "package.json changed by patch; re-syncing dependencies"; '
    # without the skip guard the install hangs forever fetching Chromium
    "export PUPPETEER_SKIP_DOWNLOAD=true PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true; "
    "if [ -f yarn.lock ]; then timeout 900 yarn install --silent > /dev/null 2>&1 || true; "
    "else timeout 900 npm install --silent > /dev/null 2>&1 || true; fi; "
    "chmod -R a+rX node_modules > /dev/null 2>&1 || true; "
    "fi"
)


# MARK: Script Creation Functions
def make_eval_script_list_js(
    instance, specs, env_name, repo_directory, base_commit, test_patch
) -> list:
    """
    Applies the test patch and runs the tests.
    """
    eval_commands = make_eval_script_list_common(
        instance, specs, env_name, repo_directory, base_commit, test_patch
    )
    # Insert downloading right after reset command
    eval_commands[4:4] = get_download_img_commands(instance)
    if instance["repo"] in MAP_REPO_TO_TEST_CMDS:
        # Update test commands if they are custom commands
        test_commands = MAP_REPO_TO_TEST_CMDS[instance["repo"]](instance)
        idx_start_test_out = eval_commands.index(f": '{START_TEST_OUTPUT}'")
        idx_end_test_out = eval_commands.index(f": '{END_TEST_OUTPUT}'")
        eval_commands[idx_start_test_out + 1 : idx_end_test_out] = test_commands
    # emitted before START_TEST_OUTPUT so installer output never reaches the log parsers
    idx_start = eval_commands.index(f": '{START_TEST_OUTPUT}'")
    eval_commands.insert(idx_start, _SYNC_DEPS_IF_MANIFEST_CHANGED)
    return eval_commands
