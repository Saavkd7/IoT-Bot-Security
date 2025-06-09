#!/bin/bash
export USER=kali
export HOME=/home/kali

# Start VNC as kali user
su - kali -c "vncserver :1 -geometry 1280x720 -depth 24"
tail -F /home/kali/.vnc/*.log

