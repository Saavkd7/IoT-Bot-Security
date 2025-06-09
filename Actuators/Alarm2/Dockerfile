FROM python:3.9-slim
RUN apt-get update && \
    apt-get install -y iproute2 && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY GasActuator.py .
COPY entrypoint.sh /entrypoint.sh
COPY certs/ca.crt /mosquitto/certs/ca.crt
RUN chmod 644 /mosquitto/certs/ca.crt
COPY requirements.txt .
RUN chmod +x /entrypoint.sh
RUN apt-get update && apt-get install -y nano
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/entrypoint.sh"]

