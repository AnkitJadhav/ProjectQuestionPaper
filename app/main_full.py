"""
Full-featured FastAPI app for Railway deployment
Includes all Question Paper Generator functionality with smart startup
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import shutil
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="Question Paper Generator",
    description="AI-powered question paper generation from textbooks and sample papers",
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

# Create necessary directories
os.makedirs("data/output", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)

# Serve static files (for generated PDFs)
app.mount("/files", StaticFiles(directory="data/output"), name="files")

# Global variables for lazy loading
_deps_loaded = False
_ml_ready = False

def _load_deps():
    """Load basic dependencies"""
    global _deps_loaded
    if not _deps_loaded:
        try:
            from .deps import add_document, get_all_documents, UPLOAD_PATH, init_documents_table
            init_documents_table()  # Initialize database tables
            _deps_loaded = True
            return add_document, get_all_documents, UPLOAD_PATH
        except Exception as e:
            print(f"Warning: Could not load deps: {e}")
            raise HTTPException(status_code=503, detail="Database not ready")
    else:
        from .deps import add_document, get_all_documents, UPLOAD_PATH
        return add_document, get_all_documents, UPLOAD_PATH

def _load_worker():
    """Load worker functions"""
    try:
        from .worker import ingest_pdf, generate_question_paper, get_job_status
        return ingest_pdf, generate_question_paper, get_job_status
    except Exception as e:
        print(f"Warning: Could not load worker: {e}")
        raise HTTPException(status_code=503, detail="Worker not ready")

def _load_schemas():
    """Load schema definitions"""
    try:
        from .schemas import (
            UploadResponse, DocumentInfo, GenerateRequest, 
            GenerateResponse, JobStatus, DocType
        )
        return UploadResponse, DocumentInfo, GenerateRequest, GenerateResponse, JobStatus, DocType
    except Exception as e:
        print(f"Warning: Could not load schemas: {e}")
        return None, None, None, None, None, None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Question Paper Generator API",
        "version": "1.0.0",
        "status": "running",
        "features": ["upload", "generation", "search"],
        "mode": "full"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    global _ml_ready
    
    try:
        response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "mode": "full"
        }
        
        # Check Redis connection
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            response["redis_configured"] = True
            try:
                import redis
                r = redis.from_url(redis_url)
                r.ping()
                response["redis_status"] = "connected"
            except Exception as e:
                response["redis_status"] = f"error: {str(e)}"
        else:
            response["redis_configured"] = False
            response["redis_status"] = "not_configured"
        
        # Check database
        try:
            _load_deps()
            response["database_status"] = "ready"
        except:
            response["database_status"] = "not_ready"
        
        # Check ML status
        if os.path.exists("/tmp/ml_ready"):
            response["ml_status"] = "ready"
            _ml_ready = True
        else:
            response["ml_status"] = "pending"
            
        return response
        
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"ping": "pong", "timestamp": datetime.now().isoformat()}

@app.get("/ready")
async def ready():
    """Ultra-simple ready check - always responds quickly"""
    return {"ready": True}

@app.get("/status")
async def status():
    """Detailed status information"""
    global _ml_ready
    
    return {
        "app": "Question Paper Generator",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "features": {
            "database": _deps_loaded,
            "ml_processing": _ml_ready,
            "redis": bool(os.getenv("REDIS_URL")),
            "file_upload": True,
            "pdf_generation": True
        }
    }

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    doc_type: str = "textbook"
):
    """Upload a PDF file for processing"""
    try:
        # Load dependencies
        add_document, get_all_documents, UPLOAD_PATH = _load_deps()
        ingest_pdf, generate_question_paper, get_job_status = _load_worker()
        
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Generate unique ID and save file
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_PATH, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Add to database
        add_document(
            doc_id=file_id,
            filename=file.filename,
            doc_type=doc_type,
            upload_time=datetime.now().isoformat(),
            status="uploaded"
        )
        
        # Start processing if ML is ready
        task_id = None
        if _ml_ready:
            try:
                task_id = ingest_pdf(file_path, file_id, doc_type)
            except Exception as e:
                print(f"Could not start processing: {e}")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "task_id": task_id,
            "status": "uploaded",
            "message": "File uploaded successfully. Processing will start when ML dependencies are ready." if not _ml_ready else "File uploaded and processing started."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        add_document, get_all_documents, UPLOAD_PATH = _load_deps()
        documents = get_all_documents()
        
        return {
            "documents": [
                {
                    "doc_id": doc[0],
                    "filename": doc[1], 
                    "doc_type": doc[2],
                    "upload_time": doc[3],
                    "status": doc[4]
                }
                for doc in documents
            ],
            "total_count": len(documents)
        }
        
    except Exception as e:
        return {"error": str(e), "documents": []}

@app.post("/generate")
async def generate_paper(
    textbook_ids: List[str],
    sample_paper_id: str,
    subject: str = "General",
    exam_type: str = "midterm",
    difficulty: str = "medium"
):
    """Generate a question paper"""
    try:
        if not _ml_ready:
            raise HTTPException(
                status_code=503, 
                detail="ML dependencies not ready yet. Please wait a few minutes and try again."
            )
        
        # Load worker functions
        ingest_pdf, generate_question_paper, get_job_status = _load_worker()
        
        # Validate inputs
        if not textbook_ids:
            raise HTTPException(status_code=400, detail="No textbooks specified")
        if not sample_paper_id:
            raise HTTPException(status_code=400, detail="No sample paper specified")
        
        # Start generation task
        config = {
            "textbook_ids": textbook_ids,
            "sample_paper_id": sample_paper_id,
            "subject": subject,
            "exam_type": exam_type,
            "difficulty": difficulty
        }
        
        task_id = generate_question_paper(textbook_ids, sample_paper_id, config)
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Question paper generation started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}")
async def check_job_status(job_id: str):
    """Check the status of a background job"""
    try:
        ingest_pdf, generate_question_paper, get_job_status = _load_worker()
        return get_job_status(job_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated file"""
    try:
        file_path = os.path.join("data/output", filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    try:
        add_document, get_all_documents, UPLOAD_PATH = _load_deps()
        
        # This is a simplified implementation
        # In production, you'd also remove from vector DB
        import sqlite3
        from .deps import META_PATH
        
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            cur.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task to install ML dependencies
@app.on_event("startup")
async def startup_event():
    """Background initialization of ML dependencies"""
    global _ml_ready
    
    if os.path.exists("/tmp/ml_ready"):
        _ml_ready = True
        print("✅ ML dependencies already ready")
        return
    
    async def install_ml_deps():
        try:
            print("🔧 Starting ML dependencies installation...")
            from .runtime_installer import install_ml_dependencies
            success = install_ml_dependencies()
            if success:
                _ml_ready = True
                print("🎉 ML dependencies installed successfully!")
                # Create ready flag
                with open("/tmp/ml_ready", "w") as f:
                    f.write("ready")
            else:
                print("❌ Failed to install ML dependencies")
        except Exception as e:
            print(f"❌ Error installing ML dependencies: {e}")
    
    # Start installation in background
    asyncio.create_task(install_ml_deps())

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    ) 