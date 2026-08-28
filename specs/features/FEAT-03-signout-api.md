# Feature: Sign Out (API)
**Owner:** Backend | **Module:** Authentication

## Goal
Allow a session to be ended.

## Scope
- Endpoint: `POST /auth/logout` — returns confirmation.
- Since JWTs are stateless, rely on short expiry + client discarding the token.
