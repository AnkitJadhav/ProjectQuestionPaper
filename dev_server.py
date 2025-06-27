#!/usr/bin/env python3
"""
Development server that runs without Redis/Celery dependencies
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uuid
import shutil
from datetime import datetime
from typing import List, Optional

# Set up paths
sys.path.append('.')
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Question Paper Generator (Dev Mode)",
    description="Development version - AI-powered question paper generation",
    version="1.0.0-dev"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/files", StaticFiles(directory="data/output"), name="files")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Question Paper Generator API (Development Mode)",
        "version": "1.0.0-dev",
        "status": "running",
        "note": "This is a development server without Redis/Celery"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "development",
        "redis": "not required",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF file (simplified for development)"""
    try:
        # Generate unique ID
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join("data/uploads", filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "file_id": file_id,
            "filename": file.filename,
            "status": "uploaded",
            "message": "File uploaded successfully (processing not implemented in dev mode)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        uploads_dir = "data/uploads"
        if not os.path.exists(uploads_dir):
            return {"documents": []}
            
        files = []
        for filename in os.listdir(uploads_dir):
            if filename.endswith('.pdf'):
                files.append({
                    "filename": filename,
                    "upload_time": datetime.now().isoformat(),
                    "status": "uploaded"
                })
        
        return {"documents": files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_paper():
    """Generate a question paper (placeholder for development)"""
    return {
        "task_id": str(uuid.uuid4()),
        "status": "not implemented",
        "message": "Question paper generation requires full setup with Redis/Celery"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "message": "Development server is working!",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Question Paper Generator Development Server...")
    print("📝 This is a simplified version without Redis/Celery")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 