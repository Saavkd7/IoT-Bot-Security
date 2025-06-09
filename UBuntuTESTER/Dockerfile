FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y \
    mosquitto-clients \
    nano \
    curl \
    net-tools \
    iputils-ping \
    iproute2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
    
RUN apt-get update && apt-get install -y \
    nmap \
    sudo \
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
RUN pip3 install scapy paho-mqtt faker scapy netifaces


RUN ip link set eth0 promisc on || true
RUN ip link set eth1 promisc on || true

WORKDIR /app
COPY enable_promisc.sh /usr/local/bin/enable_promisc.sh 
COPY ATTACKS/ /app 
RUN apt update && apt install -y net-tools
RUN chmod +x /usr/local/bin/enable_promisc.sh
CMD ["/usr/local/bin/enable_promisc.sh"]


