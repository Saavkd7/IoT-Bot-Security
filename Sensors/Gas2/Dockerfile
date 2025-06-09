FROM python:3.9-slim
RUN apt-get update && \
    apt-get install -y iproute2 && \
    rm -rf /var/lib/apt/lists/*
    
RUN apt-get update && apt-get install -y \
    tcpdump \
    iputils-ping \
    net-tools \
    iproute2 \
    curl \
    wget \
    dnsutils \
    vim \
    nano \
    netcat-openbsd \
    telnet \
    openssl \
    procps \
    python3 \
    python3-pip \
    git \
    && apt-get clean


# Optional: Add tools like scapy, mqtt clients, etc.
RUN pip3 install scapy paho-mqtt faker

WORKDIR /app
COPY sgas.py .
COPY requirements.txt .
COPY entrypoint.sh /entrypoint.sh
COPY certs/ca.crt /mosquitto/certs/ca.crt
RUN chmod 644 /mosquitto/certs/ca.crt
RUN chmod +x /entrypoint.sh
RUN apt-get update && apt-get install -y nano
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/entrypoint.sh"]

