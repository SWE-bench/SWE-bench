#!/bin/bash

# or can't edit files
sudo chown -R vscode:vscode /home/vscode/repo

# headless Xorg
export DISPLAY=:0
sudo Xvfb :0 -screen 0 1024x768x16 &
sleep 1


# window manager
fluxbox &
sleep 1

# vscode
code --no-sandbox /home/vscode/repo
sleep 5
while IFS=',' read -ra file; do
    code --no-sandbox /home/vscode/repo/$file
done <<< "$FILES"

# vnc server
sudo x11vnc -display :0 -usepw -forever -shared -rfbauth /home/vscode/.vnc/passwd -rfbport 5901 &

sleep 5

xdotool key ctrl+shift+p
xdotool type "Cline: Jump to Chat Input"
xdotool key Return

sleep 5

echo "$PROMPT" | xclip -selection clipboard
xdotool key ctrl+v
xdotool key Return

# keep the container running until file /tmp/request_finished is created
while [ ! -f "/tmp/request_finished" ]; do :; done

cd /home/vscode/repo
git diff --patch HEAD > /home/vscode/repo/diff.patch
chmod a+r /home/vscode/repo/diff.patch
