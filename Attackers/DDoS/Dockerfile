# Dockerfile.ddos
FROM python:3.9-slim

WORKDIR /app
COPY DDOs.py .

RUN pip install paho-mqtt

ENV BROKER_ADDRESS=mqtt-broker
ENV TARGET_TOPIC=building/zone3/gas/detection
ENV ATTACK_RATE=0.01

CMD ["python", "DDOs.py"]
