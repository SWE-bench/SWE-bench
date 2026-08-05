# Constants - Commonly Used Commands
TEST_XVFB_PREFIX = 'xvfb-run --server-args="-screen 0 1280x1024x24 -ac :99"'
XVFB_DEPS = [
    "python3",
    "python3-pip",
    "xvfb",
    "x11-xkb-utils",
    "xfonts-100dpi",
    "xfonts-75dpi",
    "xfonts-scalable",
    "xfonts-cyrillic",
    "x11-apps",
    "firefox",
]
X11_DEPS = [
    "libx11-xcb1",
    "libxcomposite1",
    "libxcursor1",
    "libxdamage1",
    "libxi6",
    "libxtst6",
    "libnss3",
    "libcups2",
    "libxss1",
    "libxrandr2",
    "libasound2",
    "libatk1.0-0",
    "libgtk-3-0",
    "x11-utils",
]

# Constants - Task Instance Installation Environment
SET_OPENSSL_TO_LEGACY = "NODE_OPTIONS=--openssl-legacy-provider"
SET_PUPPETEER_ENV_VAR = "PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable"
SET_PUPPETEER_PATH = "sed -i \"s|process.env.CHROME_BIN = require('puppeteer').executablePath();|process.env.CHROME_BIN = '/usr/bin/google-chrome-stable';|\" {}"
INSTALL_JULIA = [
    "wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz",
    "tar zxvf julia-1.9.3-linux-x86_64.tar.gz",
    "mv julia-1.9.3/ /opt/",
    "ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia",
]

SPECS_HIGHLIGHTJS = {k: {
    "install": [
        "npm install",
        "npm run build"
    ],
    "test_cmd": [
        "npm install",
        "npm run build",
        "npm run test",
    ],
    "docker_specs": {
        "node_version": "21.6.2"
    }
} for k in [
    '10.0', '10.2', '10.3', '10.4', '10.5', '10.6', '11.0', '11.2', '11.3',
    '11.4', '11.5', '11.6', '8.4', '8.9', '9.13', '9.15', '9.16', '9.17', '9.18',
    None
]}

SPECS_MAPBOX = {k: {
    "apt-pkgs": ["libglew-dev", "libxi-dev"],
    "install": ["npm install"],
    "test_cmd": "npm test",
    "docker_specs": {
        "node_version": "18.20.4"
    }
} for k in [
    '0.11', '0.12', '0.13', '0.14', '0.15', '0.18', '0.21', '0.22', '0.23',
    '0.25', '0.26', '0.28', '0.30', '0.31', '0.32', '0.33', '0.34', '0.36',
    '0.37', '0.38', '0.39', '0.40', '0.41', '0.42', '0.43', '0.44', '0.45',
    '0.46', '0.47', '0.49', '0.50', '0.51', '0.52', '0.53', '0.7', '0.8',
    '0.9', '1.6'
]}

SPECS_PLOTLYJS = {k: {
    "apt-pkgs": ["xvfb x11-xkb-utils",
                 "xfonts-100dpi", "xfonts-75dpi", "xfonts-scalable",
                 "xfonts-cyrillic x11-apps"],
    "install": [
        "su chromeuser -c 'npm install'",
        "su chromeuser -c 'npm run build'",
        "su chromeuser -c 'npm run pretest'",
    ],
    "test_cmd": (f'xvfb-run --server-args="-screen 0 1280x1024x24 -ac :99" '
                 'su chromeuser -c "./node_modules/.bin/karma start test/jasmine/karma.conf.js '
                 '--nowatch --verbose --capture-timeout 210000 --browser-disconnect-tolerance 3 '
                 '--browser-disconnect-timeout 210000 --browser-no-activity-timeout 210000"'),
    "docker_specs": {
        "node_version": "9.2.0",
        "run_args": {
            "cap_add": ["SYS_ADMIN"],
        },
    },
} for k in [
    "2.33", "2.32", "2.31", "2.30", "2.29", "2.28", "2.27", "2.26", "2.25",
    "2.24", "2.23", "2.22", "2.21", "2.20", "2.19", "2.18", "2.17", "2.16",
    "2.15", "2.14", "2.13", "2.12", "2.11", "2.10", "2.9", "2.8", "2.7",
    "2.6", "2.5", "2.4", "2.3", "2.2", "2.1", "2.0", "1.58", "1.57", "1.56",
    "1.55", "1.54", "1.53", "1.52", "1.51", "1.50", "1.49", "1.48", "1.47",
    "1.46", "1.45", "1.44", "1.43", "1.42", "1.41", "1.40", "1.39", "1.38",
    "1.37", "1.36", "1.35", "1.34", "1.33", "1.32", "1.31", "1.30", "1.29",
    "1.28", "1.27", "1.26", "1.25", "1.24", "1.23", "1.22", "1.21", "1.20",
    "1.19", "1.18", "1.17", "1.16", "1.15", "1.14", "1.13", "1.12", "1.11",
    "1.10", "1.9", "1.8", "1.7", "1.6", "1.5", "1.4", "1.3", "1.2", "1.1",
    "1.0",
]}
for k in [
    "2.33", "2.32", "2.31", "2.30", "2.29", "2.28", "2.27", "2.26", "2.25",
    "2.24", "2.23", "2.22", "2.21", "2.20", "2.19", "2.18", "2.17", "2.16",
    "2.15", "2.14", "2.13", "2.12", "2.11", "2.10", "2.9", "2.8", "2.7",
    "2.6", "2.5", "2.4", "2.3", "2.2", "2.1", "2.0"
]:
    SPECS_PLOTLYJS[k]["docker_specs"]["node_version"] = "16.20.2"

TEST_CMD_PRISM = "./node_modules/.bin/mocha tests/run.js --reporter json"
SPECS_PRISM = {
    **{k: {
        "install": ["npm ci", "npm run build"],
        "test_cmd": TEST_CMD_PRISM,
        "docker_specs": {
            "node_version": "12.22.12",
        }
    } for k in ['1.24', '1.25', '1.27', '1.28']},
    **{k: {
        "install": ["npm install", "npm run build"],
        "test_cmd": TEST_CMD_PRISM,
        "docker_specs": {
            "node_version": "10.24.1",
        }
    } for k in ['1.22', '1.23']},
    **{k: {
        "install": ["npm install"],
        "test_cmd": TEST_CMD_PRISM,
        "docker_specs": {
            "node_version": "8.17.0",
        }
    } for k in ['1.15', '1.16', '1.17', '1.19', '1.20']}
}
SPECS_PRISM['1.15']['docker_specs']['node_version'] = '4.9.1'
SPECS_PRISM['1.16']['docker_specs']['node_version'] = '21.6.2'
SPECS_PRISM['1.17']['docker_specs']['node_version'] = '21.6.2'

# Insomnia node versions:
# 1.0 = '10.15'
# 5.1 = '7.4.0'
# 5.2 = '7.4.0'
# 5.3 = '7.4.0'
# 5.11 = '8'
# 6.0 = '8'
# 6.2 = '10'
# 9.1 = '20.9.0'
# 9.3 = '20.9.0'
# 2020.1 = '10.15'
# 2020.2 = '10'
# 2020.4 = '12.18.3'
# 2020.5 = '12.18.3'
# 2021.1 = '12.18.3'
# 2021.2 = '12.18.3'
# 2021.4 = '12.18.3'
# 2021.5 = '12.18.3'
# 2021.6 = '12.18.3'
# 2022.4 = '16.13.2'
# 2022.7 = '16.17.0'
# 2023.1 = '16.17.0'
# 2023.2 = '16.17.0'
# 2023.5 = '18.15.0'
SPECS_INSOMNIA = {
    k: {
        "apt-pkgs": ["libfontconfig1-dev"],
        "install": ["npm install"],
        "test_cmd": "./node_modules/.bin/jest --json",
        # "test_cmd": PRINT_WORKSPACE_TESTS,
        "docker_specs": {},
    } for k in ['1.0', '5.1', '5.2', '5.3', '5.11', '6.0', '6.2', '9.1', '9.3',
                '2020.1', '2020.2', '2020.4', '2020.5', '2021.1', '2021.2',
                '2021.4', '2021.5', '2021.6', '2022.4', '2022.7', '2023.1',
                '2023.2', '2023.5']
}
for k in ['5.1', '5.2', '5.3']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '7.4.0'
for k in ['1.0', '2020.1']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '10.15.3'
for k in ['5.11', '6.0']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '8.17.0'
for k in ['6.2', '2020.2']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '10.24.1'  # '10.15.3'
for k in ['9.1', '9.3']:
    SPECS_INSOMNIA[k]["install"] = ["npm install"]
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '20.9.0'
    SPECS_INSOMNIA[k]['test_cmd'] = "npm run test -- --json"
for k in ['2020.4', '2020.5', '2021.1', '2021.2', '2021.4', '2021.5', '2021.6']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '12.18.3'
for k in ['2022.4']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '16.13.2'
for k in ['2022.7', '2023.1', '2023.2']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '16.17.0'
for k in ['2023.5']:
    SPECS_INSOMNIA[k]['docker_specs']['node_version'] = '18.15.0'


TEST_CMD_ESLINT = './node_modules/.bin/mocha --forbid-only --reporter min -t 10000 --no-colors "tests/{bin,conf,lib,tools}/**/*.js"'
SPECS_ESLINT = {
    **{k: {
        "install": ["npm install"],
        "test_cmd": TEST_CMD_ESLINT,
        "docker_specs": {
            "node_version": "10.24.1",
        }
    } for k in [
        '0.20', '0.24', '0.3', '0.5', '1.0', '1.1',
        '1.10', '1.5', '1.7', '1.9', '2.0', '2.10',
        '2.12', '2.13', '2.5', '3.1', '3.11',
        '3.16', '3.5', '4.1', '4.7', '4.9', '5.14',
        '6.6', '6.7', '7.18', '7.22', '8.1', '8.50'
    ]},
}
for v in ['0.20', '0.24', '0.3', '0.5', '1.0', '1.1', '1.10', '1.5',
    '1.7', '1.9', '2.0', '2.10', '2.12', '2.13', '2.5', '3.1', '3.11']:
    SPECS_ESLINT[v]["docker_specs"]["node_version"] = "4.9.1"
SPECS_ESLINT['8.1']["docker_specs"]["node_version"] = "21.6.2"
# eslint 8.50 needs re2 -> node-gyp 13, which requires node ^20.17 || >=22.9 (21.x unsupported)
SPECS_ESLINT['8.50']["docker_specs"]["node_version"] = "20.18.1"

TEST_CMD_BPMN_JS = "./node_modules/.bin/karma start test/config/karma.unit.js --no-colors"
SPECS_BPMN_JS = {
    **{k: {
        "install": ["npm install"],
        "test_cmd": [
            SET_PUPPETEER_PATH.format("test/config/karma.unit.js"),
            "sed -i \"/module.exports = function(karma) {/i \\\\\n"
            "var customLaunchers = { \\\\\n"
            "  ChromeNoSandbox: { \\\\\n"
            "    base: 'ChromeHeadless', \\\\\n"
            "    flags: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'] \\\\\n"
            "  } \\\\\n"
            "}; \\\\\n"
            "browsers = ['ChromeNoSandbox']; \\\\\n"
            "\" test/config/karma.unit.js",
            "sed -i \"/browsers,/a \\\\    customLaunchers,\" test/config/karma.unit.js",
            f'{SET_PUPPETEER_ENV_VAR} su chromeuser -c "{TEST_CMD_BPMN_JS}"',
        ],
        "docker_specs": {
            "node_version": "21.6.2",
        }
    } for k in [
        '0.27', '0.9', '2.3', '2.4', '2.5', '3.0', '3.3',
        '3.4', '4.0', '5.0', '5.1', '6.0', '6.3', '7.2', '7.3',
        '7.4', '8.3', '8.8', '8.9', '9.0', '9.1', '9.2', '9.3',
        '11.1', '11.3', '13.2', '14.0', '15.2'
    ]},
}
for v in ['6.0', '6.3', '7.2', '7.3', '7.4', '8.3', '8.8', '8.9', '9.0', '9.1', '9.2', '9.3']:
    SPECS_BPMN_JS[v]["docker_specs"]["node_version"] = "16.20.2"
# Set OpenSSL to legacy provider for certain versions
for v in ['3.0', '3.3', '3.4', '4.0', '5.0', '5.1']:
    SPECS_BPMN_JS[v]["test_cmd"][-1] = f'{SET_OPENSSL_TO_LEGACY} {SPECS_BPMN_JS[v]["test_cmd"][-1]}'

SPECS_OPENLAYERS = {
    **{k: {
        "apt-pkgs": XVFB_DEPS,
        "install": ["npm install"],
        "test_cmd": "npm run test",
        "docker_specs": {
            "node_version": "21.6.2",
            "run_args": {
                "cap_add": ["SYS_ADMIN"],
            }
        }
    } for k in [
        '3.0', '3.4', '3.5', '3.8', '3.10', '3.11', '3.12', '3.14', '3.16', '3.17', '3.18', '3.19', '3.20',
        '4.0', '4.3', '4.4', '4.5', '4.6',
        '5.1', '5.2', '5.3',
        '6.0', '6.1', '6.2', '6.3', '6.4', '6.5', '6.5.1', '6.6', '6.9', '6.10', '6.11', '6.12', '6.13', '6.14',
        '7.0', '7.1', '7.2', '7.3', '7.4', '7.5',
        '8.1', '9.0', '9.1'
    ]},
}
# Replace puppeteer executable path
# NOTE: 6.5.1 was an artificially introduced version for karma.config.[js -> cjs]
for v in [
    '6.5.1', '6.6', '6.9', '6.10', '6.11', '6.12', '6.13', '6.14',
    '7.0', '7.1', '7.2', '7.3', '7.5'
]:
    SPECS_OPENLAYERS[v]["install"].append(SET_PUPPETEER_PATH.format("test/browser/karma.config.cjs"))
for v in ['6.0', '6.1', '6.2', '6.3', '6.4', '6.5']:
    SPECS_OPENLAYERS[v]["install"].append(SET_PUPPETEER_PATH.format("test/karma.config.js"))

SPECS_EMOTION = {
    **{k: {
        "install": [
            "npm i -g yarn",
            "yarn",
            "yarn build"
        ],
        "test_cmd": "yarn test",
        "docker_specs": {
            "node_version": "16.20.2"
        }
    } for k in ['10.0']},
    **{k: {
        "install": ["npm install"],
        "test_cmd": "npm test",
        "docker_specs": {
            "node_version": "8.17.0"
        }
    } for k in ['2.0', '5.1', '5.2', '7.0']}
}

SPECS_GROMMET = {
    **{k: {
        "install": [
            "npm i -g yarn",
            "yarn install"
        ],
        "test_cmd": [
            "yarn install",
            "yarn test",
        ],
        "docker_specs": {
            "node_version": "21.6.2"
        }
    } for k in [
        '1.7', '2.0', '2.3', '2.6', '2.7',
        '2.11', '2.13', '2.14', '2.15', '2.16', '2.17', '2.18', '2.19',
        '2.20', '2.21', '2.22', '2.25', '2.26', '2.27', '2.29',
        '2.31', '2.33', '2.34'
    ]}
}

SPECS_PIXIJS = {
    **{k: {
        "apt-pkgs": XVFB_DEPS + ["libfontconfig1-dev"],
        "install": [
            "sed -i \"s/'ts-jest': {/'ts-jest': { isolatedModules: true,/\" jest.config.js",
            "sed -i \"/coverageDirectory: '<rootDir>\/dist\/coverage',/d\" jest.config.js",
            "sed -i 's/testTimeout: 10000/testTimeout: 10000,/' jest.config.js",
            "sed -i 's/};/    maxConcurrency: 3,\\n};/' jest.config.js",
            "sed -i 's/};/    maxWorkers: \"50%\",\\n};/' jest.config.js",
            "npm install",
            "cat jest.config.js",
        ],
        "test_cmd": ["npx jest --silent --no-colors"],
        "docker_specs": {
            "node_version": "18.20.4"
        }
    } for k in [
        '4.1', '4.3', '4.5', '4.8', '5.0', '6.0',
        '7.1', '7.2', '7.3', '8.0', '8.1', '8.2'
    ]}
}

SPECS_NEXT = {
    **{k: {
        "apt-pkgs": XVFB_DEPS,
        "install": ["su chromeuser -c 'npm install'"],
        "test_cmd": "npm run test",
        "docker_specs": {
            "node_version": "14.11.0",
            "run_args": {
                "cap_add": ["SYS_ADMIN"],
            },
        }
    } for k in [
        '1.11', '1.14', '1.15', '1.16', '1.17', '1.18', '1.19',
        '1.20', '1.21', '1.22', '1.23', '1.24', '1.25', '1.26', '1.27'
    ]}
}
SPECS_NEXT['1.27']['docker_specs']['node_version'] = '21.6.2'
for v in ['1.22', '1.23', '1.24', '1.25', '1.26', '1.27']:
    SPECS_NEXT[v]['install'].insert(0, SET_PUPPETEER_PATH.format("scripts/test/karma.js"))
for v in [
    '1.11', '1.14', '1.15', '1.16', '1.17', '1.18',
    '1.19', '1.20', '1.21', '1.22', '1.23', '1.24', '1.25'
]:
    SPECS_NEXT[v]['install'].extend([
        "npm install babel-preset-es2015",
        "npm install cheerio@1.0.0-rc.3",
        'npm i sass@1.36.0 --save-exact',
        'npm show cheerio',
    ])
for v in ['1.11', '1.14', '1.15', '1.16', '1.17', '1.18', '1.19', '1.20']:
    SPECS_NEXT[v]['apt-pkgs'].extend(["libsass-dev", "sassc"])
    SPECS_NEXT[v]['docker_specs']['node_version'] = '8.17.0'

SPECS_CYPRESS = {
    **{k: {
        "apt-pkgs": XVFB_DEPS,
        "install": ["npm i -g yarn", "yarn"],
        "test_cmd": "yarn test",
        "docker_specs": {
            "node_version": '16.20.2'
        }
    } for k in [
        '1.0', '1.1', '1.4',
        '10.0', '10.1', '10.10', '10.11', '10.2', '10.3', '10.5', '10.6', '10.7', '10.8', '10.9',
        '11.0', '11.1', '11.2',
        '12.0', '12.1', '12.2', '12.3', '12.4', '12.5', '12.6', '12.7', '12.8',
        '12.9', '12.10', '12.11', '12.12', '12.14', '12.17',
        '13.4', '13.6',
        '2.0', '2.1',
        '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8',
        '4.0', '4.1', '4.10', '4.11', '4.12', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.9',
        '5.0', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6',
        '6.0', '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.7', '6.8',
        '7.1', '7.2', '7.4', '7.5', '7.7',
        '8.0', '8.1', '8.2', '8.3', '8.4', '8.6',
        '9.0', '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '9.7'
    ]}
}
for v in ['12.9', '12.10', '12.11', '12.12', '12.14', '12.17', '13.4', '13.6']:
    SPECS_CYPRESS[v]['docker_specs']['node_version'] = '21.6.2'

# carbon a11y engine is fetched from a CDN at runtime; pin it so results are reproducible
CARBON_ACHECKER_ARCHIVE = "07Oct2020"
_PIN_CARBON_ACHECKER = (
    f"printf 'ruleArchive: {CARBON_ACHECKER_ARCHIVE}\\n' > /testbed/.achecker.yml; "
    f'echo "achecker archive pinned to {CARBON_ACHECKER_ARCHIVE}"'
)
SPECS_CARBON = {
    **{k: {
        "install": [
            "npm i -g yarn",
            "yarn install",
            "yarn build",
            _PIN_CARBON_ACHECKER,
        ],
        "test_cmd": "yarn test",
        "docker_specs": {
            "node_version": {
                "20.14": "20.14.0", "20.12": "20.12.2", "20.11": "20.11.1", "20.9": "20.9.0",
                "18.17": "18.17.1", "18.16": "18.16.1", "18.15": "18.15.0", "18.14": "18.14.2",
                "16.19": "16.19.1", "16.18": "16.18.1", "16.17": "16.17.1", "16.16": "16.16.0",
                "16.15": "16.15.1", "16.14": "16.14.2", "16.13": "16.13.2",
                "14.17": "14.17.6", "14": "14.17.6", "12": "12.22.12", "10": "10.24.1",
                "7.2": "8.17.0"
            }[k]
        }
    } for k in [
        '7.2', '10', '12', '14', '14.17',
        '16.13', '16.14', '16.15', '16.16', '16.17', '16.18', '16.19',
        '18.14', '18.15', '18.16', '18.17', '20.9', '20.11', '20.12', '20.14'
    ]}
}

SPECS_SCRATCH = {
    **{k: {
        "install": ["npm install"],
        "test_cmd": "./node_modules/.bin/jest --runInBand --no-colors",
        "docker_specs": {
            "node_version": {
                "1": "20.16.0",
                "2": "20.16.0",
                "3": "12.22.12",
                "4": "12.22.12",
                "5": "20.16.0",
                "8": "20.16.0",
            }[k]
        }
    } for k in ['1', '2', '3', '4', '5', '8']}
}
for v in ['1', '2', '3', '4']:
    SPECS_SCRATCH[v]['install'].extend([
        "npm install cheerio@1.0.0-rc.3",
        "npm show cheerio"
    ])

SPECS_LIGHTHOUSE = {
    **{k: {
        "install": [
            "npm i -g yarn",
            "yarn",
            "yarn build-all"
        ],
        "test_cmd": "yarn mocha",
        "docker_specs": {
            "node_version": "16.20.2",
        }
    } for k in [
        '1.0', '1.1', '1.2', '1.4', '1.5', '1.6',
        '2.0', '2.1', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9',
        '3.0', '3.1', '3.2',
        '4.0', '4.1',
        '5.0', '5.1', '5.2', '5.6',
        '6.0', '6.1', '6.3', '6.4', '6.5',
        '7.0',
        '8.0', '8.2', '8.3', '8.6',
        '9.5',
        '10.0', '10.2'
    ]}
}
for v in ['2.0', '2.1', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9']:
    SPECS_LIGHTHOUSE[v]["install"] = [
        "npm i -g yarn",
        "yarn",
        "yarn install-all",
        "yarn build-all",
    ]
for v in ['1.0', '1.1', '1.2', '1.4', '1.5', '1.6']:
    SPECS_LIGHTHOUSE[v]["docker_specs"]["node_version"] = "8.17.0"
    SPECS_LIGHTHOUSE[v]["install"] = [
        "npm install",
        "npm run install-all",
    ]

SPECS_PRETTIER = {
    **{k: {
        "install": [
            "npm i -g yarn",
            "yarn",
        ],
        "test_cmd": "yarn test",
        "docker_specs": {
            "node_version": "20.16.0",
        }
    } for k in [
        '0.0', '0.11', '0.13', '0.15', '0.16', '0.20', '1.11',
        '1.4', '1.5', '1.6', '1.7', '1.8', '2.1', '2.2', '2.3',
        '2.6', '2.9', '3.0', '3.3', '3.4'
    ]}
}

PIP_INSTALLS_QUARTOCLI = [
    "pip3 install --user pipenv",
    "pip3 install nbformat",
    "pip3 install nbclient",
    "pip3 install pandocfilters",
    "pip3 install shiny",
    "pip3 install pyyaml",
    "pip3 install setuptools",
    "pip3 install numpy",
    "pip3 install seaborn",
    "pip3 install matplotlib",
    "pip3 install bokeh",
    "pip3 install bokeh_sampledata",
    "pip3 install ipyleaflet",
    "pip3 install pandas",
    "pip3 install itables",
    "pip3 install pexpect",
    "pip3 install ptyprocess",
    "pip3 install appnope",
    "pip3 install ipykernel",
]
# quarto: TeX Live 2026 loops forever on tests/docs/page-layout/tufte-pdf.qmd; 2024 renders it in 9s
TEXLIVE_2024_REPO = (
    "https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2024/tlnet-final"
)
PIN_TINYTEX_2024 = [
    "rm -rf /root/.TinyTeX /opt/TinyTeX",
    "wget -qO /tmp/install-tinytex.sh https://tinytex.yihui.org/install-bin-unix.sh",
    "TINYTEX_VERSION=2024.12 sh /tmp/install-tinytex.sh",
    f'"$(echo /root/.TinyTeX/bin/*)"/tlmgr option repository {TEXLIVE_2024_REPO}',
    # babel-french unpacked directly: `tlmgr update --self` against the frozen repo breaks the tree
    f"curl -sSL {TEXLIVE_2024_REPO}/archive/babel-french.tar.xz "
    "-o /tmp/babel-french.tar.xz || true",
    "tar -xJf /tmp/babel-french.tar.xz -C /root/.TinyTeX/texmf-dist "
    "tex/generic/babel-french || true",
    '"$(echo /root/.TinyTeX/bin/*)"/mktexlsr || true',
    'tex_ver="$("$(echo /root/.TinyTeX/bin/*)"/xelatex --version)"; '
    'case "$tex_ver" in *"TeX Live 2024"*) echo "TinyTeX pinned to TL2024 OK";; '
    '*) echo "TinyTeX pin FAILED, got: $tex_ver"; exit 1;; esac',
]
SPECS_QUARTOCLI = {
    None : {
        "apt-pkgs": ["libffi-dev", "zip", "unzip", "python3", "python3-pip", "python3.10-distutils", "r-base-core",
                     "poppler-utils", "libxml2-utils"],
        "install": INSTALL_JULIA + ["ls .",
                    "[ -f configure.sh ] || ./configure-linux.sh",
                    "[ -f configure-linux.sh ] || ./configure.sh",
                    "cd tests", "./configure-test-env.sh || true", "cd ..",
                    ] + PIN_TINYTEX_2024 + PIP_INSTALLS_QUARTOCLI,
        "test_cmd": [ # test generates files that add future test cases -- run tests fairly
            "cp -r tests/ tests_tmp/", 
            "cd tests", 
            "QUARTO_TESTS_NO_CONFIG=\"true\" ./run-tests.sh",
            "cd ..",
            "rm -rf tests/", 
            "mv tests_tmp/ tests/", 
        ],
        "docker_specs": {
            "run_args": {
                "cap_add": ["SYS_ADMIN"],
            }
        }
    } 
}
SPECS_CALYPSO = {
    **{
        k: {
            "apt-pkgs": ["libsass-dev", "sassc"],
            "install": ["npm install --unsafe-perm"],
            "test_cmd": "npm run test-client",
            "docker_specs": {
                "node_version": k,
            },
        }
        for k in [
            "0.8",
            "4.2.3",
            "4.3.0",
            "5.10.1",
            "5.11.1",
            "6.1.0",
            "6.7.0",
            "6.9.0",
            "6.9.1",
            "6.9.4",
            "6.10.0",
            "6.10.2",
            "6.10.3",
            "6.11.1",
            "6.11.2",
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
            "10.10.0",
            "10.12.0",
            "10.13.0",
            "10.14.0",
            "10.15.2",
            "10.16.3",
        ]
    }
}

TEST_CHART_JS_TEMPLATE = "./node_modules/.bin/cross-env NODE_ENV=test ./node_modules/.bin/karma start {} --single-run --coverage --grep --auto-watch false"
SPECS_CHART_JS = {
    **{
        k: {
            "install": [
                "pnpm install",
                "pnpm run build",
            ],
            "test_cmd": [
                "pnpm install",
                "pnpm run build",
                f'{TEST_XVFB_PREFIX} su chromeuser -c "{TEST_CHART_JS_TEMPLATE.format("./karma.conf.cjs")}"',
            ],
            "docker_specs": {
                "node_version": "21.6.2",
                "pnpm_version": "7.9.0",
                "run_args": {
                    "cap_add": ["SYS_ADMIN"],
                },
            },
        }
        for k in ["4.0", "4.1", "4.2", "4.3", "4.4"]
    },
    **{
        k: {
            "install": ["npm install"],
            "test_cmd": [
                "npm install",
                "npm run build",
                f'{TEST_XVFB_PREFIX} su chromeuser -c "{TEST_CHART_JS_TEMPLATE.format("./karma.conf.js")}"',
            ],
            "docker_specs": {
                "node_version": "21.6.2",
                "run_args": {
                    "cap_add": ["SYS_ADMIN"],
                },
            },
        }
        for k in ["3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8"]
    },
    **{
        k: {
            "install": ["npm install", "npm install -g gulp-cli"],
            "test_cmd": [
                "npm install",
                "gulp build",
                TEST_XVFB_PREFIX + ' su chromeuser -c "gulp test"',
            ],
            "docker_specs": {
                "node_version": "21.6.2",
                "run_args": {
                    "cap_add": ["SYS_ADMIN"],
                },
            },
        }
        for k in ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"]
    },
}
for v in SPECS_CHART_JS.keys():
    SPECS_CHART_JS[v]["apt-pkgs"] = XVFB_DEPS

SPECS_MARKED = {
    **{
        k: {
            "install": ["npm install"],
            "test_cmd": "./node_modules/.bin/jasmine --no-color --config=jasmine.json",
            "docker_specs": {
                "node_version": "12.22.12",
            },
        }
        for k in [
            "0.3",
            "0.5",
            "0.6",
            "0.7",
            "1.0",
            "1.1",
            "1.2",
            "2.0",
            "3.9",
            "4.0",
            "4.1",
            "5.0",
        ]
    }
}
for v in ["4.0", "4.1", "5.0"]:
    SPECS_MARKED[v]["docker_specs"]["node_version"] = "20.16.0"

SPECS_P5_JS = {
    **{
        k: {
            "apt-pkgs": X11_DEPS,
            "install": [
                "npm install",
                "PUPPETEER_SKIP_CHROMIUM_DOWNLOAD='' node node_modules/puppeteer/install.js",
                "./node_modules/.bin/grunt yui",
            ],
            "test_cmd": (
                """sed -i 's/concurrency:[[:space:]]*[0-9][0-9]*/concurrency: 1/g' Gruntfile.js\n"""
                "stdbuf -o 1M ./node_modules/.bin/grunt test --quiet --force"
            ),
            "docker_specs": {
                "node_version": "14.17.3",
            },
        }
        for k in [
            "0.10",
            "0.2",
            "0.4",
            "0.5",
            "0.6",
            "0.7",
            "0.8",
            "0.9",
            "1.0",
            "1.1",
            "1.2",
            "1.3",
            "1.4",
            "1.5",
            "1.6",
            "1.7",
            "1.8",
            "1.9",
        ]
    },
}
for k in [
    "0.4",
    "0.5",
    "0.6",
]:
    SPECS_P5_JS[k]["install"] = [
        "npm install",
        "./node_modules/.bin/grunt yui",
    ]

SPECS_REACT_PDF = {
    **{
        k: {
            "apt-pkgs": [
                "pkg-config",
                "build-essential",
                "libpixman-1-0",
                "libpixman-1-dev",
                "libcairo2-dev",
                "libpango1.0-dev",
                "libjpeg-dev",
                "libgif-dev",
                "librsvg2-dev",
            ]
            + X11_DEPS,
            "install": ["npm i -g yarn", "yarn install"],
            "test_cmd": 'NODE_OPTIONS="--experimental-vm-modules" ./node_modules/.bin/jest --no-color',
            "docker_specs": {"node_version": "18.20.4"},
        }
        for k in ["1.0", "1.1", "1.2", "2.0"]
    }
}
for v in ["1.0", "1.1", "1.2"]:
    SPECS_REACT_PDF[v]["docker_specs"]["node_version"] = "8.17.0"
    SPECS_REACT_PDF[v]["install"] = ["npm install", "npm install cheerio@1.0.0-rc.3"]
    SPECS_REACT_PDF[v]["test_cmd"] = "./node_modules/.bin/jest --no-color"


JEST_JSON_JQ_TRANSFORM = """jq -r '.testResults[].assertionResults[] | "[" + (.status | ascii_upcase) + "] " + ((.ancestorTitles | join(" > ")) + (if .ancestorTitles | length > 0 then " > " else "" end) + .title)'"""

SPECS_BABEL = {
    "14532": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": ["yarn jest babel-generator --verbose"],
        "install": ["make bootstrap"],
        "build": ["make build"],
    },
    "13928": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": ['yarn jest babel-parser -t "arrow" --verbose'],
        "install": ["make bootstrap"],
        "build": ["make build"],
    },
    "15649": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": ["yarn jest packages/babel-traverse/test/scope.js --verbose"],
        "install": ["make bootstrap"],
        "build": ["make build"],
    },
    "15445": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": [
            'yarn jest packages/babel-generator/test/index.js -t "generation " --verbose'
        ],
        "install": ["make bootstrap"],
        "build": ["make build"],
    },
    "16130": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": ["yarn jest babel-helpers --verbose"],
        "install": ["make bootstrap"],
        "build": ["make build"],
    },
}

SPECS_VUEJS = {
    "11899": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": [
            "pnpm run test packages/compiler-sfc/__tests__/compileStyle.spec.ts --no-watch --reporter=verbose"
        ],
        "install": ["pnpm i"],
        "build": ["pnpm run build compiler-sfc"],
    },
    "11870": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": [
            "pnpm run test packages/runtime-core/__tests__/helpers/renderList.spec.ts --no-watch --reporter=verbose"
        ],
        "install": ["pnpm i"],
    },
    "11739": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": [
            'pnpm run test packages/runtime-core/__tests__/hydration.spec.ts --no-watch --reporter=verbose -t "mismatch handling"'
        ],
        "install": ["pnpm i"],
    },
    "11915": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": [
            'pnpm run test packages/compiler-core/__tests__/parse.spec.ts --no-watch --reporter=verbose -t "Element"'
        ],
        "install": ["pnpm i"],
    },
    "11589": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "test_cmd": [
            "pnpm run test packages/runtime-core/__tests__/apiWatch.spec.ts --no-watch --reporter=verbose"
        ],
        "install": ["pnpm i"],
    },
}

SPECS_DOCUSAURUS = {
    "10309": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["yarn install"],
        "test_cmd": [
            "yarn test packages/docusaurus-plugin-content-docs/src/client/__tests__/docsClientUtils.test.ts --verbose"
        ],
    },
    "10130": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["yarn install"],
        "test_cmd": [
            "yarn test packages/docusaurus/src/server/__tests__/brokenLinks.test.ts --verbose"
        ],
    },
    "9897": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["yarn install"],
        "test_cmd": [
            "yarn test packages/docusaurus-utils/src/__tests__/markdownUtils.test.ts --verbose"
        ],
    },
    "9183": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["yarn install"],
        "test_cmd": [
            "yarn test packages/docusaurus-theme-classic/src/__tests__/options.test.ts --verbose"
        ],
    },
    "8927": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["yarn install"],
        "test_cmd": [
            "yarn test packages/docusaurus-utils/src/__tests__/markdownLinks.test.ts --verbose"
        ],
    },
}

SPECS_IMMUTABLEJS = {
    "2006": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "build": ["npm run build"],
        "test_cmd": ["npx jest __tests__/Range.ts --verbose"],
    },
    "2005": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "build": ["npm run build"],
        "test_cmd": [
            f"npx jest __tests__/OrderedMap.ts __tests__/OrderedSet.ts --silent --json | {JEST_JSON_JQ_TRANSFORM}"
        ],
    },
}

SPECS_THREEJS = {
    "27395": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        # --ignore-scripts is used to avoid downloading chrome for puppeteer
        "install": ["npm install --ignore-scripts"],
        "test_cmd": ["npx qunit test/unit/src/math/Sphere.tests.js"],
    },
    "26589": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install --ignore-scripts"],
        "test_cmd": [
            "npx qunit test/unit/src/objects/Line.tests.js test/unit/src/objects/Mesh.tests.js test/unit/src/objects/Points.tests.js"
        ],
    },
    "25687": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install --ignore-scripts"],
        "test_cmd": [
            'npx qunit test/unit/src/core/Object3D.tests.js -f "/json|clone|copy/i"'
        ],
    },
}

SPECS_PREACT = {
    "4152": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/components.test.js"'
        ],
    },
    "4316": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/events.test.js"'
        ],
    },
    "4245": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="hooks/test/browser/useId.test.js"'
        ],
    },
    "4182": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="hooks/test/browser/errorBoundary.test.js"'
        ],
    },
    "4436": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/refs.test.js"'
        ],
    },
    "3763": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/lifecycles/componentDidMount.test.js"'
        ],
    },
    "3739": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="hooks/test/browser/useState.test.js"',
        ],
    },
    "3689": {
        "docker_specs": {"node_version": "18", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="hooks/test/browser/errorBoundary.test.js"',
        ],
    },
    "3567": {
        "docker_specs": {"node_version": "18", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="hooks/test/browser/useEffect.test.js"',
        ],
    },
    "3562": {
        "docker_specs": {"node_version": "18", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="compat/test/browser/render.test.js"',
        ],
    },
    "3454": {
        "docker_specs": {"node_version": "18", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/svg.test.js"',
        ],
    },
    "3345": {
        "docker_specs": {"node_version": "18", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="hooks/test/browser/useEffect.test.js"',
        ],
    },
    "3062": {
        "docker_specs": {"node_version": "16", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/render.test.js"',
        ],
    },
    "3010": {
        "docker_specs": {"node_version": "16", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/render.test.js"',
        ],
    },
    "2927": {
        "docker_specs": {"node_version": "16", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/render.test.js"',
        ],
    },
    "2896": {
        "docker_specs": {"node_version": "16", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="compat/test/browser/memo.test.js"',
        ],
    },
    "2757": {
        "docker_specs": {"node_version": "16", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": [
            'COVERAGE=false BABEL_NO_MODULES=true npx karma start karma.conf.js --single-run --grep="test/browser/render.test.js"',
        ],
    },
}

SPECS_AXIOS = {
    "5892": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": ["npx mocha test/unit/adapters/http.js -R tap -g 'compression'"],
    },
    "5316": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        # Patch involves adding a new dependency, so we need to re-install
        "build": ["npm install"],
        "test_cmd": ["npx mocha test/unit/adapters/http.js -R tap -g 'FormData'"],
    },
    "4738": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        # Tests get stuck for some reason, so we run them with a timeout
        "test_cmd": [
            "timeout 10s npx mocha -R tap test/unit/adapters/http.js -g 'timeout'"
        ],
    },
    "4731": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": ["npx mocha -R tap test/unit/adapters/http.js -g 'body length'"],
    },
    "6539": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": ["npx mocha -R tap test/unit/regression/SNYK-JS-AXIOS-7361793.js"],
    },
    "5085": {
        "docker_specs": {"node_version": "20", "_variant": "js_2"},
        "install": ["npm install"],
        "test_cmd": ["npx mocha -R tap test/unit/regression/bugs.js"],
    },
}


MAP_REPO_VERSION_TO_SPECS_JS = {
    "Automattic/wp-calypso": SPECS_CALYPSO,
    "chartjs/Chart.js": SPECS_CHART_JS,
    "markedjs/marked": SPECS_MARKED,
    "processing/p5.js": SPECS_P5_JS,
    "diegomura/react-pdf": SPECS_REACT_PDF,
    "babel/babel": SPECS_BABEL,
    "vuejs/core": SPECS_VUEJS,
    "facebook/docusaurus": SPECS_DOCUSAURUS,
    "immutable-js/immutable-js": SPECS_IMMUTABLEJS,
    "mrdoob/three.js": SPECS_THREEJS,
    "preactjs/preact": SPECS_PREACT,
    "axios/axios": SPECS_AXIOS,
    "alibaba-fusion/next": SPECS_NEXT,
    "bpmn-io/bpmn-js": SPECS_BPMN_JS,
    "carbon-design-system/carbon": SPECS_CARBON,
    "cypress-io/cypress": SPECS_CYPRESS,
    "emotion-js/emotion": SPECS_EMOTION,
    "eslint/eslint": SPECS_ESLINT,
    "GoogleChrome/lighthouse": SPECS_LIGHTHOUSE,
    "grommet/grommet": SPECS_GROMMET,
    "highlightjs/highlight.js": SPECS_HIGHLIGHTJS,
    "Kong/insomnia": SPECS_INSOMNIA,
    "mapbox/mapbox-gl-js": SPECS_MAPBOX,
    "openlayers/openlayers": SPECS_OPENLAYERS,
    "pixijs/pixijs": SPECS_PIXIJS,
    "plotly/plotly.js": SPECS_PLOTLYJS,
    "prettier/prettier": SPECS_PRETTIER,
    "PrismJS/prism": SPECS_PRISM,
    "quarto-dev/quarto-cli": SPECS_QUARTOCLI,
    "scratchfoundation/scratch-gui": SPECS_SCRATCH,
}

# these repos use system chrome, so puppeteer's ~150MB download is waste and stalls builds
_PUPPETEER_SKIP_DOWNLOAD = (
    "export PUPPETEER_SKIP_DOWNLOAD=true PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true"
)
for _repo in (
    "openlayers/openlayers",
    "bpmn-io/bpmn-js",
    "alibaba-fusion/next",
    "GoogleChrome/lighthouse",
):
    for _spec in MAP_REPO_VERSION_TO_SPECS_JS[_repo].values():
        if "install" in _spec and _PUPPETEER_SKIP_DOWNLOAD not in _spec["install"]:
            _spec["install"] = [_PUPPETEER_SKIP_DOWNLOAD] + list(_spec["install"])

# Constants - Repository Specific Installation Instructions
MAP_REPO_TO_INSTALL_JS = {}
