import PyPDF2
from typing import Iterator, Tuple
import io


def stream_pages(file_path: str) -> Iterator[Tuple[int, str]]:
    """Stream PDF pages one by one to avoid loading entire PDF in memory"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file, strict=False)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():  # Only yield pages with actual text
                        yield page_num + 1, text
                except Exception as e:
                    print(f"Error extracting text from page {page_num + 1}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        raise


def stream_pages_from_bytes(pdf_bytes: bytes) -> Iterator[Tuple[int, str]]:
    """Stream PDF pages from bytes data"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes), strict=False)
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                if text.strip():  # Only yield pages with actual text
                    yield page_num + 1, text
            except Exception as e:
                print(f"Error extracting text from page {page_num + 1}: {e}")
                continue
                
    except Exception as e:
        print(f"Error reading PDF from bytes: {e}")
        raise


def read_pdf_streaming(file_path: str) -> str:
    """Read entire PDF text by streaming pages (function name used by worker)"""
    try:
        text_content = []
        for page_num, page_text in stream_pages(file_path):
            text_content.append(f"\n--- Page {page_num} ---\n")
            text_content.append(page_text)
        
        return "\n".join(text_content)
    except Exception as e:
        print(f"Error reading PDF text from {file_path}: {e}")
        raise


def get_pdf_info(file_path: str) -> dict:
    """Get basic PDF information"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file, strict=False)
            
            return {
                "num_pages": len(pdf_reader.pages),
                "title": pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                "author": pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                "subject": pdf_reader.metadata.get('/Subject', '') if pdf_reader.metadata else ''
            }
    except Exception as e:
        print(f"Error getting PDF info for {file_path}: {e}")
        return {"num_pages": 0, "title": "", "author": "", "subject": ""} 