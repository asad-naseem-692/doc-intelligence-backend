# Feature: Document Status (API)
**Owner:** Backend | **Module:** Document Management

## Goal
Let the frontend know when a document has finished processing.

## Scope
- Status field on the `documents` record: "processing" | "ready" | "failed".
- Updated by the processing pipeline as each stage completes.
- `GET /documents/{id}` returns current status so the frontend can poll it.
