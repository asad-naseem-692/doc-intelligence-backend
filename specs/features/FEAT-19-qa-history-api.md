# Feature: Q&A History (API)
**Owner:** Backend | **Module:** Citation & History

## Goal
Let a user see their past questions and answers.

## Scope
- `qa_history` table: id, user_id, question, answer, citations (json),
  created_at.
- Endpoint: `GET /query/history` — filtered to `user_id = current_user.id`
  only.
