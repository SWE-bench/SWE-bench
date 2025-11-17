_DOCKERFILE_BASE_AGNOSTIC = r"""FROM --platform={platform} ubuntu:{ubuntu_version}

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y \
    bash \
    build-essential \
    ca-certificates \
    curl \
    git \
    jq \
    liblzma-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    make \
    tar \
    tzdata \
    unzip \
    wget \
    xz-utils \
    zip \
    zlib1g-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /testbed/
"""

_DOCKERFILE_ENV_AGNOSTIC = r"""FROM --platform={platform} {base_image_key}

WORKDIR /testbed/
"""

_DOCKERFILE_INSTANCE_AGNOSTIC = r"""FROM --platform={platform} {env_image_name}

COPY ./setup_repo.sh /root/
RUN /bin/bash /root/setup_repo.sh

WORKDIR /testbed/
"""
