FROM python:3.11-slim

WORKDIR /app

# Install git for cloning (if needed) and libpq for Postgres
RUN apt-get update && apt-get install -y git libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "worker.py"]