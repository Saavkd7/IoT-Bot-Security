FROM python:3.9-slim
RUN apt-get update && \
    apt-get install -y iproute2 && \
    rm -rf /var/lib/apt/lists/*
COPY stemp.py /app/stemp.py
COPY requirements.txt /app/
COPY certs/ca.crt /mosquitto/certs/ca.crt
RUN chmod 644 /mosquitto/certs/ca.crt
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN apt-get update && apt-get install -y nano
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/entrypoint.sh"]
# CMD ["python3", "stemp.py"]
