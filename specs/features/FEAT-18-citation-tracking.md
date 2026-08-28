# Feature: Citation Tracking
**Owner:** Backend | **Module:** Citation & History

## Goal
Let every answer point back to exactly where it came from.

## Scope
- Each answer response includes a `citations` list: document filename,
  chunk_index, and a short excerpt of the source chunk text.
- Built from the same chunks used in `grounded-answer-generation` — no
  separate lookup or guessing.
