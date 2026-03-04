# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies for Selenium / Chrome (if needed later)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app
ENV PYTHONPATH=/app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for the Web Dashboard
EXPOSE 8000

# Copy the rest of the application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p data

# Start bot in background and web server in foreground (Unbuffered logs)
CMD python -u bot_listener.py & uvicorn web.main:app --host 0.0.0.0 --port 8000
