# Import FAISS only when needed
def _ensure_faiss():
    """Ensure FAISS is available"""
    try:
        from app.runtime_installer import ensure_ml_dependencies
        if not ensure_ml_dependencies():
            raise ImportError("ML dependencies not ready")
        import faiss
        return faiss
    except Exception as e:
        raise ImportError(f"FAISS not available: {e}")
import sqlite3
import os
import json
import numpy as np
from typing import List, Dict


DB_PATH = "data/index.faiss"
META_PATH = "data/metadata.sqlite"
UPLOAD_PATH = "data/uploads"


def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs("data", exist_ok=True)
    os.makedirs(UPLOAD_PATH, exist_ok=True)


def get_index():
    """Get or create FAISS index"""
    faiss = _ensure_faiss()
    ensure_directories()
    if not os.path.exists(DB_PATH):
        dim = 384  # MiniLM output dimension
        index = faiss.IndexFlatL2(dim)
        faiss.write_index(index, DB_PATH)
    return faiss.read_index(DB_PATH)


def add_embeddings(vecs: np.ndarray, metas: List[Dict]):
    """Add embeddings to FAISS index and metadata to SQLite"""
    faiss = _ensure_faiss()
    ensure_directories()
    ix = get_index()
    start_id = ix.ntotal
    ix.add(vecs.astype("float32"))
    faiss.write_index(ix, DB_PATH)

    with sqlite3.connect(META_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)
        cur.executemany(
            "INSERT INTO meta (id, data) VALUES (?,?)",
            [(start_id + i, json.dumps(m)) for i, m in enumerate(metas)],
        )
        con.commit()


def init_documents_table():
    """Initialize documents metadata table"""
    ensure_directories()
    with sqlite3.connect(META_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT,
                doc_type TEXT,
                upload_time TEXT,
                status TEXT
            )
        """)
        con.commit()


def add_document(doc_id: str, filename: str, doc_type: str, upload_time: str, status: str):
    """Add document metadata"""
    ensure_directories()
    with sqlite3.connect(META_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO documents 
            (doc_id, filename, doc_type, upload_time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, filename, doc_type, upload_time, status))
        con.commit()


def get_all_documents():
    """Get all documents from metadata"""
    ensure_directories()
    with sqlite3.connect(META_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT doc_id, filename, doc_type, upload_time, status FROM documents")
        return cur.fetchall()


def update_document_status(doc_id: str, status: str):
    """Update document processing status"""
    ensure_directories()
    with sqlite3.connect(META_PATH) as con:
        cur = con.cursor()
        cur.execute("UPDATE documents SET status = ? WHERE doc_id = ?", (status, doc_id))
        con.commit()


def add_to_index(embedding: np.ndarray, text: str, metadata: dict):
    """
    Add a single embedding to the index (function name used by worker)
    """
    # Convert single embedding to batch format
    vecs = np.array([embedding]).astype("float32")
    
    # Add metadata with text content
    meta_with_text = {
        "text": text,
        **metadata
    }
    
    add_embeddings(vecs, [meta_with_text])


# Initialize tables on import
init_documents_table() 