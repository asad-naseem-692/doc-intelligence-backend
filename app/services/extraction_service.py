from pathlib import Path


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


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
        if not extracted:
            raise ValueError("No readable text found in PDF")
        return extracted
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
        if not extracted:
            raise ValueError("No readable text found in DOCX")
        return extracted
    except Exception as e:
        raise ValueError(f"DOCX extraction failed: {e}")
