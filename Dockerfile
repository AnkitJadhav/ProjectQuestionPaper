# Ultra-optimized Dockerfile for Render.com - ML during build, aggressive cleanup
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.render.txt ./requirements.txt

# Install dependencies with aggressive cleanup
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge \
    && rm -rf ~/.cache/pip \
    && rm -rf /tmp/* \
    && find /usr/local/lib/python3.11/site-packages -name "*.pyc" -delete \
    && find /usr/local/lib/python3.11/site-packages -name "__pycache__" -type d -exec rm -rf {} + || true \
    && find /usr/local/lib/python3.11/site-packages -name "*.so" -exec strip {} + || true

# Copy application code
COPY app/ ./app/
COPY start_production.py ./

# Create data directories
RUN mkdir -p data/uploads data/output

# Final cleanup
RUN rm -rf /tmp/* /var/tmp/* /root/.cache || true

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV FORCE_FULL_MODE=true

# Expose port
EXPOSE $PORT

# Start production app
CMD ["python", "start_production.py"] 