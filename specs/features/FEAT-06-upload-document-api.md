# Feature: Upload Document (API)
**Owner:** Backend | **Module:** Document Management

## Goal
Accept a PDF/DOCX file and start processing it.

## Scope
- Endpoint: `POST /documents` (multipart upload).
- Validate file type (PDF/DOCX only) and size limit server-side.
- Bind document to the logged-in user (from JWT, never from request body).
- Save file to storage, create a `documents` record with status = "processing".
- Trigger the processing pipeline (text extraction → chunking → embeddings)
  asynchronously so the upload request returns quickly.
