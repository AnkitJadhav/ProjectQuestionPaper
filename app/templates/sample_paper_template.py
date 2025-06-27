"""
Improved Sample Paper Template System
Uses placeholders to preserve exact formatting while replacing questions
"""

class SamplePaperTemplate:
    """Template for exact sample paper format replication with placeholders"""
    
    # Exact template based on the sample paper structure
    TEMPLATE_80_MARKS = """May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - {paper_code}

Time : 3 Hours Marks : 80

Instructions :1. All Questions are Compulsory.2. Each Sub-question carry 5 marks.
3. Each Sub-question should be answered between 75 to 100 words. Write every questions
answer on separate page.
4. Question paper of 80 Marks, it will be converted in to your programme structure marks.

1. Solve any four sub-questions.
a) {Q1_A} 5
b) {Q1_B} 5
c) {Q1_C} 5
d) {Q1_D} 5
e) {Q1_E} 5

2. Solve any four sub-questions.
a) {Q2_A} 5
b) {Q2_B} 5
c) {Q2_C} 5
d) {Q2_D} 5
e) {Q2_E} 5

(P.T.O.)

3. Solve any four sub-questions.
a) {Q3_A} 5
b) {Q3_B} 5
c) {Q3_C} 5
d) {Q3_D} 5
e) {Q3_E} 5

4. Solve any four sub-questions.
a) {Q4_A} 5
b) {Q4_B} 5
c) {Q4_C} 5
d) {Q4_D} 5
e) {Q4_E} 5

sssssss"""

    @staticmethod
    def generate_paper_code():
        """Generate a paper code similar to the sample"""
        import datetime
        import random
        
        current_date = datetime.datetime.now()
        code_suffix = f"T97/BMG{random.randint(301, 399)}/EE/{current_date.strftime('%Y%m%d')}"
        return f"MaKA{current_date.strftime('%y')}-{random.randint(2000, 2999)} {code_suffix} : 1{code_suffix}"
    
    @classmethod
    def create_question_paper(cls, questions_list):
        """
        Create a complete question paper using placeholders
        
        Args:
            questions_list: List of 20 questions (will be organized into 4 sets of 5)
        
        Returns:
            Formatted question paper string
        """
        if len(questions_list) < 20:
            # Pad with placeholder questions if needed
            questions_list.extend([f"Question {i+1} placeholder"] * (20 - len(questions_list)))
        
        paper_code = cls.generate_paper_code()
        
        # Create replacement dictionary
        replacements = {
            'paper_code': paper_code
        }
        
        # Organize questions into 4 sets of 5
        for q_set in range(1, 5):  # Q1, Q2, Q3, Q4
            for sub_q in range(5):  # A, B, C, D, E
                question_index = (q_set - 1) * 5 + sub_q
                sub_letter = chr(ord('A') + sub_q)  # A, B, C, D, E
                placeholder_key = f"Q{q_set}_{sub_letter}"
                
                if question_index < len(questions_list):
                    replacements[placeholder_key] = questions_list[question_index].strip()
                else:
                    replacements[placeholder_key] = f"Question {question_index + 1} placeholder"
        
        # Replace all placeholders in the template
        formatted_paper = cls.TEMPLATE_80_MARKS
        for key, value in replacements.items():
            formatted_paper = formatted_paper.replace(f"{{{key}}}", value)
        
        return formatted_paper


def extract_questions_from_sample(sample_text):
    """
    Extract existing questions from sample paper to understand the pattern
    """
    import re
    
    # Find all sub-questions (a), b), c), d), e) patterns
    question_pattern = r'[a-e]\)\s*([^0-9\n]+?)(?=\s*5\s*[a-e]\)|\s*5\s*$|\s*5\s*\(P\.T\.O\.\))'
    matches = re.findall(question_pattern, sample_text, re.DOTALL)
    
    # Clean up the matches
    questions = []
    for match in matches:
        cleaned = re.sub(r'\s+', ' ', match.strip())
        if cleaned and len(cleaned) > 10:  # Filter out very short matches
            questions.append(cleaned)
    
    return questions


def validate_question_paper_format(paper_text):
    """Validate that generated paper follows the correct format"""
    import re
    
    checks = {
        "has_marks_80": bool(re.search(r'Marks\s*:\s*80', paper_text)),
        "has_time_3_hours": bool(re.search(r'Time\s*:\s*3\s*Hours', paper_text)),
        "has_4_main_questions": len(re.findall(r'^\d+\.\s*Solve any four', paper_text, re.MULTILINE)) == 4,
        "has_20_sub_questions": len(re.findall(r'^[a-e]\)', paper_text, re.MULTILINE)) == 20,
        "has_instructions": bool(re.search(r'Instructions\s*:', paper_text)),
        "has_pto": bool(re.search(r'\(P\.T\.O\.\)', paper_text)),
        "has_proper_ending": bool(re.search(r'sssssss', paper_text)),
        "no_placeholders": not bool(re.search(r'\{[^}]+\}', paper_text))  # Ensure no unreplaced placeholders
    }
    
    return checks, all(checks.values())


def create_paper_from_questions(questions_list):
    """
    Main function to create a properly formatted question paper
    
    Args:
        questions_list: List of 20 questions
    
    Returns:
        Formatted question paper string
    """
    template = SamplePaperTemplate()
    return template.create_question_paper(questions_list)


def parse_llm_response_to_questions(llm_response):
    """
    Parse LLM response to extract individual questions
    
    Args:
        llm_response: Raw response from LLM
    
    Returns:
        List of 20 individual questions
    """
    import re
    
    # Try to extract questions from various formats
    questions = []
    
    # Method 1: Look for numbered questions (1. 2. 3. etc.)
    numbered_pattern = r'(?:^|\n)\s*\d+\.\s*([^0-9\n]+?)(?=\n\s*\d+\.|\n\s*$|$)'
    numbered_matches = re.findall(numbered_pattern, llm_response, re.MULTILINE | re.DOTALL)
    
    if len(numbered_matches) >= 15:  # If we found a good number of questions
        questions.extend([q.strip() for q in numbered_matches[:20]])
    
    # Method 2: Look for sub-questions pattern a), b), c)
    if len(questions) < 20:
        sub_question_pattern = r'[a-e]\)\s*([^a-e\n]+?)(?=\s*[a-e]\)|\s*\d+\.|\s*$)'
        sub_matches = re.findall(sub_question_pattern, llm_response, re.DOTALL)
        
        if len(sub_matches) >= 15:
            questions = [q.strip() for q in sub_matches[:20]]
    
    # Method 3: Fallback - split by sentences and take meaningful ones
    if len(questions) < 20:
        sentences = re.split(r'[.!?]+', llm_response)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and '?' in s]
        questions.extend(meaningful_sentences[:20])
    
    # Ensure we have exactly 20 questions
    while len(questions) < 20:
        questions.append(f"Generated question {len(questions) + 1}")
    
    return questions[:20]


# Test function
def test_template_system():
    """Test the template system with sample questions"""
    sample_questions = [
        "Define an element according to Antoine Lavoisier",
        "What are the physical states of elements at room temperature",
        "Differentiate between metals and non-metals based on their properties",
        "Explain why the properties of a compound differ from its constituent elements",
        "Describe the characteristics of mercury as a metal",
        "Compare and contrast mixtures and compounds",
        "Explain the significance of fixed proportions in compounds",
        "How does a chemical change differ from a physical change",
        "What happens when iron and sulphur are heated together",
        "Why are the properties of a mixture similar to its constituents",
        "What is a pure substance and how is it classified",
        "Explain the term dispersion in chemistry",
        "Describe the process of crystallization",
        "What are the different types of solutions",
        "Explain the concept of solubility",
        "Define concentration and its units",
        "What is the difference between homogeneous and heterogeneous mixtures",
        "Describe the methods of separation of mixtures",
        "Explain the law of conservation of mass",
        "What are the applications of chemistry in daily life"
    ]
    
    paper = SamplePaperTemplate.create_question_paper(sample_questions)
    checks, is_valid = validate_question_paper_format(paper)
    
    print("Template Test Results:")
    print(f"Valid format: {is_valid}")
    print(f"Checks: {checks}")
    print(f"Paper length: {len(paper)} characters")
    
    return paper, is_valid 