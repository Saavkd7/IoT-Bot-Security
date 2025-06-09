FROM kalilinux/kali-rolling

# Non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Update Kali and install core tools
RUN apt update && apt install -y \
    python3 \
    python3-pip \
    net-tools \
    iputils-ping \
    curl \
    nano \
    xfce4 xfce4-goodies tightvncserver dbus-x11 \
    && apt clean

# Install Python MQTT/sniffing tools
RUN pip3 install --break-system-packages paho-mqtt scapy


# Create VNC password and configure GUI user
RUN useradd -m kali && \
    echo "kali:kali" | chpasswd && \
    mkdir -p /home/kali/.vnc && \
    echo "kali" | vncpasswd -f > /home/kali/.vnc/passwd && \
    chmod 600 /home/kali/.vnc/passwd && \
    chown -R kali:kali /home/kali

# Copy startup script
COPY start-vnc.sh /start-vnc.sh
RUN chmod +x /start-vnc.sh

# Set default user
USER root
WORKDIR /home/kali

# Expose VNC port
EXPOSE 5901

# Start VNC when container runs
CMD ["/start-vnc.sh"]

