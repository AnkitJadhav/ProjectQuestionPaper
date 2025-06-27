#!/bin/bash

echo "🔍 DEBUG: Starting debug script"
echo "🔍 DEBUG: Current time: $(date)"
echo "🔍 DEBUG: Working directory: $(pwd)"
echo "🔍 DEBUG: Environment variables:"
echo "PORT: $PORT"
echo "REDIS_URL: $REDIS_URL"
echo "ENVIRONMENT: $ENVIRONMENT"
echo ""

echo "🔍 DEBUG: Checking Python installation:"
python --version
echo ""

echo "🔍 DEBUG: Checking FastAPI installation:"
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
echo ""

echo "🔍 DEBUG: Checking if app file exists:"
ls -la app/
echo ""

echo "🔍 DEBUG: Testing app import:"
python -c "from app.main_minimal import app; print('App imported successfully')"
echo ""

echo "🔍 DEBUG: Starting server with debug info:"
PORT=${PORT:-8000}
echo "Using port: $PORT"

# Start uvicorn with debug logging
uvicorn app.main_minimal:app --host 0.0.0.0 --port $PORT --log-level debug 