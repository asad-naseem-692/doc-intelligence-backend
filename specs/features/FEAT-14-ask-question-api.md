# Feature: Ask Question (API)
**Owner:** Backend | **Module:** Question & Answer

## Goal
Accept a user's question and return a grounded answer.

## Scope
- Endpoint: `POST /query`
- Input: question text (and optionally a specific document_id to scope
  the search to one document).
- Orchestrates: embed the question → hybrid retrieval → grounded answer
  generation → confidence fallback check → save to history → return
  answer + citations.
