#!/usr/bin/env python3
"""
Test the add_document function directly
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.deps import add_document, get_all_documents

def test_add_document():
    """Test add_document function directly"""
    
    try:
        print("Testing add_document function...")
        
        # Test adding a document
        doc_id = "test-doc-123"
        filename = "test.pdf"
        doc_type = "textbook"
        upload_time = datetime.now().isoformat()
        status = "processing"
        
        print(f"Adding document: {doc_id}, {filename}, {doc_type}, {upload_time}, {status}")
        
        add_document(doc_id, filename, doc_type, upload_time, status)
        print("✅ add_document called successfully")
        
        # Test retrieving documents
        print("\nRetrieving all documents...")
        documents = get_all_documents()
        print(f"Documents found: {len(documents)}")
        for doc in documents:
            print(f"  - {doc}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_add_document() 