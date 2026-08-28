# Feature: Embedding Generation Service
**Owner:** Backend | **Module:** Processing Pipeline

## Goal
Convert each text chunk into a vector (list of numbers) representing its meaning.

## Scope
- `app/services/embedding_service.py`: calls the Gemini embeddings
  endpoint (via the OpenAI SDK pointed at Gemini's OpenAI-compatible
  `base_url`) for each chunk, returns the embedding vector.
- `GEMINI_API_KEY` read from environment via `app/core/config.py` — never
  hardcoded.
- Batch requests where possible to reduce API calls.
- If the API call fails, retry with backoff; if it keeps failing, mark
  the document status "failed".
