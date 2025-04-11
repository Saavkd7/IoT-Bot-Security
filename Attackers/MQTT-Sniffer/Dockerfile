FROM python:3.9-slim
RUN apt update && apt install -y tcpdump libpcap-dev
RUN pip install scapy
COPY sniffer.py .
CMD ["python", "sniffer.py"]
