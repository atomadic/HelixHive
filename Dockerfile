FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Ensure the orchestrator is executable
RUN chmod +x orchestrator.py

# Run the heartbeat when the container starts
ENTRYPOINT ["python", "orchestrator.py", "--tick"]
