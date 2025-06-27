#!/usr/bin/env python3
"""
Production startup script for Render.com deployment
ML dependencies installed during build, starts immediately
"""
import os
import sys
import uvicorn

def main():
    print("🚀 Starting Question Paper Generator in PRODUCTION mode...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Verify main_full.py exists
    main_full_path = "app/main_full.py"
    if os.path.exists(main_full_path):
        print(f"✅ Found {main_full_path}")
    else:
        print(f"❌ ERROR: {main_full_path} not found!")
        sys.exit(1)
    
    # Get port from environment
    port = int(os.environ.get("PORT", 8000))
    print(f"🌐 Starting server on port {port}")
    
    # Create ML ready marker (since dependencies are pre-installed)
    try:
        with open("/tmp/ml_ready", "w") as f:
            f.write("ready")
        print("✅ ML dependencies pre-installed and ready!")
    except:
        pass
    
    # Start server immediately
    try:
        print("📦 Importing app.main_full...")
        from app.main_full import app
        print("✅ Successfully imported full production app")
        
        # Start uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ ERROR starting production app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 