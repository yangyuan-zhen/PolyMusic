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

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for the Web Dashboard
EXPOSE 8000

# Copy the rest of the application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p data

# Use a simple wrapper to run both background tasks and the web server
CMD ["sh", "-c", "python bot_listener.py & python web/main.py"]
