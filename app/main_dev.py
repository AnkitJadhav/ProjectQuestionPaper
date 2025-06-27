from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
from datetime import datetime
from typing import List, Optional
import shutil
import asyncio
import threading

from .schemas import (
    UploadResponse, DocumentInfo, GenerateRequest, 
    GenerateResponse, JobStatus, DocType
)
from .deps import add_document, get_all_documents, UPLOAD_PATH
from .worker_dev import ingest_pdf, generate_question_paper, get_job_status
from .rag.deepseek_client import test_connection


# Initialize FastAPI app
app = FastAPI(
    title="Question Paper Generator (Full Dev Mode)",
    description="Full-featured AI-powered question paper generation - Development Mode",
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

# Serve static files (for generated PDFs)
os.makedirs("data/output", exist_ok=True)
app.mount("/files", StaticFiles(directory="data/output"), name="files")


def run_task_in_background(func, *args, **kwargs):
    """Run a task in background thread"""
    def wrapper():
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"Background task error: {e}")
            import traceback
            traceback.print_exc()
    
    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Question Paper Generator API (Full Development Mode)",
        "version": "1.0.0-dev",
        "status": "running",
        "features": {
            "pdf_upload": "✅ Available",
            "document_processing": "✅ Available", 
            "question_generation": "✅ Available",
            "pdf_export": "✅ Available",
            "background_jobs": "✅ Available (In-Memory)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        from .deps import get_index
        index = get_index()
        
        # Test LLM connection
        llm_status = "unknown"
        try:
            llm_status = "connected" if test_connection() else "disconnected"
        except:
            llm_status = "error"
        
        return {
            "status": "healthy",
            "mode": "full_development",
            "vector_db_size": index.ntotal,
            "llm_status": llm_status,
            "job_queue": "in-memory",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    doc_type: str = Form(...)
):
    """Upload a PDF file"""
    try:
        # Validate doc_type
        if doc_type not in ["textbook", "sample"]:
            raise ValueError(f"Invalid doc_type: {doc_type}. Must be 'textbook' or 'sample'")
        
        # Generate unique ID
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_PATH, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Add document to database
        add_document(
            doc_id=file_id,
            filename=file.filename,
            doc_type=doc_type,  # Use the string directly
            upload_time=datetime.now().isoformat(),
            status="processing"
        )
        
        # Start processing task in background
        task_id = ingest_pdf(file_path, file_id, doc_type)  # Use the string directly
        run_task_in_background(lambda: None)  # Task already started
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "task_id": task_id,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        raw_documents = get_all_documents()
        # Convert tuples to objects
        documents = []
        for doc_tuple in raw_documents:
            doc_id, filename, doc_type, upload_time, status = doc_tuple
            documents.append({
                "doc_id": doc_id,
                "filename": filename,
                "doc_type": doc_type,
                "upload_time": upload_time,
                "status": status
            })
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=GenerateResponse)
async def generate_paper(request: GenerateRequest):
    """Generate a question paper"""
    try:
        # Validate request
        if not request.textbook_ids:
            raise ValueError("No textbooks specified")
        if not request.sample_paper_id:
            raise ValueError("No sample paper specified")
            
        # Start generation task in background
        task_id = generate_question_paper(
            request.textbook_ids,
            request.sample_paper_id,
            request.model_dump()  # Use model_dump instead of deprecated dict()
        )
        run_task_in_background(lambda: None)  # Task already started
        
        return {
            "task_id": task_id,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def check_job_status(job_id: str):
    """Check status of a background job"""
    try:
        status = get_job_status(job_id)
        
        # Convert to expected format
        return {
            "id": status["id"],
            "status": status["status"],
            "progress": status.get("progress", 0),
            "result": status.get("result"),
            "error": status.get("error"),
            "created_at": status.get("created_at"),
            "completed_at": status.get("completed_at") if status["status"] in ["completed", "failed"] else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated file"""
    try:
        file_path = os.path.join("data/output", filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {filename}")
            
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    try:
        from .deps import META_PATH
        import sqlite3
        
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            cur.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Document not found")
            
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_content(query: str, doc_type: Optional[str] = None, limit: int = 10):
    """Search through document content"""
    try:
        from .rag.retriever import semantic_search
        
        results = semantic_search(
            query=query,
            doc_type=doc_type,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        from .deps import get_index, META_PATH
        import sqlite3
        
        # Vector DB stats
        index = get_index()
        vector_count = index.ntotal
        
        # Document stats
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            cur.execute("SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type")
            doc_counts = dict(cur.fetchall())
            
            cur.execute("SELECT status, COUNT(*) FROM documents GROUP BY status")
            status_counts = dict(cur.fetchall())
        
        # Job stats (from in-memory storage)
        from .worker_dev import jobs
        job_stats = {}
        for job in jobs.values():
            status = job["status"]
            job_stats[status] = job_stats.get(status, 0) + 1
        
        return {
            "vector_db": {
                "total_embeddings": vector_count
            },
            "documents": {
                "by_type": doc_counts,
                "by_status": status_counts
            },
            "jobs": job_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Full-Featured Question Paper Generator Development Server...")
    print("📝 All features available with in-memory job processing")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 