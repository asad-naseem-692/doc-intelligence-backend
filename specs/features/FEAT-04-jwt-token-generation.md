# Feature: JWT Token Generation & Verification
**Owner:** Backend | **Module:** Authentication

## Goal
Issue and verify signed tokens used to authenticate every request.

## Scope
- `create_access_token(user_id, role)` and `decode_access_token(token)`.
- Payload: `sub` (user id), `role`, `exp`.
- Signed using `JWT_SECRET_KEY` from environment.
- `get_current_user` dependency rejects invalid/expired tokens with 401.
