#!/usr/bin/env python3
"""
Check database contents
"""

import sqlite3
from pathlib import Path

def check_database():
    """Check database contents"""
    
    db_path = Path("data/metadata.sqlite")
    if not db_path.exists():
        print("Database file doesn't exist!")
        return
    
    try:
        with sqlite3.connect(str(db_path)) as con:
            cur = con.cursor()
            
            # Check tables
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cur.fetchall()
            print(f"Tables: {tables}")
            
            # Check documents table
            cur.execute("SELECT * FROM documents")
            documents = cur.fetchall()
            print(f"Documents: {documents}")
            
            # Check meta table if it exists
            if ('meta',) in tables:
                cur.execute("SELECT COUNT(*) FROM meta")
                meta_count = cur.fetchone()[0]
                print(f"Meta entries: {meta_count}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database() 