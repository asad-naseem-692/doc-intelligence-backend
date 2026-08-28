# Feature: View All Users (API)
**Owner:** Backend | **Module:** Admin Panel

## Goal
Let an admin see who is using the system.

## Scope
- Endpoint: `GET /admin/users` (admin role only, 403 otherwise).
- Returns id, name, email, role, created_at for every user.
- Does NOT return any other user's documents or chunk content — admin
  can see who exists, not what they've uploaded or asked.
