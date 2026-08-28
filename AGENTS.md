# AGENTS.md — Backend (FastAPI) — AI Document Intelligence System

## Scope
This file applies to the `backend/` folder only. Deploys to Railway with
a Postgres database that has the `pgvector` extension enabled. A sibling
`frontend/AGENTS.md` covers the frontend.

## Tech stack (do not substitute)
Python, FastAPI, Pydantic v2, SQLAlchemy + Alembic, PostgreSQL + pgvector
extension, python-jose (JWT), passlib[bcrypt] (password hashing),
`pypdf` / `python-docx` (text extraction), LlamaIndex (chunking), OpenAI
SDK pointed at Gemini's OpenAI-compatible endpoint (embeddings + chat).

## Python project manager: use `uv`, not pip/requirements.txt
This project uses **`uv`** (Astral's fast Python package/project manager)
instead of plain `pip` + `requirements.txt`. Concretely:
- Initialize with `uv init` and manage dependencies with `uv add <package>`
  (e.g. `uv add fastapi uvicorn sqlalchemy alembic psycopg2-binary pgvector
  pydantic python-jose passlib pypdf python-docx llama-index openai`).
- This creates/maintains `pyproject.toml` and a `uv.lock` lockfile —
  commit both to the repo so dependency versions are reproducible.
- Local setup for anyone (including future sessions) is just `uv sync`
  — it creates the virtual environment and installs exact locked
  versions in one step, no separate `python -m venv` + `pip install`.
- Run the app via `uv run uvicorn app.main:app --reload` rather than
  activating a venv manually.
- The `Dockerfile` should install `uv` in the build stage and use
  `uv sync --frozen` (or equivalent) to install dependencies from the
  lockfile, then run the app the same way.
- Do not create a `requirements.txt` for this project — `pyproject.toml`
  + `uv.lock` are the single source of truth for dependencies.

## Build order — full-stack, one feature at a time
Same as Project 2: build vertical slices pairing backend + frontend
specs, one feature at a time, stop for approval after each. Follow
`specs/features/` in `FEAT-XX` numeric order.

## Core architectural invariant
This backend is the single source of truth. All authorization, document
ownership checks, and RAG logic happen here — never trust the frontend.
**Every user can only ever access their own documents, chunks, and Q&A
history — no exceptions, checked on every request via the verified JWT.**

## AI usage — read this carefully
Only two things in this entire system call an AI model. Everything else
is regular code:
1. **Embeddings** (`embedding_service.py`) — converts text into vectors.
   Called once per chunk at upload time, and once per question at query
   time.
2. **Chat/answer generation** (`rag_service.py` / grounded answer step) —
   generates the final answer text, given only the retrieved chunks.

Both are called via the OpenAI Python SDK, but pointed at Gemini:
```python
from openai import OpenAI
client = OpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```
Never call any other AI provider. Never let the AI model decide
authorization, confidence thresholds, or citation formatting — those are
deterministic code, not model output.

## Hard rules
- Every answer must include citations (document + chunk reference) drawn
  from the actual retrieved chunks — never fabricated.
- If retrieval confidence is below the defined threshold, always return
  the fixed fallback message instead of generating an answer — this
  check is a plain code comparison, not a model decision.
- Document ownership is absolute: a query only ever searches chunks
  belonging to `current_user.id`. Admins do NOT get access to other
  users' document content — only to the user list itself.
- Deleting a document or user must cascade-delete all its chunks,
  embeddings, and qa_history — no orphaned vector data left behind.
- `DATABASE_URL`, `CORS_ORIGINS`, and `GEMINI_API_KEY` always come from
  environment variables via a central `app/core/config.py` — never
  hardcoded, never read via scattered `os.getenv()`.
- Never combine `allow_origins=["*"]` with `allow_credentials=True`.

## Database
Same single-database strategy as Project 2: one Postgres database on
Railway (with pgvector enabled), reached via a public connection string
for local development and an internal reference once deployed. I will
provide the real connection string directly for the local `.env` — never
hardcode it in any committed file.

## Data dictionary — return exactly these field names, always
`snake_case` fields, ISO 8601 UTC timestamps, UUID string ids, errors as
`{ "detail": "message" }`, list endpoints return plain arrays.

- **User**: `id, name, email, role ("user"|"admin"), created_at`
- **Auth response**: `{ "access_token": string, "token_type": "bearer", "user": User }`
- **Document**: `id, filename, owner_id, status ("processing"|"ready"|"failed"), uploaded_at`
- **Chunk** (internal, not usually exposed directly): `id, document_id, chunk_index, text, embedding`
- **Citation**: `document_id, filename, chunk_index, excerpt`
- **QueryResponse**: `{ "answer": string, "citations": Citation[], "is_fallback": boolean }`
- **QAHistoryEntry**: `id, question, answer, citations, created_at`

If a feature needs a field not listed here, use the same conventions and
flag it in your summary — add it to both `backend/AGENTS.md` and
`frontend/AGENTS.md`. Never invent or rename a field silently on one side.

## Keep specs and code in sync (mandatory, every time)
The spec file for a feature is the source of truth for what that feature
is supposed to do — not just a one-time planning document. Whenever you
add, change, or remove behavior in a feature after it's already been
built:
1. **Update that feature's `.md` file in `specs/features/` in the same
   change** — add/edit/remove the relevant bullet points (endpoint path,
   request/response shape, validation rule, permission rule) so the spec
   still accurately describes the current behavior.
2. If the change affects what the frontend receives (new/renamed field,
   changed endpoint, changed status codes), note that clearly in the
   spec so it's visible to whoever is working on the frontend repo.
3. If a change doesn't fit any existing feature file, create a new
   `FEAT-XX-name.md` for it, following the same format as the others,
   rather than leaving the change undocumented.
4. Never let a spec describe behavior that no longer exists in the code,
   and never let the code do something its spec doesn't mention. Treat a
   stale or missing spec update as an incomplete task, not an optional
   cleanup step.

## Never let a change to one feature break a feature it depends on
Before changing a feature others rely on (e.g. embedding generation,
which the query pipeline depends on), check `specs/features/` for
anything referencing it. Update its spec explicitly if changed, and
confirm nothing else breaks.

## What you set up yourself
`.env.example` / local `.env` (`DATABASE_URL`, `CORS_ORIGINS`,
`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`GEMINI_API_KEY`, `ENVIRONMENT`), `.gitignore` (must ignore `.env`,
`.venv/`, `__pycache__/`, but NOT `uv.lock` — that gets committed),
`pyproject.toml` + `uv.lock` (via `uv add`, see above — no
`requirements.txt`), `Dockerfile` (installs `uv`, runs `uv sync --frozen`,
listens on Railway's `$PORT`), central `app/core/config.py`, a `/health`
endpoint.

## Deployment target
Railway (backend + Postgres with pgvector enabled). `CORS_ORIGINS` needs
the deployed frontend's Vercel URL once known.
