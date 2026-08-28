# Feature: Hybrid Retrieval Service
**Owner:** Backend | **Module:** Question & Answer

## Goal
Find the chunks most relevant to the user's question, restricted to
their own documents.

## Scope
- `app/services/rag_service.py`: embeds the question (Gemini), then
  queries `chunks` filtered to `document.owner_id = current_user.id`.
- Combines vector similarity (pgvector cosine distance) with a keyword
  match check — a chunk that matches both should rank higher than one
  matching only one signal.
- Returns the top-K matching chunks with their similarity scores.
- No AI text-generation here — this is retrieval only.
