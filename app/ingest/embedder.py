import numpy as np
from typing import List
import os

# Ensure ML dependencies are installed at runtime
try:
    from app.runtime_installer import ensure_ml_dependencies
    ensure_ml_dependencies()
except Exception as e:
    print(f"Warning: Could not ensure ML dependencies: {e}")

# Now import ML libraries
from sentence_transformers import SentenceTransformer

# Global model instance - loaded once
_model = None


def get_model():
    """Get or load the embedding model"""
    global _model
    if _model is None:
        print("Loading SentenceTransformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded successfully")
    return _model


def embed_batch(texts: List[str], batch_size: int = 10) -> np.ndarray:
    """
    Encode a batch of texts into embeddings
    Args:
        texts: List of text strings to embed
        batch_size: Number of texts to process at once
    Returns:
        numpy array of embeddings
    """
    if not texts:
        return np.array([])
    
    model = get_model()
    
    # Filter out empty texts
    non_empty_texts = [text.strip() for text in texts if text.strip()]
    
    if not non_empty_texts:
        return np.array([])
    
    try:
        embeddings = model.encode(
            non_empty_texts, 
            batch_size=batch_size, 
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings
    except Exception as e:
        print(f"Error during embedding: {e}")
        raise


def embed_single(text: str) -> np.ndarray:
    """Embed a single text string"""
    if not text.strip():
        return np.array([])
    
    return embed_batch([text])[0]


def get_embedding_dimension() -> int:
    """Get the dimension of embeddings from this model"""
    return 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings


def embed_chunks_in_batches(texts: List[str], max_batch_size: int = 32) -> List[np.ndarray]:
    """
    Embed texts in batches to manage memory usage
    Returns list of embedding arrays (one per batch)
    """
    if not texts:
        return []
    
    batches = []
    for i in range(0, len(texts), max_batch_size):
        batch_texts = texts[i:i + max_batch_size]
        batch_embeddings = embed_batch(batch_texts, batch_size=10)
        if batch_embeddings.size > 0:
            batches.append(batch_embeddings)
    
    return batches


def get_embeddings(texts: List[str]) -> List[np.ndarray]:
    """
    Get embeddings for a list of texts (function name used by worker)
    Returns list of numpy arrays, one per text
    """
    if not texts:
        return []
    
    # Use the batch embedding function
    embeddings = embed_batch(texts)
    
    # Convert to list of individual embeddings
    if embeddings.size == 0:
        return []
    
    return [embeddings[i] for i in range(len(embeddings))] 