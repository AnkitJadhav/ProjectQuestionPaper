#!/bin/bash

# Railway startup script for Question Paper Generator

set -e

echo "🚀 Starting Question Paper Generator on Railway..."

# Create necessary directories
mkdir -p data/uploads data/output

# Set permissions
chmod 755 data/uploads data/output

# Check if Redis is available (retry logic)
echo "🔄 Waiting for Redis connection..."
for i in {1..30}; do
    if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
        echo "✅ Redis connected successfully"
        break
    fi
    echo "⏳ Waiting for Redis... (attempt $i/30)"
    sleep 2
done

# Download ML models if not present (for faster startup)
python -c "
import os
from sentence_transformers import SentenceTransformer
model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
print(f'📦 Loading embedding model: {model_name}')
model = SentenceTransformer(model_name)
print('✅ Model loaded successfully')
"

# Start the application based on process type
if [ "$RAILWAY_SERVICE_NAME" = "worker" ]; then
    echo "🔧 Starting Celery Worker..."
    exec celery -A app.worker worker --loglevel=info --concurrency=2
elif [ "$RAILWAY_SERVICE_NAME" = "beat" ]; then
    echo "⏰ Starting Celery Beat..."
    exec celery -A app.worker beat --loglevel=info
else
    echo "🌐 Starting FastAPI Web Server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi 