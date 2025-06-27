"""
Runtime installer for ML dependencies
This installs heavy ML libraries at container startup to keep build image small
"""
import subprocess
import sys
import os
import importlib
from typing import List

# ML dependencies to install at runtime
ML_DEPENDENCIES = [
    "sentence-transformers==2.2.2",
    "transformers==4.35.0", 
    "torch==2.1.0",
    "faiss-cpu==1.7.4",
    "numpy==1.24.3",
    "scikit-learn==1.3.0"
]

def is_package_installed(package_name: str) -> bool:
    """Check if a package is already installed"""
    try:
        importlib.import_module(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False

def install_package(package: str) -> bool:
    """Install a single package"""
    try:
        print(f"📦 Installing {package}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--no-cache-dir", package
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def install_ml_dependencies() -> bool:
    """Install all ML dependencies if not already present"""
    print("🔍 Checking ML dependencies...")
    
    # Quick check for main packages
    main_packages = ["sentence_transformers", "torch", "faiss"]
    all_installed = all(is_package_installed(pkg) for pkg in main_packages)
    
    if all_installed:
        print("✅ All ML dependencies already installed")
        return True
    
    print("📥 Installing ML dependencies at runtime...")
    print("⏳ This may take 2-3 minutes on first startup...")
    
    failed_packages = []
    for package in ML_DEPENDENCIES:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"❌ Failed to install: {failed_packages}")
        return False
    
    print("🎉 All ML dependencies installed successfully!")
    return True

def ensure_ml_dependencies():
    """Ensure ML dependencies are installed, install if missing"""
    try:
        # Check if ML dependencies are already ready
        if os.path.exists("/tmp/ml_ready"):
            return True
            
        # Check if we're in a production environment
        if os.getenv("ENVIRONMENT") == "production":
            print("🚀 Production environment detected")
        
        success = install_ml_dependencies()
        return success
            
    except Exception as e:
        print(f"⚠️ Warning: Could not install ML dependencies: {e}")
        return False

if __name__ == "__main__":
    ensure_ml_dependencies() 