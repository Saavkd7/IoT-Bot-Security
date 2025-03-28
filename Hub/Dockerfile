# Use slim Python image
FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Default command (overridden per container in docker-compose)
CMD ["python", "hub.py"]

