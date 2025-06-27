#!/usr/bin/env python3
"""
Simple startup script for the Question Paper Generator application
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == '__main__':
    print("🚀 Starting Question Paper Generator")
    print("=" * 50)
    
    # Check environment variables
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_key:
        print("⚠️  DEEPSEEK_API_KEY not found in environment")
        print("Please set your API key in the .env file")
        sys.exit(1)
    else:
        print(f"✅ DeepSeek API key loaded: {deepseek_key[:10]}...")
    
    # Ensure data directories exist
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    print("✅ Data directories created")
    
    # Start the FastAPI application
    print("🌐 Starting FastAPI server on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔥 Press Ctrl+C to stop the server")
    print("")
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to avoid multiprocessing issues
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1) 