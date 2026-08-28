# Feature: Confidence Fallback
**Owner:** Backend | **Module:** Question & Answer

## Goal
Never let the system hallucinate — if there isn't good enough matching
content, say so instead of guessing.

## Scope
- Define a fixed similarity-score threshold (e.g. below X = "not
  confident enough").
- If the top retrieved chunks fall below the threshold, skip answer
  generation and return a fixed fallback response: "I couldn't find
  enough information in your documents to answer this."
- This check happens in code (a simple comparison), not something the AI
  model decides on its own.
