"""
Enhanced Worker for Professional Question Paper Generation
Handles multiple textbooks, chapter weightage, and intelligent question distribution
"""

import os
import sys
import asyncio
import traceback
import uuid
from typing import List, Dict, Any
from collections import defaultdict

# Add app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.retriever import search_by_doc_id
from rag.deepseek_client import chat_async
from schemas import ChapterWeightage, ProfessionalQuestionConfig, QuestionDistributionSummary
from templates.sample_paper_template import (
    SamplePaperTemplate, 
    parse_llm_response_to_questions, 
    validate_question_paper_format
)
from pdf_export import create_question_paper_pdf

# Global job tracking
enhanced_job_status = {}

def update_enhanced_job_progress(job_id: str, progress: int, status: str = "processing", result: Any = None, error: str = None):
    """Update enhanced job progress"""
    enhanced_job_status[job_id] = {
        "progress": progress,
        "status": status,
        "result": result,
        "error": error
    }

def get_enhanced_job_status(job_id: str) -> Dict[str, Any]:
    """Get enhanced job status"""
    return enhanced_job_status.get(job_id, {"progress": 0, "status": "not_found"})

class ProfessionalQuestionGenerator:
    """Professional question generator with multi-source support"""
    
    def __init__(self):
        self.question_types = {
            "definition": ["Define", "What is", "State the definition of"],
            "explanation": ["Explain", "Describe", "Elaborate on", "Discuss"],
            "comparison": ["Compare and contrast", "Differentiate between", "Distinguish between"],
            "application": ["Give examples of", "List applications of", "How is", "Where is"],
            "analysis": ["Analyze", "Evaluate", "Assess", "Critically examine"]
        }
    
    def calculate_question_distribution(self, chapter_weightages: List[ChapterWeightage], config: ProfessionalQuestionConfig) -> Dict[str, Dict]:
        """Calculate how many questions to generate from each chapter"""
        
        total_weightage = sum(ch.weightage_percentage for ch in chapter_weightages)
        if total_weightage != 100:
            # Normalize weightages to 100%
            for ch in chapter_weightages:
                ch.weightage_percentage = int((ch.weightage_percentage / total_weightage) * 100)
        
        distribution = {}
        remaining_questions = config.total_questions
        
        for i, chapter in enumerate(chapter_weightages):
            if i == len(chapter_weightages) - 1:  # Last chapter gets remaining questions
                questions_count = remaining_questions
            else:
                questions_count = int((chapter.weightage_percentage / 100) * config.total_questions)
                remaining_questions -= questions_count
            
            distribution[chapter.document_id] = {
                "questions": max(1, questions_count),  # Ensure at least 1 question per chapter
                "chapter_name": chapter.chapter_name,
                "weightage": chapter.weightage_percentage,
                "focus_topics": chapter.focus_topics,
                "difficulty": chapter.difficulty_level
            }
        
        return distribution
    
    def get_diverse_content_from_chapter(self, document_id: str, chapter_info: Dict, questions_needed: int) -> List[Dict]:
        """Get diverse content from a specific chapter"""
        
        # Base search queries for comprehensive coverage
        base_queries = [
            "definition concept theory",
            "properties characteristics features",
            "applications uses examples",
            "process method procedure",
            "classification types categories"
        ]
        
        # Add focus topics if specified
        if chapter_info.get("focus_topics"):
            base_queries.extend(chapter_info["focus_topics"])
        
        all_chunks = []
        for query in base_queries:
            chunks = search_by_doc_id(query, document_id, k=3)
            all_chunks.extend(chunks)
        
        # Remove duplicates and select diverse content
        seen_texts = set()
        unique_chunks = []
        for chunk in all_chunks:
            text_key = chunk.get('text', '')[:100]  # First 100 chars as key
            if text_key not in seen_texts and len(chunk.get('text', '')) > 50:
                seen_texts.add(text_key)
                unique_chunks.append(chunk)
        
        return unique_chunks[:max(questions_needed * 2, 10)]

async def generate_professional_question_paper(
    chapter_weightages: List[ChapterWeightage],
    sample_paper_id: str,
    config: ProfessionalQuestionConfig,
    special_instructions: str = None
) -> str:
    """Generate professional question paper from multiple textbook sources"""
    
    job_id = str(uuid.uuid4())[:8]
    generator = ProfessionalQuestionGenerator()
    
    try:
        print(f"🚀 Starting professional question paper generation (Job: {job_id})")
        print(f"📚 Sources: {len(chapter_weightages)} chapters")
        update_enhanced_job_progress(job_id, 5)
        
        # Calculate question distribution
        question_distribution = generator.calculate_question_distribution(chapter_weightages, config)
        
        print("📋 Question Distribution:")
        for doc_id, info in question_distribution.items():
            print(f"  • {info['chapter_name']}: {info['questions']} questions ({info['weightage']}%)")
        
        update_enhanced_job_progress(job_id, 15)
        
        # Get sample paper format
        sample_chunks = search_by_doc_id("question paper format", sample_paper_id, k=10)
        if not sample_chunks:
            raise Exception("Could not retrieve sample paper format")
        
        update_enhanced_job_progress(job_id, 25)
        
        # Generate questions from each chapter
        all_questions = []
        sources_used = []
        
        for doc_id, chapter_info in question_distribution.items():
            questions_needed = chapter_info["questions"]
            
            print(f"  📖 Processing {chapter_info['chapter_name']} ({questions_needed} questions)...")
            
            # Get content from this chapter
            content_chunks = generator.get_diverse_content_from_chapter(doc_id, chapter_info, questions_needed)
            
            if not content_chunks:
                print(f"  ⚠️ No content found for {chapter_info['chapter_name']}, skipping...")
                continue
            
            # Build prompt for this chapter
            content_text = "\n".join([
                f"Content {i+1}: {chunk.get('text', '')[:400]}"
                for i, chunk in enumerate(content_chunks[:10])
            ])
            
            focus_instruction = ""
            if chapter_info.get("focus_topics"):
                focus_instruction = f"Focus on: {', '.join(chapter_info['focus_topics'])}"
            
            prompt = f"""Generate exactly {questions_needed} university-level questions based on this textbook content.

### TEXTBOOK CONTENT - {chapter_info['chapter_name']}:
{content_text}

### REQUIREMENTS:
- Generate exactly {questions_needed} questions
- Each question answerable in 75-100 words
- Use academic language appropriate for university students
- Questions should test understanding, not memorization
{focus_instruction}

### OUTPUT FORMAT:
List {questions_needed} questions numbered 1-{questions_needed}, one per line.
Do NOT include explanations or answers.

Generate the questions:"""
            
            # Generate questions with LLM
            try:
                raw_response = await chat_async(prompt)
                chapter_questions = parse_llm_response_to_questions(raw_response)
                chapter_questions = chapter_questions[:questions_needed]
                all_questions.extend(chapter_questions)
                
                # Track source usage
                sources_used.append(QuestionDistributionSummary(
                    source_name=chapter_info['chapter_name'],
                    document_id=doc_id,
                    questions_generated=len(chapter_questions),
                    weightage_applied=chapter_info['weightage'],
                    topics_covered=chapter_info.get('focus_topics', [])
                ))
                
                print(f"  ✅ Generated {len(chapter_questions)} questions")
                
            except Exception as e:
                print(f"  ❌ Error generating questions: {e}")
                continue
        
        update_enhanced_job_progress(job_id, 70)
        
        # Ensure we have enough questions
        if len(all_questions) < config.total_questions * 0.8:
            raise Exception(f"Only generated {len(all_questions)} questions, need at least {int(config.total_questions * 0.8)}")
        
        # Trim to exact number needed
        all_questions = all_questions[:config.total_questions]
        
        print(f"✅ Generated {len(all_questions)} total questions from {len(sources_used)} sources")
        update_enhanced_job_progress(job_id, 80)
        
        # Apply to template
        template = SamplePaperTemplate()
        formatted_paper = template.create_question_paper(all_questions)
        
        # Validate format
        checks, is_valid = validate_question_paper_format(formatted_paper)
        print(f"✅ Template applied. Format valid: {is_valid}")
        
        update_enhanced_job_progress(job_id, 90)
        
        # Create PDF
        structured_data = {
            "title": f"Professional Multi-Chapter Question Paper",
            "metadata": {
                "total_marks": config.total_marks,
                "num_questions": 4,
                "academic_level": config.academic_level,
                "sources_count": len(sources_used)
            },
            "instructions": [
                "All Questions are Compulsory.",
                f"Each Sub-question carry {config.marks_per_question} marks.",
                f"Each Sub-question should be answered between {config.word_limit_min} to {config.word_limit_max} words.",
                f"Question paper of {config.total_marks} Marks, it will be converted in to your programme structure marks."
            ],
            "raw_content": formatted_paper,
            "individual_questions": all_questions,
            "sources_used": [source.dict() for source in sources_used],
            "special_instructions": special_instructions
        }
        
        output_filename = f"professional_paper_{job_id}.pdf"
        pdf_path = create_question_paper_pdf(structured_data, output_filename)
        
        if not os.path.exists(pdf_path):
            raise Exception("PDF file was not created successfully")
        
        # Calculate quality metrics
        quality_metrics = {
            "sources_covered": len(sources_used),
            "total_questions": len(all_questions),
            "average_question_length": sum(len(q.split()) for q in all_questions) / len(all_questions)
        }
        
        update_enhanced_job_progress(job_id, 100, "completed", {
            "pdf_filename": output_filename,
            "total_questions": len(all_questions),
            "total_marks": config.total_marks,
            "sources_used": [source.dict() for source in sources_used],
            "format_validated": checks,
            "template_applied": is_valid,
            "quality_metrics": quality_metrics,
            "chapter_distribution": question_distribution
        })
        
        print(f"✅ Professional question paper generated: {output_filename}")
        
    except Exception as e:
        error_msg = f"Error generating professional question paper: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        update_enhanced_job_progress(job_id, 0, "failed", None, error_msg)
    
    return job_id

if __name__ == "__main__":
    print("🧪 Enhanced Professional Question Paper Generation System")
    print("🚀 Ready for multi-chapter question generation with weightage!") 