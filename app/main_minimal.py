"""
Minimal FastAPI app for Railway deployment
Only includes essential endpoints to pass healthcheck
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Question Paper Generator",
    description="AI-powered question paper generation (minimal mode)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Question Paper Generator API",
        "version": "1.0.0",
        "status": "running",
        "mode": "minimal"
    }

@app.get("/health")
async def health_check():
    """Ultra-minimal health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": "minimal",
        "version": "1.0.0"
    }

@app.get("/ping")
async def ping():
    """Simplest possible endpoint"""
    return {"ping": "pong"}

@app.get("/test")
async def test():
    """Test endpoint"""
    return {
        "test": "ok",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    """Status endpoint"""
    return {
        "app": "Question Paper Generator",
        "status": "running",
        "mode": "minimal",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown")
    } 