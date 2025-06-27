#!/bin/bash

# Minimal startup script for Railway deployment
# Installs ML dependencies in background to keep API responsive

set -e

echo "🚀 Starting Question Paper Generator (Minimal Mode)..."

# Create necessary directories
mkdir -p data/uploads data/output

# Set permissions
chmod 755 data/uploads data/output

# Check if Redis is available (non-blocking)
echo "🔄 Checking Redis connection..."
if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
    echo "✅ Redis connected successfully"
else
    echo "⚠️ Redis not available yet (will retry later)"
fi

# Install ML dependencies in background
echo "🔧 Starting ML dependencies installation in background..."
python -c "
import subprocess
import sys
import os

def install_ml_dependencies():
    try:
        print('📦 Installing ML dependencies...')
        deps = [
            'sentence-transformers==2.2.2',
            'transformers==4.35.0', 
            'torch==2.1.0',
            'faiss-cpu==1.7.4',
            'scikit-learn==1.3.0'
        ]
        
        for dep in deps:
            print(f'Installing {dep}...')
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', dep], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print('✅ ML dependencies installed successfully!')
        
        # Create a flag file to indicate completion
        with open('/tmp/ml_ready', 'w') as f:
            f.write('ready')
            
    except Exception as e:
        print(f'❌ Error installing ML dependencies: {e}')

# Start installation in background
import threading
thread = threading.Thread(target=install_ml_dependencies)
thread.daemon = True
thread.start()
print('🎯 ML installation started in background')
" &

# Start the web server immediately
echo "🌐 Starting FastAPI web server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 