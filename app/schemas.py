from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class DocType(str, Enum):
    textbook = "textbook"
    sample = "sample"


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    task_id: str
    status: str


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    doc_type: DocType
    upload_time: str
    status: str


class GenerateRequest(BaseModel):
    textbook_ids: List[str] = Field(..., description="List of textbook document IDs")
    sample_paper_id: str = Field(..., description="Sample paper document ID")
    subject_query: str = Field(default="", description="Special instructions for question selection")


class JobStatus(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None


class GenerateResponse(BaseModel):
    task_id: str
    status: str


class ChapterWeightage(BaseModel):
    """Chapter weightage specification"""
    chapter_name: str
    document_id: str
    weightage_percentage: int  # 0-100
    focus_topics: Optional[List[str]] = []  # Specific topics to focus on
    difficulty_level: Optional[str] = "medium"  # easy, medium, hard


class ProfessionalQuestionConfig(BaseModel):
    """Professional question generation configuration"""
    total_questions: int = 20
    total_marks: int = 80
    marks_per_question: int = 5
    
    # Question distribution
    definition_questions: Optional[int] = 5  # "Define...", "What is..."
    explanation_questions: Optional[int] = 5  # "Explain...", "Describe..."
    comparison_questions: Optional[int] = 3   # "Compare...", "Differentiate..."
    application_questions: Optional[int] = 4  # "Give examples...", "Applications..."
    analysis_questions: Optional[int] = 3     # "Analyze...", "Evaluate..."
    
    # Content requirements
    word_limit_min: int = 75
    word_limit_max: int = 100
    
    # Professional preferences
    include_diagrams_references: bool = False
    include_numerical_problems: bool = False
    academic_level: str = "undergraduate"  # undergraduate, graduate, postgraduate


class EnhancedGenerationRequest(BaseModel):
    """Enhanced request for professional question paper generation"""
    
    # Multiple textbook sources
    textbook_sources: List[ChapterWeightage]
    sample_paper_id: str
    
    # Professional configuration
    question_config: ProfessionalQuestionConfig
    
    # Additional instructions
    special_instructions: Optional[str] = None  # Free text for specific requirements
    subject_focus: Optional[str] = None  # e.g., "organic chemistry", "thermodynamics"
    
    # Quality controls
    avoid_repetition: bool = True
    ensure_syllabus_coverage: bool = True
    maintain_difficulty_balance: bool = True


class QuestionDistributionSummary(BaseModel):
    """Summary of how questions were distributed across sources"""
    source_name: str
    document_id: str
    questions_generated: int
    weightage_applied: int
    topics_covered: List[str]


class EnhancedGenerationResponse(BaseModel):
    """Enhanced response with detailed generation information"""
    job_id: str
    pdf_filename: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    
    # Enhanced metadata
    total_questions: int
    total_marks: int
    sources_used: List[QuestionDistributionSummary]
    
    # Quality metrics
    syllabus_coverage_percentage: Optional[float] = None
    difficulty_distribution: Optional[Dict[str, int]] = None
    question_type_distribution: Optional[Dict[str, int]] = None
    
    # Validation results
    format_validated: Dict[str, bool]
    content_quality_score: Optional[float] = None


# Update existing GenerationRequest to maintain backward compatibility
class GenerationRequest(BaseModel):
    textbook_ids: List[str]
    sample_paper_id: str
    config: Dict[str, Any] = {}
    
    # New optional enhanced features
    chapter_weightage: Optional[List[ChapterWeightage]] = None
    professional_config: Optional[ProfessionalQuestionConfig] = None
    special_instructions: Optional[str] = None 