# Feature: Embedding Generation Service
**Owner:** Backend | **Module:** Processing Pipeline

## Goal
Convert each text chunk into a dense vector representing its meaning.

## Scope
- `app/services/embedding_service.py`: calls Gemini embedding endpoint (`gemini-embedding-001`, dimension: 3072) via OpenAI SDK with `base_url="https://generativelanguage.googleapis.com/v1beta/openai/"`.
- Model name and dimension configured via `app/core/config.py` (`GEMINI_EMBEDDING_MODEL` and `EMBEDDING_DIMENSION`).
- Batch requests (default `BATCH_SIZE = 20`) with exponential retry backoff (up to 3 retries).
- Response vectors stored in PostgreSQL via `pgvector` column `Vector(3072)`.
