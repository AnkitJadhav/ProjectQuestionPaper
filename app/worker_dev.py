#!/usr/bin/env python3
"""
Development worker that processes tasks in-memory without Redis/Celery
"""

import os
import sys
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import json
import traceback

# Add app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.retriever import search_by_doc_id, hybrid_search
from rag.deepseek_client import chat_async
from rag.prompt_builder import build_question_generation_prompt
from templates.sample_paper_template import (
    SamplePaperTemplate, 
    parse_llm_response_to_questions, 
    validate_question_paper_format
)
from postprocess import clean_and_structure_output
from pdf_export import create_question_paper_pdf

# Global job tracking
job_status = {}
job_results = {}

def create_job(task_name: str, **kwargs) -> str:
    """Create a new job and return job ID"""
    job_id = str(uuid.uuid4())
    job_status[job_id] = {
        "id": job_id,
        "task": task_name,
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "progress": 0,
        "result": None,
        "error": None,
        "kwargs": kwargs
    }
    return job_id

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get job status"""
    return job_status.get(job_id, {"progress": 0, "status": "not_found"})

def update_job_progress(job_id: str, progress: int, status: str = "processing", result: Any = None, error: str = None):
    """Update job progress"""
    job_status[job_id] = {
        "progress": progress,
        "status": status,
        "result": result,
        "error": error
    }

def ingest_pdf(file_path: str, doc_id: str, doc_type: str) -> str:
    """Process PDF ingestion"""
    job_id = create_job("ingest_pdf", file_path=file_path, doc_id=doc_id, doc_type=doc_type)
    
    try:
        # Import here to avoid issues if not available
        from .ingest.pdf_reader import read_pdf_streaming
        from .ingest.chunker import chunk_text
        from .ingest.embedder import get_embeddings
        from .deps import add_to_index, update_document_status
        
        update_job_progress(job_id, 10, "processing")
        
        # Read PDF
        print(f"📖 Reading PDF: {file_path}")
        text = read_pdf_streaming(file_path)
        update_job_progress(job_id, 30)
        
        # Chunk text
        print(f"✂️ Chunking text into segments...")
        chunks = chunk_text(text)
        update_job_progress(job_id, 50)
        
        # Generate embeddings
        print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
        embeddings = get_embeddings([chunk["text"] for chunk in chunks])
        update_job_progress(job_id, 80)
        
        # Add to vector database
        print(f"💾 Adding to vector database...")
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            add_to_index(
                embedding=embedding,
                text=chunk["text"],
                metadata={
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "chunk_id": f"{doc_id}_{i}",
                    "page": chunk.get("page", 0)
                }
            )
        
        # Update document status
        update_document_status(doc_id, "completed")
        update_job_progress(job_id, 100, "completed", f"Successfully processed {len(chunks)} chunks")
        print(f"✅ PDF ingestion completed: {doc_id}")
        
    except Exception as e:
        error_msg = f"Error processing PDF: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        update_job_progress(job_id, 0, "failed", None, error_msg)
        
        # Update document status
        try:
            from .deps import update_document_status
            update_document_status(doc_id, "failed")
        except:
            pass
    
    return job_id

def generate_question_paper(textbook_ids: list, sample_paper_id: str, config: dict) -> str:
    """
    Generate question paper using template system with individual question generation
    """
    job_id = str(uuid.uuid4())[:8]  # Short ID for filename
    
    try:
        print(f"🚀 Starting question paper generation (Job: {job_id})")
        update_job_progress(job_id, 10)
        
        # Step 1: Get sample paper format (for reference, not direct use)
        print(f"📋 Retrieving sample paper format...")
        sample_chunks = search_by_doc_id(
            "question paper format structure instructions marks time",
            sample_paper_id,
            k=10
        )
        
        if not sample_chunks:
            raise Exception("Could not retrieve sample paper format")
        
        # Combine sample paper text
        sample_paper_text = "\n".join([chunk.get('text', '') for chunk in sample_chunks])
        print(f"✅ Sample paper format retrieved ({len(sample_paper_text)} characters)")
        
        update_job_progress(job_id, 25)
        
        # Step 2: Get textbook content
        print(f"📚 Retrieving textbook content from {len(textbook_ids)} documents...")
        textbook_chunks = []
        
        for doc_id in textbook_ids:
            # Get diverse content from each textbook using multiple queries
            queries = [
                'chemistry',
                'atoms',
                'molecules', 
                'elements',
                'compounds',
                'reactions'
            ]
            
            for query in queries:
                chunks = search_by_doc_id(query, doc_id, k=3)
                textbook_chunks.extend(chunks)
            
            # Remove duplicates based on text content
            seen_texts = set()
            unique_chunks = []
            for chunk in textbook_chunks:
                text = chunk.get('text', '')[:100]  # First 100 chars as key
                if text not in seen_texts:
                    seen_texts.add(text)
                    unique_chunks.append(chunk)
            textbook_chunks = unique_chunks
        
        if not textbook_chunks:
            raise Exception("Could not retrieve textbook content")
        
        print(f"✅ Retrieved {len(textbook_chunks)} content chunks from textbooks")
        update_job_progress(job_id, 40)
        
        # Step 3: Build prompt for individual question generation
        print(f"🎯 Building question generation prompt...")
        prompt = build_question_generation_prompt(textbook_chunks, sample_paper_text, config)
        
        print(f"✅ Prompt built ({len(prompt)} characters)")
        update_job_progress(job_id, 55)
        
        # Step 4: Generate individual questions with LLM
        print(f"🤖 Generating individual questions with DeepSeek...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            raw_response = loop.run_until_complete(chat_async(prompt))
        finally:
            loop.close()
        
        if not raw_response or len(raw_response.strip()) < 100:
            raise Exception("LLM generated insufficient content")
        
        print(f"✅ LLM response received ({len(raw_response)} characters)")
        update_job_progress(job_id, 70)
        
        # Step 5: Parse individual questions from LLM response
        print(f"📝 Parsing individual questions from response...")
        questions_list = parse_llm_response_to_questions(raw_response)
        
        if len(questions_list) < 15:
            raise Exception(f"Only {len(questions_list)} questions extracted, need at least 15")
        
        print(f"✅ Extracted {len(questions_list)} questions")
        update_job_progress(job_id, 80)
        
        # Step 6: Apply questions to template
        print(f"🎨 Applying questions to sample paper template...")
        template = SamplePaperTemplate()
        formatted_paper = template.create_question_paper(questions_list)
        
        # Validate the formatted paper
        checks, is_valid = validate_question_paper_format(formatted_paper)
        print(f"✅ Template applied. Format valid: {is_valid}")
        print(f"   Format checks: {checks}")
        
        update_job_progress(job_id, 90)
        
        # Step 7: Create structured data for PDF
        print(f"📄 Creating PDF...")
        structured_data = {
            "title": "Chemistry Question Paper",
            "metadata": {
                "total_marks": 80,
                "num_questions": 4,
                "generated_at": "",
                "subject": "Chemistry"
            },
            "instructions": [
                "All Questions are Compulsory.",
                "Each Sub-question carry 5 marks.",
                "Each Sub-question should be answered between 75 to 100 words.",
                "Question paper of 80 Marks, it will be converted in to your programme structure marks."
            ],
            "questions": [],
            "raw_content": formatted_paper,  # This will be used by the new PDF system
            "individual_questions": questions_list
        }
        
        output_filename = f"question_paper_{job_id}.pdf"
        pdf_path = create_question_paper_pdf(structured_data, output_filename)
        
        # Verify PDF was created
        if not os.path.exists(pdf_path):
            raise Exception("PDF file was not created successfully")
        
        update_job_progress(job_id, 100, "completed", {
            "pdf_filename": output_filename,
            "json_data": structured_data,
            "total_questions": 20,  # 4 main questions × 5 sub-questions each
            "total_marks": 80,
            "format_validated": checks,
            "questions_extracted": len(questions_list),
            "template_applied": is_valid
        })
        
        print(f"✅ Question paper generated successfully: {output_filename}")
        
    except Exception as e:
        error_msg = f"Error generating question paper: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        update_job_progress(job_id, 0, "failed", None, error_msg)
    
    return job_id

def validate_generated_format(paper_text: str) -> Dict[str, bool]:
    """Validate that the generated paper follows the correct format"""
    import re
    
    checks = {
        "has_correct_marks": bool(re.search(r'Marks\s*:\s*80', paper_text)),
        "has_correct_time": bool(re.search(r'Time\s*:\s*3\s*Hours', paper_text)),
        "has_main_questions": len(re.findall(r'\d+\.\s*Solve any four', paper_text)) >= 3,
        "has_sub_questions": len(re.findall(r'[a-e]\)', paper_text)) >= 15,
        "has_instructions": bool(re.search(r'Instructions\s*:', paper_text)),
        "has_pto": bool(re.search(r'\(P\.T\.O\.\)', paper_text)),
        "has_proper_ending": bool(re.search(r'sssssss', paper_text))
    }
    
    return checks

def test_template_system():
    """Test the new template system"""
    try:
        print("🧪 Testing Template System...")
        
        from templates.sample_paper_template import test_template_system
        paper, is_valid = test_template_system()
        
        if is_valid:
            print("✅ Template system test passed!")
            print(f"Generated paper length: {len(paper)} characters")
            print(f"First 300 chars: {paper[:300]}...")
        else:
            print("❌ Template system test failed!")
            
        return is_valid
        
    except Exception as e:
        print(f"❌ Template system test error: {e}")
        return False

def test_question_parsing():
    """Test question parsing functionality"""
    try:
        print("🧪 Testing Question Parsing...")
        
        sample_llm_response = """
        1. Define an element according to Antoine Lavoisier
        2. What are the physical states of elements at room temperature
        3. Differentiate between metals and non-metals based on their properties
        4. Explain why the properties of a compound differ from its constituent elements
        5. Describe the characteristics of mercury as a metal
        6. Compare and contrast mixtures and compounds
        7. Explain the significance of fixed proportions in compounds
        8. How does a chemical change differ from a physical change
        9. What happens when iron and sulphur are heated together
        10. Why are the properties of a mixture similar to its constituents
        11. What is a pure substance and how is it classified
        12. Explain the term dispersion in chemistry
        13. Describe the process of crystallization
        14. What are the different types of solutions
        15. Explain the concept of solubility
        16. Define concentration and its units
        17. What is the difference between homogeneous and heterogeneous mixtures
        18. Describe the methods of separation of mixtures
        19. Explain the law of conservation of mass
        20. What are the applications of chemistry in daily life
        """
        
        questions = parse_llm_response_to_questions(sample_llm_response)
        
        print(f"✅ Parsed {len(questions)} questions")
        print("Sample questions:")
        for i, q in enumerate(questions[:5]):
            print(f"  {i+1}. {q}")
        
        return len(questions) >= 15
        
    except Exception as e:
        print(f"❌ Question parsing test error: {e}")
        return False

def test_sample_paper_extraction():
    """Test function to verify sample paper extraction works"""
    try:
        # Test with a known sample paper
        sample_chunks = search_by_doc_id(
            "question paper format structure",
            "d43b5ceb-063a-4832-a072-3939ca2451fc",  # Sample paper ID
            k=5
        )
        
        if sample_chunks:
            sample_text = "\n".join([chunk.get('text', '') for chunk in sample_chunks])
            print("✅ Sample paper extraction test successful")
            print(f"Sample text length: {len(sample_text)}")
            print(f"First 200 chars: {sample_text[:200]}")
            return True
        else:
            print("❌ No sample chunks found")
            return False
            
    except Exception as e:
        print(f"❌ Sample paper extraction test failed: {e}")
        return False

def test_textbook_content_extraction():
    """Test function to verify textbook content extraction works"""
    try:
        # Test with a known textbook
        textbook_chunks = search_by_doc_id(
            "chemistry",
            "ecf456a9-656e-4ee3-abe1-a9a7678d0a11",  # Textbook ID
            k=5
        )
        
        if textbook_chunks:
            print("✅ Textbook content extraction test successful")
            print(f"Found {len(textbook_chunks)} chunks")
            for i, chunk in enumerate(textbook_chunks[:2]):
                print(f"Chunk {i+1}: {chunk.get('text', '')[:100]}...")
            return True
        else:
            print("❌ No textbook chunks found")
            return False
            
    except Exception as e:
        print(f"❌ Textbook content extraction test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Improved Question Paper Generation System...")
    print("=" * 60)
    
    # Test all components
    tests = [
        ("Template System", test_template_system),
        ("Question Parsing", test_question_parsing),
        ("Sample Paper Extraction", test_sample_paper_extraction),
        ("Textbook Content Extraction", test_textbook_content_extraction)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    for test_name, result in results:
        print(f"  {'✅' if result else '❌'} {test_name}")
    
    all_passed = all(result for _, result in results)
    print(f"\n🏁 Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🚀 System ready for question paper generation!")
    else:
        print("\n⚠️ Please fix failing tests before proceeding.") 