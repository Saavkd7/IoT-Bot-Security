FROM python:3.9-slim
RUN apt-get update && \
    apt-get install -y iproute2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY smotion.py .
COPY requirements.txt .
COPY certs/ca.crt /mosquitto/certs/ca.crt
RUN chmod 644 /mosquitto/certs/ca.crt
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y nano
ENTRYPOINT ["/entrypoint.sh"]

