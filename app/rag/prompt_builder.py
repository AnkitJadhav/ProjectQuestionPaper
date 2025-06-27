from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SYS_TEMPLATE = """You are an expert examiner creating individual questions based on textbook content."""


ENHANCED_TEMPLATE = SYS_TEMPLATE


def build_prompt(instr: Dict[str, Any], structure_chunks: List[Dict], subject_chunks: List[Dict], template_type: str = "basic") -> str:
    """
    Legacy function - redirects to new template system
    """
    sample_text = "\n".join([chunk.get('text', '') for chunk in structure_chunks[:5]])
    
    if not sample_text.strip():
        # Use default template if no sample found
        sample_text = """May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024
Time : 3 Hours Marks : 80
Instructions :1. All Questions are Compulsory.2. Each Sub-question carry 5 marks.
3. Each Sub-question should be answered between 75 to 100 words."""
    
    return build_question_generation_prompt(subject_chunks, sample_text, instr)


def build_question_generation_prompt(textbook_chunks: List[Dict], sample_paper_text: str, config: Dict[str, Any]) -> str:
    """
    Build a prompt to generate individual questions that will be used with the template system
    """
    
    # Extract textbook content for question generation
    textbook_content = "\n".join([
        f"Content {i+1}: {chunk.get('text', '')[:400]}"
        for i, chunk in enumerate(textbook_chunks[:20])
    ])
    
    prompt = f"""You are a professional examination paper setter. Your task is to generate exactly 20 individual questions based on the textbook content provided.

### 📚 TEXTBOOK CONTENT FOR QUESTIONS:
{textbook_content}

### 🎯 REQUIREMENTS:

1. **QUESTION COUNT**: Generate exactly 20 questions
2. **QUESTION CONTENT**: 
   - ALL questions must be based on the provided textbook content
   - Questions should be appropriate for university-level chemistry students
   - Each question should be answerable in 75-100 words
   - Make questions clear, specific, and educational

3. **QUESTION TYPES TO CREATE**:
   - Definitions and explanations (e.g., "Define an element according to...")
   - Short descriptions of concepts (e.g., "Describe the characteristics of...")
   - Brief notes on topics (e.g., "Write a note on...")
   - Comparisons between concepts (e.g., "Compare and contrast...")
   - Applications and examples (e.g., "Explain with examples...")

4. **OUTPUT FORMAT**:
   - List exactly 20 questions, numbered 1-20
   - Each question on a separate line
   - No sub-parts or options
   - No marks allocation (will be added by template)
   - No additional formatting or explanations

### 📝 EXAMPLE FORMAT:
1. Define an element according to Antoine Lavoisier
2. What are the physical states of elements at room temperature
3. Differentiate between metals and non-metals based on their properties
...
20. What are the applications of chemistry in daily life

### ⚠️ OUTPUT INSTRUCTIONS:
Generate ONLY the numbered list of 20 questions. Do NOT include any explanations, answers, or additional text.

**Generate the 20 questions now:**"""

    return prompt


def build_exact_format_prompt(textbook_chunks: List[Dict], sample_paper_text: str, config: Dict[str, Any]) -> str:
    """
    Legacy function - redirects to new question generation approach
    """
    return build_question_generation_prompt(textbook_chunks, sample_paper_text, config)


def build_question_generation_prompt_simple(textbook_chunks: List[Dict], topic_focus: str = "") -> str:
    """
    Generate individual questions from textbook content with simpler approach
    """
    
    content_text = "\n".join([
        f"• {chunk.get('text', '')[:300]}"
        for chunk in textbook_chunks[:15]
    ])
    
    focus_instruction = f"Focus particularly on: {topic_focus}" if topic_focus else ""
    
    prompt = f"""Generate exactly 20 short-answer questions based on the following textbook content. Each question should be answerable in 75-100 words.

### TEXTBOOK CONTENT:
{content_text}

### REQUIREMENTS:
- Create questions that test understanding of the content
- Questions should be suitable for university-level students
- Each question should be clear and specific
- Mix different types: definitions, explanations, comparisons, applications
{focus_instruction}

### FORMAT:
Generate exactly 20 questions, numbered 1-20, one per line.

Questions:"""

    return prompt


def build_review_prompt(question_paper: str, requirements: Dict[str, Any]) -> str:
    """Build a prompt for reviewing and improving a generated question paper"""
    
    return f"""Please review this question paper and suggest improvements:

### ORIGINAL QUESTION PAPER:
{question_paper}

### REQUIREMENTS:
- Grade: {requirements.get('grade', 'Not specified')}
- Total Marks: {requirements.get('total_marks', 100)}
- Number of Questions: {requirements.get('num_questions', 10)}

### REVIEW CRITERIA:
1. Are the questions appropriate for the grade level?
2. Do the marks add up to the required total?
3. Is there good variety in question types?
4. Are the instructions clear?
5. Is the difficulty progression appropriate?

### PROVIDE:
1. Overall assessment (Good/Needs Improvement)
2. Specific issues found
3. Suggested improvements
4. Revised question paper (if major changes needed)

Begin your review:"""


def build_generation_prompt(textbook_content: List[Dict], sample_format: List[Dict], config: Dict[str, Any]) -> str:
    """
    Build the main prompt for professional question paper generation
    """
    sample_text = "\n".join([chunk.get('text', '') for chunk in sample_format[:10]])
    
    return build_question_generation_prompt(textbook_content, sample_text, config)


def extract_paper_structure(sample_text: str) -> str:
    """
    Analyze sample paper to extract key structural elements
    """
    analysis = []
    
    if "80" in sample_text and "marks" in sample_text.lower():
        analysis.append("• 80 marks total")
    
    if "3 hours" in sample_text.lower():
        analysis.append("• 3 hours duration")
    
    if "solve any four" in sample_text.lower():
        analysis.append("• 4 main questions with sub-questions")
    
    if any(letter in sample_text for letter in ['a)', 'b)', 'c)', 'd)', 'e)']):
        analysis.append("• Sub-questions in a), b), c), d), e) format")
    
    return "\n".join(analysis) if analysis else "• Standard format detected"


def analyze_sample_paper_precisely(sample_text: str) -> str:
    """
    Perform detailed analysis of sample paper structure for exact replication
    """
    import re
    
    analysis_parts = []
    
    # Check for 80 marks
    if re.search(r'Marks\s*:\s*80', sample_text):
        analysis_parts.append("📊 **MARKS**: Exactly 80 marks total")
    
    # Check for 3 hours
    if re.search(r'Time\s*:\s*3\s*Hours', sample_text):
        analysis_parts.append("⏰ **TIME**: Exactly 3 hours")
    
    # Check for main question pattern
    main_questions = re.findall(r'(\d+)\.\s*Solve any four', sample_text)
    if main_questions:
        analysis_parts.append(f"🔢 **STRUCTURE**: {len(main_questions)} main questions")
    
    # Check for sub-questions
    sub_questions = re.findall(r'[a-e]\)', sample_text)
    if sub_questions:
        analysis_parts.append(f"📝 **SUB-QUESTIONS**: {len(sub_questions)} sub-questions found")
    
    # Check for specific instructions
    if "75 to 100 words" in sample_text:
        analysis_parts.append("📋 **WORD LIMIT**: 75-100 words per answer")
    
    if "Each Sub-question carry 5 marks" in sample_text:
        analysis_parts.append("💯 **MARKING**: 5 marks per sub-question")
    
    return "\n".join(analysis_parts) if analysis_parts else "⚠️ **ANALYSIS**: Standard format detected"


def analyze_difficulty_distribution(total_marks: int, num_questions: int, grade: str) -> str:
    """
    Analyze optimal difficulty distribution for the given parameters
    """
    avg_marks_per_question = total_marks / num_questions
    
    analysis = f"""
**Difficulty Distribution Analysis:**

• Average marks per question: {avg_marks_per_question:.1f}
• Grade level: {grade}

**Recommended Distribution:**
"""
    
    if avg_marks_per_question <= 3:
        analysis += """
• Focus: 70% Knowledge/Understanding, 20% Application, 10% Analysis
• Question types: Mostly short answers, definitions, simple calculations
• Time per question: 2-5 minutes average
"""
    elif avg_marks_per_question <= 6:
        analysis += """
• Focus: 40% Knowledge/Understanding, 40% Application, 20% Analysis
• Question types: Mix of short and medium answers, problem solving
• Time per question: 5-10 minutes average
"""
    elif avg_marks_per_question <= 10:
        analysis += """
• Focus: 30% Understanding, 40% Application, 30% Analysis/Evaluation
• Question types: Medium to long answers, complex problem solving
• Time per question: 10-15 minutes average
"""
    else:
        analysis += """
• Focus: 20% Understanding, 30% Application, 50% Analysis/Evaluation/Creation
• Question types: Long answers, essays, comprehensive problem solving
• Time per question: 15+ minutes average
"""
    
    return analysis


def build_marking_scheme_prompt(question_paper: str) -> str:
    """Build a prompt for generating a detailed marking scheme"""
    
    return f"""Create a detailed marking scheme for this question paper:

### QUESTION PAPER:
{question_paper}

### MARKING SCHEME REQUIREMENTS:
1. Each sub-question carries 5 marks
2. Provide point-wise marking for each question
3. Include key points that must be covered
4. Suggest partial marking criteria
5. List common mistakes to watch for

Generate the complete marking scheme:""" 