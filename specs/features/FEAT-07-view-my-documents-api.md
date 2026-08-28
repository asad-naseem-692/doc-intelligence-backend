# Feature: View My Documents (API)
**Owner:** Backend | **Module:** Document Management

## Goal
Return only the documents belonging to the logged-in user.

## Scope
- Endpoint: `GET /documents`
- Filters by `owner_id = current_user.id` — never returns another user's documents.
- Returns id, filename, status, uploaded_at for each.
