import sqlite3
import json
import numpy as np
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure ML dependencies are installed at runtime
try:
    from app.runtime_installer import ensure_ml_dependencies
    ensure_ml_dependencies()
except Exception as e:
    print(f"Warning: Could not ensure ML dependencies: {e}")

import faiss

from deps import get_index, META_PATH
from ingest.embedder import embed_batch


def search(query: str, k: int = 8, meta_filter: Optional[Dict] = None) -> List[Dict]:
    """
    Search for similar chunks using semantic similarity
    Args:
        query: Search query text
        k: Number of results to return
        meta_filter: Optional filter dict for metadata (e.g. {"doc_type": "textbook"})
    Returns:
        List of chunk dictionaries with metadata
    """
    try:
        # Get query embedding
        qvec = embed_batch([query]).astype("float32")
        
        # Search in FAISS index
        ix = get_index()
        if ix.ntotal == 0:
            return []
            
        scores, ids = ix.search(qvec, min(k * 3, ix.ntotal))  # Get more results for filtering
        ids = ids[0].tolist()
        scores = scores[0].tolist()
        
        # Filter out invalid IDs
        valid_indices = [i for i, id_val in enumerate(ids) if id_val != -1]
        ids = [ids[i] for i in valid_indices]
        scores = [scores[i] for i in valid_indices]
        
        if not ids:
            return []
        
        # Get metadata from SQLite
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            placeholders = ",".join("?" * len(ids))
            rows = cur.execute(
                f"SELECT id, data FROM meta WHERE id IN ({placeholders})",
                ids
            ).fetchall()
            
            # Create mapping of id to data
            id_to_data = {row[0]: json.loads(row[1]) for row in rows}
            
            # Build results with scores
            chunks = []
            for i, chunk_id in enumerate(ids):
                if chunk_id in id_to_data:
                    chunk_data = id_to_data[chunk_id]
                    chunk_data['similarity_score'] = float(scores[i])
                    chunks.append(chunk_data)
        
        # Apply metadata filters
        if meta_filter:
            filtered_chunks = []
            for chunk in chunks:
                if all(chunk.get(k) == v for k, v in meta_filter.items()):
                    filtered_chunks.append(chunk)
            chunks = filtered_chunks
        
        # Sort by similarity score (lower is better for L2 distance)
        chunks.sort(key=lambda x: x.get('similarity_score', float('inf')))
        
        return chunks[:k]
        
    except Exception as e:
        print(f"Error in search: {e}")
        return []


def search_by_doc_type(query: str, doc_type: str, k: int = 8) -> List[Dict]:
    """Search within a specific document type"""
    return search(query, k, meta_filter={"doc_type": doc_type})


def search_by_doc_id(query: str, doc_id: str, k: int = 8) -> List[Dict]:
    """Search within a specific document"""
    return search(query, k, meta_filter={"doc_id": doc_id})


def get_random_chunks(doc_type: str, k: int = 5) -> List[Dict]:
    """Get random chunks from a document type (for testing/fallback)"""
    try:
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            rows = cur.execute(
                "SELECT data FROM meta WHERE json_extract(data, '$.doc_type') = ? ORDER BY RANDOM() LIMIT ?",
                (doc_type, k)
            ).fetchall()
            
            return [json.loads(row[0]) for row in rows]
            
    except Exception as e:
        print(f"Error getting random chunks: {e}")
        return []


def get_chunks_by_document(doc_id: str, limit: int = None) -> List[Dict]:
    """Get all chunks from a specific document"""
    try:
        with sqlite3.connect(META_PATH) as con:
            cur = con.cursor()
            
            query = "SELECT data FROM meta WHERE json_extract(data, '$.doc_id') = ?"
            params = [doc_id]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
                
            rows = cur.execute(query, params).fetchall()
            
            return [json.loads(row[0]) for row in rows]
            
    except Exception as e:
        print(f"Error getting chunks by document: {e}")
        return []


def hybrid_search(query: str, subject_docs: List[str], sample_doc: str, k_per_type: int = 10) -> Dict[str, List[Dict]]:
    """
    Perform hybrid search across different document types
    Returns structured results for question paper generation
    """
    results = {
        "structure_chunks": [],
        "subject_chunks": []
    }
    
    try:
        # Search for structure/format information in sample papers
        structure_chunks = search_by_doc_id(
            "question paper format structure sections marks", 
            sample_doc, 
            k_per_type
        )
        results["structure_chunks"] = structure_chunks
        
        # Search for subject content across all subject documents
        subject_chunks = []
        for doc_id in subject_docs:
            doc_chunks = search_by_doc_id(query, doc_id, k_per_type // len(subject_docs) + 1)
            subject_chunks.extend(doc_chunks)
        
        # Sort by relevance and limit
        subject_chunks.sort(key=lambda x: x.get('similarity_score', float('inf')))
        results["subject_chunks"] = subject_chunks[:k_per_type]
        
    except Exception as e:
        print(f"Error in hybrid search: {e}")
    
    return results


def semantic_search(query: str, doc_type: Optional[str] = None, doc_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Semantic search function used by the worker
    
    Args:
        query: Search query
        doc_type: Optional document type filter
        doc_id: Optional specific document ID
        limit: Maximum number of results
    
    Returns:
        List of relevant chunks
    """
    if doc_id:
        return search_by_doc_id(query, doc_id, limit)
    elif doc_type:
        return search_by_doc_type(query, doc_type, limit)
    else:
        return search(query, limit) 