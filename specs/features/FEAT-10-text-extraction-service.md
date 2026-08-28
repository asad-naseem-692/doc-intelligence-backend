# Feature: Text Extraction Service
**Owner:** Backend | **Module:** Processing Pipeline

## Goal
Pull raw readable text out of an uploaded PDF/DOCX file.

## Scope
- `app/services/extraction_service.py`: given a file path, returns plain text.
- Uses a standard library (e.g. `pypdf` for PDF, `python-docx` for DOCX) —
  no AI involved, this is pure text extraction.
- If extraction fails (corrupt file, unsupported format), mark the
  document status "failed" with a reason.
