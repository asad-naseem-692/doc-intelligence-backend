# Feature: Sign In (API)
**Owner:** Backend | **Module:** Authentication

## Goal
Verify credentials and issue an access token.

## Scope
- Endpoint: `POST /auth/login`
- Verify password against stored hash.
- On success: issue JWT containing user id + role.
- On failure: generic "invalid email or password" error.
