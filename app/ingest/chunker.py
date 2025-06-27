import re
from itertools import islice
from typing import Iterator, Tuple


class TextChunker:
    def __init__(self, size: int = 1000, overlap: int = 200):
        self.size = size
        self.olap = overlap

    def clean(self, txt: str) -> str:
        """Clean text by removing unwanted characters and normalizing whitespace"""
        txt = re.sub(r'\s+', ' ', txt.replace('\x00', ''))
        txt = re.sub(r'[^\w\s\.\,\?\!\;\:\-\(\)\[\]\{\}]', '', txt)
        return txt.strip()

    def chunks(self, full_text: str) -> Iterator[Tuple[str, int]]:
        """Split text into overlapping chunks"""
        text = self.clean(full_text)
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + self.size
            chunk_text = text[start:end]
            
            # If we're not at the end, try to break at a sentence boundary
            if end < len(text):
                last_sentence_end = max(
                    chunk_text.rfind('.'),
                    chunk_text.rfind('!'),
                    chunk_text.rfind('?')
                )
                if last_sentence_end > len(chunk_text) * 0.7:  # Only if reasonably close to end
                    chunk_text = chunk_text[:last_sentence_end + 1]
                    end = start + last_sentence_end + 1
            
            if chunk_text.strip():
                yield chunk_text.strip(), chunk_idx
                chunk_idx += 1
            
            start = end - self.olap
            
            # Prevent infinite loop
            if start <= 0:
                start = end


def smart_chunk_by_sections(text: str, max_chunk_size: int = 1000) -> Iterator[Tuple[str, int, str]]:
    """
    Smart chunking that tries to respect document structure
    Returns: (chunk_text, chunk_idx, section_type)
    """
    # Simple heuristics for section detection
    lines = text.split('\n')
    current_chunk = []
    current_size = 0
    chunk_idx = 0
    current_section = "content"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect section headers (simple heuristic)
        if (line.isupper() or 
            re.match(r'^(Chapter|Section|Part|Unit)\s+\d+', line, re.I) or
            re.match(r'^\d+\.\s+[A-Z]', line)):
            
            # Yield current chunk if it exists
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    yield chunk_text, chunk_idx, current_section
                    chunk_idx += 1
                    
            current_chunk = [line]
            current_size = len(line)
            current_section = "header"
            
        else:
            # Add line to current chunk
            line_size = len(line)
            
            if current_size + line_size > max_chunk_size and current_chunk:
                # Yield current chunk
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    yield chunk_text, chunk_idx, current_section
                    chunk_idx += 1
                    
                current_chunk = [line]
                current_size = line_size
                current_section = "content"
            else:
                current_chunk.append(line)
                current_size += line_size
                
    # Yield final chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text:
            yield chunk_text, chunk_idx, current_section


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """
    Simple function to chunk text into overlapping segments
    Returns list of dictionaries with 'text' and metadata
    """
    chunker = TextChunker(size=chunk_size, overlap=overlap)
    chunks = []
    
    for chunk_text, chunk_idx in chunker.chunks(text):
        chunks.append({
            'text': chunk_text,
            'chunk_id': chunk_idx,
            'page': 0  # Will be set by caller if needed
        })
    
    return chunks 