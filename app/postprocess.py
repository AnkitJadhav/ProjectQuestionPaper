import re
import json
from typing import Dict, Any, List, Tuple
import logging


def clean_output(raw_output: str, instructions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and structure the raw LLM output into a standardized format
    
    Args:
        raw_output: Raw text from LLM
        instructions: Original generation instructions
    
    Returns:
        Structured question paper data
    """
    try:
        # Initialize result structure
        result = {
            "title": f"Question Paper - {instructions.get('grade', 'Unknown Grade')}",
            "metadata": {
                "grade": instructions.get('grade', ''),
                "total_marks": instructions.get('total_marks', 100),
                "num_questions": instructions.get('num_questions', 10),
                "generated_at": "",
                "subject": instructions.get('subject', 'General')
            },
            "instructions": [],
            "questions": [],
            "marking_scheme": [],
            "raw_content": raw_output
        }
        
        # Clean the raw output
        cleaned_text = clean_text(raw_output)
        
        # Extract different sections
        sections = parse_sections(cleaned_text)
        
        # Extract title if present
        title = extract_title(cleaned_text)
        if title:
            result["title"] = title
        
        # Extract instructions
        instructions_text = sections.get("instructions", "")
        if instructions_text:
            result["instructions"] = parse_instructions(instructions_text)
        
        # Extract questions
        questions = parse_questions(sections.get("questions", cleaned_text))
        result["questions"] = questions
        
        # Extract marking scheme if present
        marking_scheme = sections.get("marking_scheme", "")
        if marking_scheme:
            result["marking_scheme"] = parse_marking_scheme(marking_scheme)
        
        # Validate and fix mark allocation
        result = validate_and_fix_marks(result, instructions.get('total_marks', 100))
        
        return result
        
    except Exception as e:
        logging.error(f"Error in clean_output: {e}")
        return {
            "title": "Question Paper",
            "metadata": instructions,
            "instructions": ["Error processing output"],
            "questions": [],
            "marking_scheme": [],
            "raw_content": raw_output,
            "error": str(e)
        }


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # Fix common formatting issues
    text = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', text)
    
    return text


def clean_and_structure_output(raw_output: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main function called by worker to clean and structure LLM output
    
    Args:
        raw_output: Raw text from DeepSeek API
        config: Generation configuration (optional)
    
    Returns:
        Structured question paper data ready for PDF generation
    """
    if config is None:
        config = {}
    
    try:
        print(f"✨ Cleaning and structuring LLM output...")
        
        # Use the existing clean_output function
        structured_data = clean_output(raw_output, config)
        
        # Add generation timestamp
        from datetime import datetime
        structured_data["metadata"]["generated_at"] = datetime.now().isoformat()
        
        # Ensure we have the required structure for PDF generation
        if not structured_data.get("questions"):
            # Fallback parsing if questions weren't detected
            structured_data["questions"] = parse_questions_fallback(raw_output)
        
        # Validate the structure
        structured_data = validate_structure(structured_data)
        
        print(f"✅ Structure completed! Found {len(structured_data['questions'])} questions")
        return structured_data
        
    except Exception as e:
        print(f"❌ Error structuring output: {e}")
        # Return minimal structure to prevent crashes
        return {
            "title": "Generated Question Paper",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_marks": config.get("total_marks", 100),
                "error": str(e)
            },
            "instructions": ["Please read all questions carefully."],
            "questions": [],
            "raw_content": raw_output
        }


def parse_questions_fallback(text: str) -> List[Dict[str, Any]]:
    """Fallback question parsing when main parser fails"""
    questions = []
    
    # Simple line-by-line parsing
    lines = text.split('\n')
    current_question = ""
    question_num = 0
    
    for line in lines:
        line = line.strip()
        
        # Check if this looks like a question start
        if re.match(r'^\d+\.', line) or re.match(r'^[Qq]\d+', line):
            # Save previous question if exists
            if current_question:
                question_num += 1
                questions.append({
                    "number": question_num,
                    "text": current_question.strip(),
                    "marks": 5,  # Default marks
                    "type": "short_answer",
                    "parts": []
                })
            
            current_question = line
        elif current_question and line:
            current_question += " " + line
    
    # Don't forget the last question
    if current_question:
        question_num += 1
        questions.append({
            "number": question_num,
            "text": current_question.strip(),
            "marks": 5,
            "type": "short_answer", 
            "parts": []
        })
    
    return questions


def validate_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and fix the structured data"""
    
    # Ensure we have required fields
    if "metadata" not in data:
        data["metadata"] = {}
    
    if "questions" not in data:
        data["questions"] = []
    
    if "instructions" not in data:
        data["instructions"] = ["Answer all questions.", "Time allowed as per instruction."]
    
    # Fix question numbering
    for i, question in enumerate(data["questions"]):
        if "number" not in question:
            question["number"] = i + 1
        if "marks" not in question:
            question["marks"] = 5
        if "type" not in question:
            question["type"] = "short_answer"
    
    return data


def parse_sections(text: str) -> Dict[str, str]:
    """Parse text into different sections"""
    sections = {}
    
    # Common section patterns
    patterns = {
        "instructions": r'(?i)(?:general\s+)?instructions?[:\s]*\n(.*?)(?=\n(?:section|question|part)\s*[a-z]?[:\d]|\nQ\.?\s*\d|$)',
        "questions": r'(?i)(?:questions?|section|part)[:\s]*\n(.*?)(?=marking\s*scheme|answer\s*key|$)',
        "marking_scheme": r'(?i)(?:marking\s*scheme|answer\s*key|solutions?)[:\s]*\n(.*?)$'
    }
    
    for section_name, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            sections[section_name] = match.group(1).strip()
    
    return sections


def extract_title(text: str) -> str:
    """Extract question paper title"""
    # Look for title patterns
    title_patterns = [
        r'^([A-Z][A-Z\s,\-]+(?:EXAMINATION|TEST|PAPER|QUIZ).*?)$',
        r'^(.*?(?:Question\s+Paper|Examination|Test).*?)$',
        r'^([A-Z]{2,}.*?)$'  # All caps first line
    ]
    
    lines = text.split('\n')[:5]  # Check first 5 lines
    
    for line in lines:
        line = line.strip()
        for pattern in title_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return line
    
    return ""


def parse_instructions(instructions_text: str) -> List[str]:
    """Parse instructions into a list"""
    instructions = []
    
    # Split by numbers or bullet points
    parts = re.split(r'\n\s*(?:\d+\.|\-|\*|•)\s*', instructions_text)
    
    for part in parts:
        part = part.strip()
        if part and len(part) > 10:  # Filter out very short fragments
            instructions.append(part)
    
    return instructions


def parse_questions(questions_text: str) -> List[Dict[str, Any]]:
    """Parse questions from text"""
    questions = []
    
    # Pattern to match questions with numbers and marks
    question_pattern = r'(?:^|\n)\s*(?:[Qq]\.?\s*)?(\d+)\.?\s*(.*?)(?=\n\s*(?:[Qq]\.?\s*)?\d+\.|\n\s*$|$)'
    
    matches = re.finditer(question_pattern, questions_text, re.DOTALL)
    
    for match in matches:
        question_num = int(match.group(1))
        question_text = match.group(2).strip()
        
        if not question_text:
            continue
            
        # Extract marks if present
        marks = extract_marks_from_text(question_text)
        
        # Clean question text (remove marks notation)
        clean_question = re.sub(r'\[.*?\d+.*?marks?\]', '', question_text, flags=re.IGNORECASE).strip()
        clean_question = re.sub(r'\(\d+\s*marks?\)', '', clean_question, flags=re.IGNORECASE).strip()
        
        # Detect question type
        question_type = detect_question_type(clean_question)
        
        questions.append({
            "number": question_num,
            "text": clean_question,
            "marks": marks,
            "type": question_type,
            "parts": parse_question_parts(clean_question)
        })
    
    return questions


def extract_marks_from_text(text: str) -> int:
    """Extract marks allocation from question text"""
    # Look for patterns like [5 marks], (10 marks), etc.
    patterns = [
        r'\[(\d+)\s*marks?\]',
        r'\((\d+)\s*marks?\)',
        r'(\d+)\s*marks?',
        r'\[(\d+)\]'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return 1  # Default to 1 mark if not specified


def detect_question_type(question_text: str) -> str:
    """Detect the type of question"""
    text_lower = question_text.lower()
    
    if any(phrase in text_lower for phrase in ['choose', 'select', 'circle', 'tick', 'multiple choice']):
        return "multiple_choice"
    elif any(phrase in text_lower for phrase in ['true or false', 't/f', 'true/false']):
        return "true_false"
    elif any(phrase in text_lower for phrase in ['fill in', 'complete', 'blank']):
        return "fill_blank"
    elif any(phrase in text_lower for phrase in ['explain', 'describe', 'discuss', 'analyze', 'evaluate']):
        return "long_answer"
    elif any(phrase in text_lower for phrase in ['define', 'list', 'name', 'state']):
        return "short_answer"
    elif any(phrase in text_lower for phrase in ['solve', 'calculate', 'find', 'compute']):
        return "problem_solving"
    else:
        return "general"


def parse_question_parts(question_text: str) -> List[str]:
    """Parse multi-part questions"""
    # Look for parts like (a), (b), (i), (ii), etc.
    part_pattern = r'\n?\s*\([a-z]+\)|\n?\s*\([ivx]+\)|\n?\s*[a-z]\)|\n?\s*[ivx]+\)'
    
    parts = re.split(part_pattern, question_text)
    parts = [part.strip() for part in parts if part.strip()]
    
    return parts if len(parts) > 1 else []


def parse_marking_scheme(marking_text: str) -> List[Dict[str, Any]]:
    """Parse marking scheme"""
    scheme = []
    
    # Simple parsing for now
    lines = marking_text.split('\n')
    current_question = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a question reference
        question_match = re.match(r'(?:[Qq]\.?\s*)?(\d+)\.?', line)
        if question_match:
            current_question = int(question_match.group(1))
        
        if current_question and line:
            scheme.append({
                "question": current_question,
                "marking_points": line
            })
    
    return scheme


def validate_and_fix_marks(result: Dict[str, Any], target_marks: int) -> Dict[str, Any]:
    """Validate and fix mark allocation"""
    questions = result.get("questions", [])
    
    if not questions:
        return result
    
    # Calculate current total
    current_total = sum(q.get("marks", 1) for q in questions)
    
    if current_total != target_marks:
        # Redistribute marks proportionally
        if current_total > 0:
            ratio = target_marks / current_total
            remaining = target_marks
            
            for i, question in enumerate(questions):
                if i == len(questions) - 1:  # Last question gets remaining marks
                    question["marks"] = remaining
                else:
                    new_marks = max(1, round(question.get("marks", 1) * ratio))
                    question["marks"] = new_marks
                    remaining -= new_marks
    
    return result


def format_for_pdf(result: Dict[str, Any]) -> str:
    """Format the structured result for PDF generation"""
    lines = []
    
    # Title
    lines.append(result.get("title", "Question Paper"))
    lines.append("=" * len(result.get("title", "Question Paper")))
    lines.append("")
    
    # Metadata
    metadata = result.get("metadata", {})
    lines.append(f"Grade: {metadata.get('grade', '')}")
    lines.append(f"Total Marks: {metadata.get('total_marks', 100)}")
    lines.append(f"Number of Questions: {metadata.get('num_questions', 10)}")
    lines.append("")
    
    # Instructions
    instructions = result.get("instructions", [])
    if instructions:
        lines.append("INSTRUCTIONS:")
        for i, instruction in enumerate(instructions, 1):
            lines.append(f"{i}. {instruction}")
        lines.append("")
    
    # Questions
    questions = result.get("questions", [])
    for question in questions:
        lines.append(f"Q{question.get('number', 1)}. {question.get('text', '')} [{question.get('marks', 1)} marks]")
        lines.append("")
    
    return "\n".join(lines) 