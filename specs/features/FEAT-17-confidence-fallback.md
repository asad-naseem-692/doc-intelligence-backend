# Feature: Confidence Fallback
**Owner:** Backend | **Module:** Question & Answer

## Goal
Never let the system hallucinate — if there isn't good enough matching content, return a fallback instead of guessing.

## Scope
- Similarity-score threshold configured in `app/core/config.py`: `RAG_CONFIDENCE_THRESHOLD = 0.50`.
- **Calibration Rationale**: High-level semantic summary queries (e.g. *"give summary of project 1"*) produce a cosine similarity against specific document chunks of `~0.60 – 0.65`. Setting the threshold at `0.50` ensures legitimate broad questions are answered, while out-of-domain/irrelevant questions (which score `< 0.45`, e.g. *"recipe for pancakes"* scoring `0.42`) cleanly trigger the fallback.
- If the top retrieved chunk's score falls below `0.50` (or 0 ready chunks exist), the system skips answer generation and returns:
  `"I couldn't find enough information in your documents to answer this."` with `is_fallback = true` and `citations = []`.
- This check happens deterministically in Python code before calling LLM generation.
