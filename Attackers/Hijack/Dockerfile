FROM python:3.9-slim

WORKDIR /app
COPY hijack.py .

RUN pip install paho-mqtt

CMD ["python", "hijack.py"]
