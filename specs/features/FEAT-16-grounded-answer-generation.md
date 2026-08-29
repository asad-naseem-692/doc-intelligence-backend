# Feature: Grounded Answer Generation
**Owner:** Backend | **Module:** Question & Answer

## Goal
Generate an answer using only the retrieved document chunks — never the model's own general knowledge.

## Scope
- Sends the retrieved chunks + the user question to the Gemini chat endpoint via OpenAI SDK using model `gemini-3.6-flash` (configured in `app/core/config.py` as `GEMINI_CHAT_MODEL`).
- Strict system prompt instructs the model to answer exclusively from the provided source chunks and to return the exact fallback string if the context is insufficient.
- Citations are attached to the answer containing `document_id`, `filename`, `chunk_index`, and `excerpt`.
