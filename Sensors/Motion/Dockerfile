FROM python:3.11.9-slim

WORKDIR /app

COPY smotion.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "smotion.py"]

