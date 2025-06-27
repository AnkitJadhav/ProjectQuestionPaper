#!/usr/bin/env python3
"""
Test script to upload a file via the API endpoint
"""

import requests
import os
from pathlib import Path

def test_upload():
    """Test file upload via API"""
    
    # Find an existing PDF file
    upload_dir = Path("data/uploads")
    pdf_files = list(upload_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found")
        return
    
    pdf_path = pdf_files[0]
    print(f"Testing upload with: {pdf_path}")
    
    # Prepare the file upload
    url = "http://localhost:8000/upload"
    
    with open(pdf_path, 'rb') as f:
        files = {
            'file': ('test.pdf', f, 'application/pdf')
        }
        data = {
            'doc_type': 'textbook'
        }
        
        try:
            print("Sending upload request...")
            response = requests.post(url, files=files, data=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Upload successful!")
                
                # Check documents endpoint
                print("\nChecking documents endpoint...")
                docs_response = requests.get("http://localhost:8000/documents")
                print(f"Documents: {docs_response.text}")
                
            else:
                print("❌ Upload failed!")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_upload() 