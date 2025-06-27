"""
PDF Export Module for Question Papers
Handles creation of properly formatted PDF question papers
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from datetime import datetime
from typing import Dict, Any, List


def create_question_paper_pdf(data: Dict[str, Any], filename: str) -> str:
    """
    Create a PDF question paper from structured data using the new template system
    
    Args:
        data: Dictionary containing paper data with 'raw_content' from template
        filename: Output filename
    
    Returns:
        Path to created PDF file
    """
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Full path for the PDF
    pdf_path = os.path.join(output_dir, filename)
    
    # Check if we have properly formatted content from template
    if 'raw_content' in data and data['raw_content']:
        return create_template_based_pdf(data['raw_content'], pdf_path)
    else:
        # Fallback to old method if raw_content not available
        return create_structured_pdf(data, pdf_path)


def create_template_based_pdf(formatted_content: str, pdf_path: str) -> str:
    """
    Create PDF from properly formatted template content
    
    Args:
        formatted_content: Pre-formatted paper content from template system
        pdf_path: Path where PDF should be saved
    
    Returns:
        Path to created PDF file
    """
    
    # Create the PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles for different parts of the paper
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.black
    )
    
    time_marks_style = ParagraphStyle(
        'TimeMarks',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.black
    )
    
    instruction_style = ParagraphStyle(
        'Instructions',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=12,
        textColor=colors.black
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=8,
        textColor=colors.black
    )
    
    sub_question_style = ParagraphStyle(
        'SubQuestion',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=4,
        leftIndent=20,
        textColor=colors.black
    )
    
    # Split content into lines for processing
    lines = formatted_content.split('\n')
    story = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Header line (contains "May 2024" pattern)
        if "May 2024" in line and "-" in line:
            story.append(Paragraph(line, header_style))
            
        # Time and Marks line
        elif "Time :" in line and "Marks :" in line:
            story.append(Paragraph(line, time_marks_style))
            
        # Instructions section
        elif line.startswith("Instructions :"):
            story.append(Paragraph(line, instruction_style))
            
        # Main question numbers (1., 2., 3., 4.)
        elif line.startswith(("1.", "2.", "3.", "4.")) and "Solve any four" in line:
            story.append(Paragraph(line, question_style))
            
        # Sub-questions (a), b), c), d), e))
        elif line.startswith(("a)", "b)", "c)", "d)", "e)")):
            # Split question and marks
            if line.endswith(" 5"):
                question_text = line[:-2].strip()  # Remove " 5" at end
                marks_text = "5"
                formatted_line = f"{question_text} <b>[{marks_text} marks]</b>"
            else:
                formatted_line = line
            story.append(Paragraph(formatted_line, sub_question_style))
            
        # Special elements
        elif line == "(P.T.O.)":
            story.append(Paragraph(f"<i>{line}</i>", question_style))
            
        elif line == "sssssss":
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<i>{line}</i>", time_marks_style))
            
        # Any other content
        else:
            story.append(Paragraph(line, instruction_style))
    
    # Build the PDF
    doc.build(story)
    
    print(f"✅ PDF created successfully: {pdf_path}")
    return pdf_path


def create_structured_pdf(data: Dict[str, Any], pdf_path: str) -> str:
    """
    Legacy method: Create PDF from structured data (fallback)
    
    Args:
        data: Dictionary containing structured paper data
        pdf_path: Path where PDF should be saved
    
    Returns:
        Path to created PDF file
    """
    
    # Create the PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Define styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=8
    )
    
    # Build story
    story = []
    
    # Title
    title = data.get('title', 'Question Paper')
    story.append(Paragraph(title, title_style))
    
    # Time and Marks
    total_marks = data.get('metadata', {}).get('total_marks', 80)
    story.append(Paragraph(f"Time: 3 Hours &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Marks: {total_marks}", header_style))
    story.append(Spacer(1, 12))
    
    # Instructions
    instructions = data.get('instructions', [])
    if instructions:
        story.append(Paragraph("<b>Instructions:</b>", normal_style))
        for i, instruction in enumerate(instructions, 1):
            story.append(Paragraph(f"{i}. {instruction}", normal_style))
        story.append(Spacer(1, 12))
    
    # Questions
    questions = data.get('questions', [])
    if questions:
        for i, question in enumerate(questions, 1):
            story.append(Paragraph(f"<b>{i}. {question.get('question', '')}</b>", question_style))
            
            # Sub-questions
            sub_questions = question.get('sub_questions', [])
            for j, sub_q in enumerate(sub_questions):
                letter = chr(ord('a') + j)
                marks = sub_q.get('marks', 5)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{letter}) {sub_q.get('text', '')} [{marks} marks]", normal_style))
            
            story.append(Spacer(1, 8))
    
    # Build the PDF
    doc.build(story)
    
    print(f"✅ PDF created successfully: {pdf_path}")
    return pdf_path


def create_sample_format_pdf(paper_content: str, filename: str) -> str:
    """
    Create PDF that exactly matches the sample paper format
    
    Args:
        paper_content: Formatted paper content
        filename: Output filename
    
    Returns:
        Path to created PDF file
    """
    return create_template_based_pdf(paper_content, filename)


def validate_pdf_creation(pdf_path: str) -> bool:
    """
    Validate that PDF was created successfully
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        True if PDF exists and has content, False otherwise
    """
    try:
        if not os.path.exists(pdf_path):
            return False
        
        # Check if file has content
        file_size = os.path.getsize(pdf_path)
        return file_size > 1000  # At least 1KB
        
    except Exception:
        return False


def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
    """
    Get information about the created PDF
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Dictionary with PDF information
    """
    try:
        if not os.path.exists(pdf_path):
            return {"exists": False}
        
        file_size = os.path.getsize(pdf_path)
        created_time = datetime.fromtimestamp(os.path.getctime(pdf_path))
        
        return {
            "exists": True,
            "size_bytes": file_size,
            "size_kb": round(file_size / 1024, 2),
            "created_at": created_time.isoformat(),
            "filename": os.path.basename(pdf_path)
        }
        
    except Exception as e:
        return {"exists": False, "error": str(e)}


def test_pdf_creation():
    """Test PDF creation with sample data"""
    try:
        # Test with template-based content
        sample_content = """May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - May 2024 - MaKA24-2120 T97/BMG301/EE/20241224 : 1T97/BMG301/EE/20241224

Time : 3 Hours Marks : 80

Instructions :1. All Questions are Compulsory.2. Each Sub-question carry 5 marks.
3. Each Sub-question should be answered between 75 to 100 words. Write every questions
answer on separate page.
4. Question paper of 80 Marks, it will be converted in to your programme structure marks.

1. Solve any four sub-questions.
a) Define an element according to Antoine Lavoisier 5
b) What are the physical states of elements at room temperature 5
c) Differentiate between metals and non-metals based on their properties 5
d) Explain why the properties of a compound differ from its constituent elements 5
e) Describe the characteristics of mercury as a metal 5

2. Solve any four sub-questions.
a) Compare and contrast mixtures and compounds 5
b) Explain the significance of fixed proportions in compounds 5
c) How does a chemical change differ from a physical change 5
d) What happens when iron and sulphur are heated together 5
e) Why are the properties of a mixture similar to its constituents 5

(P.T.O.)

3. Solve any four sub-questions.
a) What is a pure substance and how is it classified 5
b) Explain the term dispersion in chemistry 5
c) Describe the process of crystallization 5
d) What are the different types of solutions 5
e) Explain the concept of solubility 5

4. Solve any four sub-questions.
a) Define concentration and its units 5
b) What is the difference between homogeneous and heterogeneous mixtures 5
c) Describe the methods of separation of mixtures 5
d) Explain the law of conservation of mass 5
e) What are the applications of chemistry in daily life 5

sssssss"""
        
        test_data = {
            "raw_content": sample_content,
            "title": "Test Chemistry Paper",
            "metadata": {"total_marks": 80}
        }
        
        pdf_path = create_question_paper_pdf(test_data, "test_paper.pdf")
        
        if validate_pdf_creation(pdf_path):
            info = get_pdf_info(pdf_path)
            print(f"✅ PDF test successful: {info}")
            return True
        else:
            print("❌ PDF validation failed")
            return False
            
    except Exception as e:
        print(f"❌ PDF test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing PDF Creation System...")
    test_pdf_creation() 