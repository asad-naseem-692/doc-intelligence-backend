# Feature: Vector Storage
**Owner:** Backend | **Module:** Processing Pipeline

## Goal
Store each chunk's text and embedding so it can be searched later.

## Scope
- `chunks` table (Postgres + pgvector extension): id, document_id,
  chunk_index, text, embedding (vector column), created_at.
- Once all chunks for a document are stored, set the document's status
  to "ready".
- No AI involved — this is a database write.
