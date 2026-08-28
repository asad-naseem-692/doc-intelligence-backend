# Feature: Semantic Chunking Service
**Owner:** Backend | **Module:** Processing Pipeline

## Goal
Split extracted text into small, meaningful pieces for embedding.

## Scope
- `app/services/chunking_service.py`: uses LlamaIndex to split text into
  chunks (target size configurable, e.g. ~300-500 tokens with slight
  overlap between chunks so context isn't cut mid-sentence).
- Each chunk keeps a reference to its source document and a chunk index
  (for citation later).
- No AI involved — this is a deterministic text-splitting step.
