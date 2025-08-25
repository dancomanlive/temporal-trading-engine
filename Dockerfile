FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

# Run the worker
CMD ["python", "workers/monitoring_worker.py"]