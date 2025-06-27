# Ultra-minimal Dockerfile for Render.com - Avoids 2GB temp storage issue
FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y curl --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy requirements and install basic dependencies only
COPY requirements.minimal.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && pip cache purge

# Copy application code
COPY app/ ./app/
COPY start_production.py ./

# Create data directories
RUN mkdir -p data/uploads data/output

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV FORCE_FULL_MODE=true

# Use dynamic port from Render
EXPOSE $PORT

# Use production startup script
CMD ["python", "start_production.py"] 