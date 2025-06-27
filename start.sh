#!/bin/bash

echo "🚀 Starting Question Paper Generator"
echo "======================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it and add your DEEPSEEK_API_KEY"
    else
        echo "DEEPSEEK_API_KEY=your_deepseek_api_key_here" > .env
        echo "REDIS_URL=redis://localhost:6379/0" >> .env
        echo "✅ Created basic .env file. Please add your DEEPSEEK_API_KEY"
    fi
    echo ""
fi

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    fi
}

# Choose startup method
echo "Choose how to start the application:"
echo "1) Docker Compose (recommended)"
echo "2) Manual setup (development)"
echo ""
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        echo "🐳 Starting with Docker Compose..."
        check_command "docker-compose"
        
        # Check if DeepSeek API key is set
        if grep -q "your_deepseek_api_key_here" .env; then
            echo "⚠️  Please set your DEEPSEEK_API_KEY in .env file before starting"
            exit 1
        fi
        
        echo "Building and starting services..."
        docker-compose up -d
        
        echo ""
        echo "✅ Services started successfully!"
        echo "📱 Frontend: http://localhost:3000"
        echo "🔧 API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
        ;;
        
    2)
        echo "🔧 Manual setup for development..."
        
        # Check required commands
        check_command "python3"
        check_command "pip"
        check_command "node"
        check_command "npm"
        check_command "redis-server"
        
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            echo "Creating Python virtual environment..."
            python3 -m venv venv
        fi
        
        # Activate virtual environment
        echo "Activating virtual environment..."
        source venv/bin/activate
        
        # Install Python dependencies
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
        
        # Install frontend dependencies
        echo "Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
        
        # Start Redis in background
        echo "Starting Redis..."
        redis-server --daemonize yes
        
        # Create data directories
        mkdir -p data/uploads data/output
        
        echo ""
        echo "✅ Setup complete! Starting services..."
        echo ""
        echo "To start the application:"
        echo "1. Terminal 1: uvicorn app.main:app --reload"
        echo "2. Terminal 2: celery -A app.worker worker --loglevel=info"
        echo "3. Terminal 3: cd frontend && npm start"
        echo ""
        echo "Or run this script with 'auto' parameter to start all services:"
        echo "./start.sh auto"
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Auto start for manual setup
if [ "$1" = "auto" ] && [ "$choice" = "2" ]; then
    echo "🚀 Auto-starting all services..."
    
    # Start FastAPI
    echo "Starting FastAPI server..."
    source venv/bin/activate
    uvicorn app.main:app --reload &
    API_PID=$!
    
    # Start Celery worker
    echo "Starting Celery worker..."
    celery -A app.worker worker --loglevel=info &
    WORKER_PID=$!
    
    # Start frontend
    echo "Starting React frontend..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo "✅ All services started!"
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 API: http://localhost:8000"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "echo '🛑 Stopping services...'; kill $API_PID $WORKER_PID $FRONTEND_PID; exit" INT
    wait
fi 