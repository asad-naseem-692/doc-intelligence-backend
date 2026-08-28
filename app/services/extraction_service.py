import re
from pathlib import Path


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def _clean_extracted_text(text: str) -> str:
    """Normalize whitespace, remove isolated newlines inside words/lines, and trim."""
    # Replace non-standard whitespace with standard spaces
    text = text.replace("\r", "\n").replace("\f", "\n").replace("\v", "\n")
    # Replace single newlines surrounded by regular letters with a single space (unwrapping words)
    text = re.sub(r"(?<=\w)\n(?=\w)", " ", text)
    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3 or more newlines with double newline (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_file(file_path: str) -> str:
    """
    Extract plain text from a PDF or DOCX file.
    No AI involved — pure deterministic text extraction.
    Raises ValueError if file type is unsupported or extraction fails.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext == ".docx":
        return _extract_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_from_pdf(file_path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            raise ValueError("PDF is encrypted and cannot be read")
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text.strip())
        extracted = "\n\n".join(parts).strip()
        cleaned = _clean_extracted_text(extracted)
        if not cleaned:
            raise ValueError("No readable text found in PDF")
        return cleaned
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")


def _extract_from_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        parts = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)
        extracted = "\n\n".join(parts).strip()
        cleaned = _clean_extracted_text(extracted)
        if not cleaned:
            raise ValueError("No readable text found in DOCX")
        return cleaned
    except Exception as e:
        raise ValueError(f"DOCX extraction failed: {e}")
