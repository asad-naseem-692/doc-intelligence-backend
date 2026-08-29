# Feature: Hybrid Retrieval Service
**Owner:** Backend | **Module:** Question & Answer

## Goal
Find the chunks most relevant to the user's question, strictly restricted to their own documents.

## Scope
- `app/services/rag_service.py`: embeds the question (`gemini-embedding-001`), then queries `chunks` joined to `documents` filtered to `document.owner_id = current_user.id` and `document.status = 'ready'`.
- Combines vector similarity (`pgvector` cosine distance) with PostgreSQL native full-text search (`ts_rank`) using an additive keyword boost architecture:
  - Base semantic similarity: `cosine_sim = max(0.0, 1.0 - cosine_distance)`
  - Keyword boost from FTS: `keyword_boost = min(0.20, fts_rank * 0.5)`
  - Combined hybrid score: `hybrid_score = min(1.0, cosine_sim + keyword_boost)`
- **Architectural Rationale**: Base relevance is anchored to dense semantic vector similarity so pure semantic matches are never penalized when FTS is 0. Exact keyword hits (names, numbers, specific acronyms) add a positive boost of up to +0.20.
- Returns the top-K matching chunks (default `TOP_K = 5`) sorted descending by hybrid score.
- No AI text-generation here — this is deterministic retrieval only.
