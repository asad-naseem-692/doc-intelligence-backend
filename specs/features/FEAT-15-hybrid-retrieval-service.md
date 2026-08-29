# Feature: Hybrid Retrieval Service
**Owner:** Backend | **Module:** Question & Answer

## Goal
Find the chunks most relevant to the user's question, strictly restricted to their own documents.

## Scope
- `app/services/rag_service.py`: embeds the question (`gemini-embedding-001`), then queries `chunks` joined to `documents` filtered to `document.owner_id = current_user.id` and `document.status = 'ready'`.
- Combines vector similarity (`pgvector` cosine distance) with PostgreSQL native full-text search (`ts_rank`):
  - Normalized vector cosine similarity: `cosine_sim = max(0.0, 1.0 - cosine_distance)` (weight: **75%**)
  - Full-text search keyword rank: `keyword_score = min(1.0, fts_rank * 2.0)` (weight: **25%**)
  - Combined hybrid score: `hybrid_score = (0.75 * cosine_sim) + (0.25 * keyword_score)`
- Returns the top-K matching chunks (default `TOP_K = 5`) sorted descending by hybrid score.
- No AI text-generation here — this is deterministic retrieval only.
