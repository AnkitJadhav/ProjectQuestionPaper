#!/usr/bin/env python3
"""
Test get_all_documents function directly
"""

import sys
import sqlite3
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_get_all_documents():
    """Test get_all_documents function directly"""
    
    try:
        # Check if the documents table exists
        db_path = "data/metadata.sqlite"
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            
            # Check if documents table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            table_exists = cur.fetchone()
            print(f"Documents table exists: {table_exists is not None}")
            
            if not table_exists:
                print("Creating documents table...")
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
                print("Documents table created")
            
            # Test direct query
            cur.execute("SELECT * FROM documents")
            docs = cur.fetchall()
            print(f"Direct query results: {docs}")
        
        # Now test the function
        from app.deps import get_all_documents
        print("Testing get_all_documents function...")
        
        documents = get_all_documents()
        print(f"Function result: {documents}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_all_documents() 