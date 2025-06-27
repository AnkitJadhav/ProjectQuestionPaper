#!/usr/bin/env python3
"""
Test script for the new question paper generation system
"""

import sys
import time
sys.path.append('app')

from app.worker_dev import generate_question_paper, get_job_status

def main():
    print("🚀 Testing New Question Paper Generation System")
    print("=" * 50)
    
    # Test configuration with correct IDs
    textbook_ids = ['ecf456a9-656e-4ee3-abe1-a9a7678d0a11']  # Chemistry textbook
    sample_paper_id = 'd43b5ceb-063a-4832-a072-3939ca2451fc'  # Sample paper
    config = {
        'subject_query': 'atoms molecules chemistry elements compounds reactions',
        'grade': 'BSc',
        'total_marks': 80
    }
    
    print(f"📚 Using textbook: {textbook_ids[0][:8]}...")
    print(f"📋 Using sample paper: {sample_paper_id[:8]}...")
    print(f"🎯 Subject query: {config['subject_query']}")
    print()
    
    # Start generation
    print("🔄 Starting generation...")
    job_id = generate_question_paper(textbook_ids, sample_paper_id, config)
    print(f"📝 Job ID: {job_id}")
    print()
    
    # Monitor progress
    print("📊 Monitoring progress...")
    for i in range(30):  # Check for up to 30 seconds
        status = get_job_status(job_id)
        
        if not status or status.get('status') == 'not_found':
            print("❌ Job not found")
            break
            
        progress = status.get('progress', 0)
        current_status = status.get('status', 'unknown')
        
        print(f"   Progress: {progress}% - Status: {current_status}")
        
        if current_status == 'completed':
            result = status.get('result', {})
            print()
            print("✅ GENERATION COMPLETED!")
            print(f"📄 PDF File: {result.get('pdf_filename', 'Unknown')}")
            print(f"📊 Total Questions: {result.get('total_questions', 'Unknown')}")
            print(f"💯 Total Marks: {result.get('total_marks', 'Unknown')}")
            print(f"✔️ Format Validation: {result.get('format_validated', {})}")
            break
            
        elif current_status == 'failed':
            error = status.get('error', 'Unknown error')
            print(f"❌ GENERATION FAILED: {error}")
            break
            
        time.sleep(1)
    else:
        print("⏰ Timeout waiting for completion")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main() 