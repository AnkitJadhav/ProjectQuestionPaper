from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import shutil
import asyncio

from .schemas import (
    UploadResponse, DocumentInfo, GenerateRequest, 
    GenerateResponse, JobStatus, DocType, EnhancedGenerationRequest, ProfessionalQuestionConfig, ChapterWeightage
)
from .deps import add_document, get_all_documents, UPLOAD_PATH
from .worker import ingest_pdf, generate_question_paper, get_job_status
from .rag.deepseek_client import test_connection
from enhanced_worker import generate_professional_question_paper, get_enhanced_job_status


# Initialize FastAPI app
app = FastAPI(
    title="Question Paper Generator",
    description="AI-powered question paper generation from textbooks and sample papers",
    version="1.0.0"
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Question Paper Generator API",
        "version": "1.0.0",
        "status": "running"
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
            "vector_db_size": index.ntotal,
            "llm_status": llm_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    doc_type: DocType = DocType.textbook
):
    """Upload a PDF file"""
    try:
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
            doc_type=doc_type.value,
            upload_time=datetime.now().isoformat(),
            status="processing"
        )
        
        # Start processing task
        task_id = ingest_pdf(file_path, file_id, doc_type.value)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "task_id": task_id,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Server is working", "timestamp": "2025-06-24-test"}


@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        # First, let's just return raw documents to see if that works
        raw_docs = get_all_documents()
        return {"raw_documents": raw_docs}
    except Exception as e:
        return {"error": str(e), "type": str(type(e))}


@app.post("/generate", response_model=GenerateResponse)
async def generate_paper(request: GenerateRequest):
    """Generate a question paper"""
    try:
        # Validate request
        if not request.textbook_ids:
            raise ValueError("No textbooks specified")
        if not request.sample_paper_id:
            raise ValueError("No sample paper specified")
            
        # Start generation task
        task_id = generate_question_paper(
            request.textbook_ids,
            request.sample_paper_id,
            request.dict()
        )
        
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
        return get_job_status(job_id)
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
        # Note: This is a simplified implementation
        # In production, you'd want to also remove from vector DB
        from .deps import META_PATH
        import sqlite3
        
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            cur.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Document not found")
            con.commit()
        
        # Try to delete physical file
        import glob
        files_to_delete = glob.glob(os.path.join(UPLOAD_PATH, f"{doc_id}_*"))
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
            except:
                pass  # File might not exist
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/search")
async def search_content(query: str, doc_type: Optional[str] = None, limit: int = 10):
    """Search through uploaded content"""
    try:
        from .rag.retriever import search, search_by_doc_type
        
        if doc_type:
            results = search_by_doc_type(query, doc_type, limit)
        else:
            results = search(query, limit)
        
        # Clean results for API response
        cleaned_results = []
        for result in results:
            cleaned_result = {
                "doc_id": result.get("doc_id"),
                "filename": result.get("filename"),
                "doc_type": result.get("doc_type"),
                "page": result.get("page"),
                "text_preview": result.get("text", "")[:200],
                "similarity_score": result.get("similarity_score")
            }
            cleaned_results.append(cleaned_result)
        
        return {
            "query": query,
            "results": cleaned_results,
            "total": len(cleaned_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get application statistics"""
    try:
        from .deps import get_index, META_PATH
        import sqlite3
        
        # Vector DB stats
        index = get_index()
        
        # Document stats
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            
            # Total documents
            total_docs = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            
            # Documents by type
            doc_types = cur.execute("""
                SELECT doc_type, COUNT(*) 
                FROM documents 
                GROUP BY doc_type
            """).fetchall()
            
            # Documents by status
            doc_status = cur.execute("""
                SELECT status, COUNT(*) 
                FROM documents 
                GROUP BY status
            """).fetchall()
        
        return {
            "vector_db": {
                "total_embeddings": index.ntotal,
                "dimension": 384
            },
            "documents": {
                "total": total_docs,
                "by_type": dict(doc_types),
                "by_status": dict(doc_status)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")


@app.post("/api/generate-professional")
async def generate_professional_paper(request: EnhancedGenerationRequest):
    """
    Generate professional question paper with multiple textbooks and chapter weightage
    """
    try:
        # Convert request to async call
        loop = asyncio.get_event_loop()
        job_id = await generate_professional_question_paper(
            chapter_weightages=request.textbook_sources,
            sample_paper_id=request.sample_paper_id,
            config=request.question_config,
            special_instructions=request.special_instructions
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Professional question paper generation started",
            "sources_count": len(request.textbook_sources),
            "total_questions": request.question_config.total_questions
        }
        
    except Exception as e:
        logger.error(f"Error starting professional generation: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/professional-status/{job_id}")
async def get_professional_status(job_id: str):
    """Get status of professional question paper generation job"""
    try:
        status = get_enhanced_job_status(job_id)
        return {
            "success": True,
            "job_id": job_id,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting professional job status: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/create-chapter-weightage")
async def create_chapter_weightage_helper(
    chapters: List[Dict[str, Any]]
):
    """
    Helper endpoint to create chapter weightage from uploaded documents
    """
    try:
        weightages = []
        total_percentage = 0
        
        for chapter in chapters:
            weightage = ChapterWeightage(
                chapter_name=chapter.get("chapter_name", "Unknown Chapter"),
                document_id=chapter.get("document_id"),
                weightage_percentage=chapter.get("weightage_percentage", 25),
                focus_topics=chapter.get("focus_topics", []),
                difficulty_level=chapter.get("difficulty_level", "medium")
            )
            weightages.append(weightage)
            total_percentage += weightage.weightage_percentage
        
        # Normalize to 100% if needed
        if total_percentage != 100:
            for w in weightages:
                w.weightage_percentage = int((w.weightage_percentage / total_percentage) * 100)
        
        return {
            "success": True,
            "chapter_weightages": [w.dict() for w in weightages],
            "total_percentage": sum(w.weightage_percentage for w in weightages)
        }
        
    except Exception as e:
        logger.error(f"Error creating chapter weightage: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/professional-config-template")
async def get_professional_config_template():
    """Get template for professional question configuration"""
    return {
        "success": True,
        "template": {
            "total_questions": 20,
            "total_marks": 80,
            "marks_per_question": 5,
            "definition_questions": 5,
            "explanation_questions": 5,
            "comparison_questions": 3,
            "application_questions": 4,
            "analysis_questions": 3,
            "word_limit_min": 75,
            "word_limit_max": 100,
            "include_diagrams_references": False,
            "include_numerical_problems": False,
            "academic_level": "undergraduate"
        },
        "question_types": {
            "definition": "Questions asking for definitions, concepts, meanings",
            "explanation": "Questions requiring detailed explanations or descriptions", 
            "comparison": "Questions asking to compare, contrast, or differentiate",
            "application": "Questions about applications, examples, or practical uses",
            "analysis": "Questions requiring analysis, evaluation, or critical thinking"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 