FROM ubuntu:22.04

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    xterm \
    fluxbox \
    wget \
    gpg \
    apt-transport-https \
    git \
    sudo \
    xclip \
    xdotool \
    bash \
    --no-install-recommends

# Add Microsoft GPG key and repository
RUN apt-get install -y ca-certificates wget gpg
RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
RUN install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
RUN echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | tee /etc/apt/sources.list.d/vscode.list > /dev/null
RUN rm -f packages.microsoft.gpg

RUN apt install -y apt-transport-https
RUN apt update -y
RUN apt install -y code

# VNC port
EXPOSE 5901

RUN useradd -m vscode && \
    echo "vscode:password" | chpasswd && \
    adduser vscode sudo && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
RUN chsh -s /bin/bash vscode

# VSCode extensions
COPY .vscode /home/vscode/.vscode
RUN chown -R vscode:vscode /home/vscode/.vscode

# VSCode settings
COPY .config /home/vscode/.config
RUN chown -R vscode:vscode /home/vscode/.config

COPY start.sh /start.sh
RUN chmod +x /start.sh
RUN chown vscode:vscode /start.sh

USER vscode
RUN mkdir -p /home/vscode/.vnc
RUN x11vnc -storepasswd password /home/vscode/.vnc/passwd
WORKDIR /home/vscode

CMD ["/start.sh"]
