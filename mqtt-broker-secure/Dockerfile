FROM eclipse-mosquitto:2.0

# ─── Root access for setup ───
USER root

# Remove default config
RUN rm -f /mosquitto/config/mosquitto.conf

# Install extra Alpine tools
RUN apk update && apk add --no-cache \
    mosquitto-clients \
    nano \
    curl \
    tcpdump \
    iputils \
    iproute2 \
    net-tools \
    wget \
    bind-tools \
    vim \
    netcat-openbsd \
    busybox-extras \
    openssl \
    procps \
    python3 \
    py3-pip \
    git \
    gcc \
    musl-dev \
    libffi-dev \
    shadow

# ✅ Fix: Give mosquitto user a shell & home directory to avoid “This account is not available”
RUN usermod -d /home/mosquitto -s /bin/sh mosquitto && \
    mkdir -p /home/mosquitto && \
    chown mosquitto:mosquitto /home/mosquitto

# Copy configuration, certificates, and scripts
COPY config/                /mosquitto/config/
COPY certs/                 /mosquitto/certs/
COPY gen_passwordfile.sh   /gen_passwordfile.sh
COPY entrypoint.sh         /entrypoint.sh

# Set executable permissions
RUN chmod +x /gen_passwordfile.sh /entrypoint.sh

# Set secure permissions on certs and config
RUN chown -R mosquitto:mosquitto /mosquitto/certs && \
    chmod 644 /mosquitto/certs/*.crt && \
    chmod 640 /mosquitto/certs/server.key

# Generate passwordfile
RUN /gen_passwordfile.sh && \
    chown mosquitto:mosquitto /mosquitto/config/passwordfile /mosquitto/config/aclfile && \
    chmod 600 /mosquitto/config/passwordfile && \
    chmod 700 /mosquitto/config/aclfile

# Drop to mosquitto user
USER mosquitto

# Expose TLS port
EXPOSE 8883

# Launch Mosquitto with dynamic entrypoint
ENTRYPOINT ["/entrypoint.sh"]

