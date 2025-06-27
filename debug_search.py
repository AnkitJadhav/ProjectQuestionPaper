#!/usr/bin/env python3
"""
Debug script to test search functionality
"""

import sys
sys.path.append('app')

from app.rag.retriever import search_by_doc_id

def main():
    print("🔍 Testing Search Functionality")
    print("=" * 40)
    
    # Test searching in the textbook
    doc_id = 'ecf456a9-656e-4ee3-abe1-a9a7678d0a11'
    query = 'atoms molecules chemistry elements compounds reactions'
    
    print(f"📚 Textbook ID: {doc_id[:8]}...")
    print(f"📝 Query: {query}")
    print()
    
    print("🔍 Searching for chemistry content...")
    chunks = search_by_doc_id(query, doc_id, k=5)
    print(f"📊 Found {len(chunks)} chunks")
    
    if chunks:
        print("\n✅ Sample chunks found:")
        for i, chunk in enumerate(chunks[:3]):
            text = chunk.get('text', '')[:200]
            score = chunk.get('similarity_score', 'N/A')
            print(f"\nChunk {i+1} (score: {score}):")
            print(f"{text}...")
    else:
        print("❌ No chunks found with specific query")
        
        # Try a broader search
        print("\n🔍 Trying broader search with 'chemistry'...")
        chunks = search_by_doc_id('chemistry', doc_id, k=5)
        print(f"📊 Found {len(chunks)} chunks with 'chemistry'")
        
        if chunks:
            print("\n✅ Broader search results:")
            for i, chunk in enumerate(chunks[:2]):
                text = chunk.get('text', '')[:200]
                print(f"\nChunk {i+1}:")
                print(f"{text}...")
        else:
            print("❌ No chunks found even with broader search")
            
            # Try searching for any content from this document
            print("\n🔍 Trying search for any content...")
            chunks = search_by_doc_id('the', doc_id, k=3)
            print(f"📊 Found {len(chunks)} chunks with 'the'")
            
            if chunks:
                print("\n✅ Any content found:")
                for i, chunk in enumerate(chunks[:2]):
                    text = chunk.get('text', '')[:200]
                    print(f"\nChunk {i+1}:")
                    print(f"{text}...")
    
    print("\n" + "=" * 40)
    print("🏁 Debug completed!")

if __name__ == "__main__":
    main() 