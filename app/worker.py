from celery import Celery
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
import asyncio
import logging
from queue import Queue
from threading import Thread
import time
import multiprocessing

from .ingest.pdf_reader import stream_pages
from .ingest.chunker import TextChunker
from .ingest.embedder import embed_batch
from .deps import add_embeddings, update_document_status, UPLOAD_PATH
from .rag.retriever import hybrid_search
from .rag.prompt_builder import build_prompt
from .rag.deepseek_client import chat_async
from .postprocess import clean_output
from .pdf_export import create_pdf_from_json


# Initialize Celery
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app = Celery('question_paper_tasks', broker=redis_url, backend=redis_url)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_max_tasks_per_child=50,
)

# Set multiprocessing start method for Windows compatibility
if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')

# Initialize in-memory queue for development
task_queue = Queue()
job_results = {}

# Job status tracking
job_status = {}

def process_queue():
    """Process tasks in the queue"""
    while True:
        try:
            if not task_queue.empty():
                task_id, func, args = task_queue.get()
                try:
                    result = func(*args)
                    job_results[task_id] = result
                    job_status[task_id] = "completed"
                except Exception as e:
                    job_status[task_id] = f"failed: {str(e)}"
                    logging.error(f"Task {task_id} failed: {str(e)}")
                task_queue.task_done()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in queue processor: {str(e)}")
            time.sleep(5)

# Start background thread for processing
try:
    worker_thread = Thread(target=process_queue, daemon=True)
    worker_thread.start()
    logging.info("Background task processor started")
except Exception as e:
    logging.error(f"Failed to start background processor: {str(e)}")

def async_task(func):
    """Decorator for async tasks"""
    def wrapper(*args, **kwargs):
        task_id = str(uuid.uuid4())
        job_status[task_id] = "pending"
        try:
            task_queue.put((task_id, func, args))
            logging.info(f"Task {task_id} queued for processing")
        except Exception as e:
            job_status[task_id] = f"failed: {str(e)}"
            logging.error(f"Failed to queue task {task_id}: {str(e)}")
        return task_id
    return wrapper

def ingest_pdf(file_path: str, doc_id: str, doc_type: str) -> str:
    """Process and ingest a PDF file"""
    task_id = str(uuid.uuid4())
    job_status[task_id] = "processing"
    
    try:
        chunks = []
        chunker = TextChunker()
        
        # Process PDF pages
        for page_num, text in stream_pages(file_path):
            page_chunks = chunker.chunks(text)
            for chunk_text, chunk_idx in page_chunks:
                chunks.append((chunk_text, page_num))
            
        # Generate embeddings in batches
        batch_size = 32
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk[0] for chunk in batch]
            page_nums = [chunk[1] for chunk in batch]
            
            embeddings = embed_batch(texts)
            
            # Store embeddings with metadata
            metadata = [{
                "text": text,
                "page": page_num,
                "doc_id": doc_id,
                "doc_type": doc_type
            } for text, page_num in zip(texts, page_nums)]
            
            add_embeddings(embeddings, metadata)
        
        # Update document status
        update_document_status(doc_id, "completed")
        
        result = {
            "status": "success",
            "file": file_path,
            "chunks": len(chunks)
        }
        
        job_results[task_id] = result
        job_status[task_id] = "completed"
        
        return task_id
        
    except Exception as e:
        logging.error(f"Error processing PDF {file_path}: {str(e)}")
        job_status[task_id] = f"failed: {str(e)}"
        update_document_status(doc_id, "failed")
        return task_id

def generate_question_paper(
    textbook_ids: List[str],
    sample_paper_id: str,
    instructions: Dict[str, Any]
) -> str:
    """Generate a question paper using RAG"""
    task_id = str(uuid.uuid4())
    job_status[task_id] = "processing"
    
    try:
        # Get relevant chunks from sample paper for structure
        structure_chunks = hybrid_search(
            "question paper format structure",
            doc_filter={"doc_id": sample_paper_id},
            k=3
        )
        
        # Get subject content chunks
        subject_chunks = []
        for doc_id in textbook_ids:
            chunks = hybrid_search(
                instructions.get("subject_query", ""),
                doc_filter={"doc_id": doc_id},
                k=5
            )
            subject_chunks.extend(chunks)
        
        # Build prompt
        prompt = build_prompt(instructions, structure_chunks, subject_chunks)
        
        # Generate with LLM
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        raw_output = loop.run_until_complete(chat_async(prompt))
        loop.close()
        
        # Clean and structure output
        structured_data = clean_output(raw_output, instructions)
        
        # Save JSON output
        output_dir = "data/output"
        os.makedirs(output_dir, exist_ok=True)
        
        json_path = os.path.join(output_dir, f"paper_{uuid.uuid4()}.json")
        with open(json_path, "w") as f:
            json.dump(structured_data, f, indent=2)
            
        # Generate PDF
        pdf_path = json_path.replace(".json", ".pdf")
        create_pdf_from_json(structured_data, pdf_path)
        
        result = {
            "status": "success",
            "json_path": json_path,
            "pdf_path": pdf_path
        }
        
        job_results[task_id] = result
        job_status[task_id] = "completed"
        
        return task_id
        
    except Exception as e:
        logging.error(f"Error generating paper: {str(e)}")
        job_status[task_id] = f"failed: {str(e)}"
        return task_id

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get status of a background job"""
    status = job_status.get(job_id, "not_found")
    result = job_results.get(job_id)
    
    return {
        "status": status,
        "result": result if status == "completed" else None
    }

def health_check():
    """Health check task"""
    try:
        # Test database connectivity
        from .deps import get_index
        index = get_index()
        
        # Test LLM connectivity
        from .rag.deepseek_client import test_connection
        llm_ok = test_connection()
        
        return {
            "status": "healthy",
            "vector_db_size": index.ntotal,
            "llm_connection": llm_ok,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Configure periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.worker.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}

celery_app.conf.timezone = 'UTC'


if __name__ == '__main__':
    # For running the worker directly
    celery_app.start() 