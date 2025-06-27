#!/usr/bin/env python3
"""
Production startup script for Render.com deployment
Starts server immediately, installs ML dependencies in background
"""
import os
import sys
import uvicorn
import threading
import time

def install_ml_background():
    """Install ML dependencies in background"""
    time.sleep(5)  # Give server time to start
    try:
        print("🔧 Starting background ML installation...")
        from app.runtime_installer import install_ml_dependencies
        success = install_ml_dependencies()
        if success:
            # Create ready marker
            with open("/tmp/ml_ready", "w") as f:
                f.write("ready")
            print("✅ ML dependencies ready!")
        else:
            print("❌ ML installation failed")
    except Exception as e:
        print(f"❌ Background ML installation error: {e}")

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
    
    # Start ML installation in background thread
    print("🔧 Starting background ML installation...")
    ml_thread = threading.Thread(target=install_ml_background, daemon=True)
    ml_thread.start()
    
    # Start server immediately
    try:
        print("📦 Importing app.main_full...")
        from app.main_full import app
        print("✅ Successfully imported full production app")
        
        # Start uvicorn immediately
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