FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ghost/ ghost/
COPY config/ config/
COPY main.py .

# Create data directory
RUN mkdir -p data/logs data/vector_db data/memory_snapshots

# Run as non-root user
RUN useradd -m -u 1000 ghost && chown -R ghost:ghost /app
USER ghost

CMD ["python", "main.py"]