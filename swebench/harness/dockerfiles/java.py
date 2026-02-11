_DOCKERFILE_BASE_JAVA = r"""
FROM --platform={platform} maven:3.9-eclipse-temurin-{java_version}

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt update && apt install -y \
wget \
git \
build-essential \
ant \
unzip \
&& rm -rf /var/lib/apt/lists/*

{mvnd_install}

RUN adduser --disabled-password --gecos 'dog' nonroot
"""

# mvnd install block for x86_64 (native binary available)
_MVND_INSTALL_AMD64 = r"""RUN curl -fsSL -o mvnd.zip https://downloads.apache.org/maven/mvnd/1.0.2/maven-mvnd-1.0.2-linux-amd64.zip && \
    unzip mvnd.zip -d /tmp && \
    mv /tmp/maven-mvnd-1.0.2-linux-amd64 /usr/local/mvnd && \
    rm mvnd.zip && \
    rm -rf /tmp/maven-mvnd-1.0.2-linux-amd64

ENV MVND_HOME=/usr/local/mvnd
ENV PATH=$MVND_HOME/bin:$PATH"""

# mvnd install block for ARM64 (no native binary; symlink mvn as mvnd)
_MVND_INSTALL_ARM64 = r"""# mvnd has no Linux ARM64 release; use mvn (pure Java, already installed)
# Create mvnd symlink so test commands that invoke 'mvnd' resolve to 'mvn'
RUN mkdir -p /usr/local/mvnd/bin && \
    ln -s "$(which mvn)" /usr/local/mvnd/bin/mvnd

ENV MVND_HOME=/usr/local/mvnd
ENV PATH=$MVND_HOME/bin:$PATH"""

_DOCKERFILE_INSTANCE_JAVA = r"""FROM --platform={platform} {env_image_name}

COPY ./setup_repo.sh /root/
RUN /bin/bash /root/setup_repo.sh

WORKDIR /testbed/
"""
