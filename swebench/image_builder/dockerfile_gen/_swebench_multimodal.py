_DOCKERFILE_BASE_JS = r"""
FROM --platform=linux/amd64 ubuntu:jammy

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/UTC

RUN rm /bin/sh && ln -s /bin/bash /bin/sh
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libssl-dev \
    software-properties-common \
    wget \
    gnupg \
    jq \
    ca-certificates \
    dbus \
    ffmpeg \
    imagemagick \
    && apt-get -y autoclean \
    && rm -rf /var/lib/apt/lists/*
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg \
        fonts-khmeros fonts-kacst fonts-freefont-ttf libxss1 dbus dbus-x11 \
        --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV NVM_DIR /usr/local/nvm

RUN mkdir -p $NVM_DIR
RUN curl --silent -o- https://raw.githubusercontent.com/creationix/nvm/v0.39.3/install.sh | bash
RUN apt-get update && apt-get install -y \
    procps \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdrm2 \
    libgbm1 libgconf-2-4 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 \
    libnss3 libpango-1.0-0 libpangocairo-1.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 libxss1 libxshmfence1 libglu1 \
    && apt-get -y autoclean \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN /usr/bin/google-chrome
RUN echo "CHROME_BIN=$CHROME_BIN" >> /etc/environment
RUN mkdir -p /run/dbus

ENV DBUS_SESSION_BUS_ADDRESS="unix:path=/run/dbus/system_bus_socket"

RUN dbus-daemon --system --fork

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV OPENSSL_CONF /etc/ssl

RUN useradd -m chromeuser

USER chromeuser

WORKDIR /home/chromeuser

USER root
"""

from swebench.data_specs.javascript import MAP_REPO_VERSION_TO_SPECS_JS
from swebench.image_builder.docker_utils import (
    make_heredoc_run_command,
    git_clone_timesafe,
)
from swebench.image_builder.constants import (
    CONTAINER_WORKDIR,
)


def make_env_script_list(instance, specs):
    """
    Set up the JavaScript/Node.js environment with required dependencies.
    """
    docker_specs = specs.get("docker_specs", {})
    node_version = docker_specs.get("node_version", "18.17.1")
    pnpm_version = docker_specs.get("pnpm_version", None)
    python_version = docker_specs.get("python_version", "3.9")
    commands = []
    if "apt-pkgs" in specs:
        apt_packages = " ".join(specs["apt-pkgs"])
        commands.extend(
            [
                "apt-get update",
                f"apt-get install -y {apt_packages}",
                "rm -rf /var/lib/apt/lists/*",
            ]
        )
    commands.extend(
        [
            f"export NODE_VERSION={node_version}",
            "source $NVM_DIR/nvm.sh",
            "nvm install $NODE_VERSION",
            "nvm alias default $NODE_VERSION",
            "nvm use default",
        ]
    )
    commands.extend(
        [
            "add-apt-repository ppa:deadsnakes/ppa",
            "apt-get update",
            f"apt-get install -y python{python_version}",
            f"ln -sf /usr/bin/python{python_version} /usr/bin/python",
        ]
    )
    commands.append("apt-get install -y python2")
    commands.extend(
        [
            f'echo "export NODE_PATH=$NVM_DIR/v{node_version}/lib/node_modules" >> /etc/environment',
            f'echo "export PATH=$NVM_DIR/versions/node/v{node_version}/bin:$PATH" >> /etc/environment',
        ]
    )
    if pnpm_version:
        commands.extend(
            [
                f"export PNPM_VERSION={pnpm_version}",
                "export PNPM_HOME=/usr/local/pnpm",
                "mkdir -p $PNPM_HOME",
                'wget -qO $PNPM_HOME/pnpm "https://github.com/pnpm/pnpm/releases/download/v$PNPM_VERSION/pnpm-linux-x64"',
                "chmod +x $PNPM_HOME/pnpm",
                "ln -s $PNPM_HOME/pnpm /usr/local/bin/pnpm",
                'echo "export PNPM_HOME=$PNPM_HOME" >> /etc/profile',
                'echo "export PATH=$PNPM_HOME:$PATH" >> /etc/profile',
            ]
        )
    commands.extend(
        [
            "source $NVM_DIR/nvm.sh && node -v",
            "source $NVM_DIR/nvm.sh && npm -v",
            "python -V",
            "python2 -V",
        ]
    )
    if pnpm_version:
        commands.append("pnpm -v")

    return make_heredoc_run_command(commands)


def make_repo_script_list(specs, repo, base_commit):
    """
    Clone the repository, install dependencies, and run any build commands.
    """
    commands = [
        *git_clone_timesafe(repo, base_commit, CONTAINER_WORKDIR),
        f"cd {CONTAINER_WORKDIR}",
        "git clean -fdxq",
    ]
    commands.append("source $NVM_DIR/nvm.sh")
    if "install" in specs:
        install_commands = specs["install"]
        if isinstance(install_commands, str):
            install_commands = [install_commands]
        commands.extend(install_commands)
    if "build" in specs:
        build_commands = specs["build"]
        if isinstance(build_commands, str):
            build_commands = [build_commands]
        commands.extend(build_commands)
    return make_heredoc_run_command(commands)


def _get_dockerfile(instance) -> str:
    """
    Generate a monolithic Dockerfile for SWE-bench Multimodal instances.
    This combines the base image, environment setup, and repository setup into a single Dockerfile.
    """
    repo = instance["repo"]
    version = instance.get("version")
    base_commit = instance["base_commit"]
    specs = MAP_REPO_VERSION_TO_SPECS_JS[repo][version]
    dockerfile = _DOCKERFILE_BASE_JS
    docker_specs = specs.get("docker_specs", {})
    node_version = docker_specs.get("node_version", "18.17.1")
    pnpm_version = docker_specs.get("pnpm_version", None)
    dockerfile += f"\nENV NODE_VERSION {node_version}\n"
    dockerfile += "ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules\n"
    dockerfile += "ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH\n"
    if pnpm_version:
        dockerfile += f"ENV PNPM_VERSION {pnpm_version}\n"
        dockerfile += "ENV PNPM_HOME /usr/local/pnpm\n"
        dockerfile += "ENV PATH $PNPM_HOME:$PATH\n"
    env_script = make_env_script_list(instance, specs)
    if env_script:
        dockerfile += f"\n{env_script}\n"
    repo_script = make_repo_script_list(specs, repo, base_commit)
    if repo_script:
        dockerfile += f"\n{repo_script}\n"
    dockerfile += f"\nWORKDIR {CONTAINER_WORKDIR}\n"

    return dockerfile
