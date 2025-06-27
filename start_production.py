#!/usr/bin/env python3
"""
Production startup script for Render.com deployment
ML dependencies installed during build, starts immediately
"""
import os
import sys
import traceback

def main():
    try:
        print("🚀 Starting Question Paper Generator in PRODUCTION mode...")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
        
        # Test basic imports first
        print("🔍 Testing basic imports...")
        import fastapi
        print("✅ FastAPI imported")
        import uvicorn
        print("✅ Uvicorn imported")
        import sqlite3
        print("✅ SQLite3 imported")
        
        # Verify main_full.py exists
        main_full_path = "app/main_full.py"
        if os.path.exists(main_full_path):
            print(f"✅ Found {main_full_path}")
        else:
            print(f"❌ ERROR: {main_full_path} not found!")
            print("Available files in app/:")
            try:
                for file in os.listdir("app"):
                    print(f"  - {file}")
            except Exception as e:
                print(f"  - Could not list app/ directory: {e}")
            sys.exit(1)
        
        # Get port from environment
        port = int(os.environ.get("PORT", 8000))
        print(f"🌐 Starting server on port {port}")
        
        # Create ML ready marker (since dependencies are pre-installed)
        try:
            with open("/tmp/ml_ready", "w") as f:
                f.write("ready")
            print("✅ ML dependencies pre-installed and ready!")
        except Exception as e:
            print(f"⚠️ Could not create ML ready marker: {e}")
        
        # Test app import
        print("📦 Testing app.main_full import...")
        try:
            from app.main_full import app
            print("✅ Successfully imported full production app")
        except Exception as e:
            print(f"❌ ERROR importing app.main_full: {e}")
            print("Traceback:")
            traceback.print_exc()
            sys.exit(1)
        
        # Start uvicorn
        print("🌐 Starting uvicorn server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in startup: {e}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 