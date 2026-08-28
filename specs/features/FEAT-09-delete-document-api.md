# Feature: Delete Document (API)
**Owner:** Backend | **Module:** Document Management

## Goal
Remove a document and everything derived from it.

## Scope
- Endpoint: `DELETE /documents/{id}`
- Only the owning user (or admin) can delete it.
- Deletes: the stored file, the `documents` record, and every `chunks`
  record (and their embeddings) that belong to it — no orphaned data left
  in the vector store.
