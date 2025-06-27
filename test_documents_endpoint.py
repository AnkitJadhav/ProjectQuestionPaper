#!/usr/bin/env python3
"""
Test the documents endpoint logic directly
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.deps import get_all_documents
from app.schemas import DocumentInfo, DocType

def test_documents_conversion():
    """Test converting raw documents to DocumentInfo objects"""
    
    try:
        print("Testing documents conversion...")
        
        # Get raw documents from database
        raw_docs = get_all_documents()
        print(f"Raw documents: {raw_docs}")
        
        documents = []
        for doc_tuple in raw_docs:
            print(f"Processing: {doc_tuple}")
            doc_id, filename, doc_type, upload_time, status = doc_tuple
            
            print(f"  doc_id: {doc_id} ({type(doc_id)})")
            print(f"  filename: {filename} ({type(filename)})")
            print(f"  doc_type: {doc_type} ({type(doc_type)})")
            print(f"  upload_time: {upload_time} ({type(upload_time)})")
            print(f"  status: {status} ({type(status)})")
            
            # Safely convert doc_type to enum
            try:
                doc_type_enum = DocType(doc_type)
                print(f"  doc_type_enum: {doc_type_enum}")
            except ValueError as e:
                print(f"  ValueError converting doc_type: {e}")
                doc_type_enum = DocType.textbook
            
            try:
                doc_info = DocumentInfo(
                    doc_id=doc_id,
                    filename=filename,
                    doc_type=doc_type_enum,
                    upload_time=upload_time,
                    status=status
                )
                print(f"  DocumentInfo created: {doc_info}")
                documents.append(doc_info)
            except Exception as e:
                print(f"  Error creating DocumentInfo: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\nTotal documents converted: {len(documents)}")
        for doc in documents:
            print(f"  - {doc.dict()}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_documents_conversion() 