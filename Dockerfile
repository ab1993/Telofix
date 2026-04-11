# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies: Git, Java, and Maven
RUN apt-get update && apt-get install -y \
    git \
    maven \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set a default command (can be overridden by docker-compose)
CMD ["python", "server.py"]