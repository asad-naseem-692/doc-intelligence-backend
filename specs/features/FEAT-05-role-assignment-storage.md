# Feature: Role Assignment & Storage
**Owner:** Backend | **Module:** Authentication

## Goal
Store and enforce each user's role (user / admin).

## Scope
- `role` column on `users` table, default "user" at signup.
- Role only ever comes from the verified JWT server-side — never trusted from a request body.
- Admin accounts are created via a seed script, not public signup (same pattern as Project 2).
