# Feature: Delete/Suspend User (API)
**Owner:** Backend | **Module:** Admin Panel

## Goal
Let an admin remove or suspend a problematic account.

## Scope
- Endpoint: `DELETE /admin/users/{id}` or `PATCH /admin/users/{id}/suspend`
  (admin role only, 403 otherwise).
- Deleting a user also deletes their documents, chunks, and qa_history
  (cascade) — no orphaned data left behind.
