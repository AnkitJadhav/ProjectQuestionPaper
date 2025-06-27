#!/usr/bin/env python3
"""
Debug script to isolate the tuple error in PDF processing
"""

import os
import sys
import traceback
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.ingest.pdf_reader import stream_pages
from app.ingest.chunker import TextChunker

def debug_pdf_processing():
    """Debug PDF processing step by step"""
    
    # Find the first PDF file
    upload_dir = Path("data/uploads")
    pdf_files = list(upload_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/uploads")
        return
    
    pdf_path = pdf_files[0]
    print(f"Testing with: {pdf_path}")
    
    try:
        print("\n1. Testing stream_pages...")
        page_count = 0
        for page_num, text in stream_pages(str(pdf_path)):
            print(f"Page {page_num}: {len(text)} characters")
            print(f"Text type: {type(text)}")
            print(f"Text preview: {repr(text[:100])}")
            page_count += 1
            if page_count >= 2:  # Test first 2 pages only
                break
        
        print(f"\n2. Testing chunker...")
        chunker = TextChunker()
        
        # Test first page only
        for page_num, text in stream_pages(str(pdf_path)):
            print(f"\nProcessing page {page_num}")
            print(f"Input text type: {type(text)}")
            
            try:
                print("Calling chunker.chunks()...")
                chunks = list(chunker.chunks(text))
                print(f"Generated {len(chunks)} chunks")
                
                for i, chunk_data in enumerate(chunks[:3]):  # First 3 chunks
                    print(f"Chunk {i}: type={type(chunk_data)}, content={type(chunk_data[0]) if isinstance(chunk_data, tuple) else 'not tuple'}")
                    
            except Exception as e:
                print(f"ERROR in chunker: {e}")
                traceback.print_exc()
                
            break  # Only test first page

        print(f"\n3. Testing worker function...")
        try:
            from app.worker import ingest_pdf
            
            # Test with a small subset
            print("Calling ingest_pdf...")
            result = ingest_pdf(str(pdf_path), "test-doc-id", "textbook")
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"ERROR in worker: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdf_processing() 