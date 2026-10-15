# Lorenzo Meola Digital CV

Employer-focused personal website with About, Resume, Projects, and a Digital Twin chat.

## Project layout

- `frontend/` - Next.js website and chat interface.
- `backend/` - FastAPI service for the Digital Twin, prompt loading, OpenAI tool dispatch, and consent-gated PostgreSQL contact storage.
- `content/` - shared, verified profile and project records.
- `database/` - provider-neutral PostgreSQL schema used by Neon now and portable to Supabase later.
- `supabase/` - Supabase-specific schema/policies retained for a future migration.
- `legacy/digital-twin-gradio/` - preserved copy of the original Gradio prototype.
- `docs/` - product, technical, design, and implementation documentation.
- `PRODUCT_PLAN.md` - product scope and delivery phases.
- `TECH_STACK.md` - architecture and technology choices.

## Content source

Keep public profile and project facts in `content/profile.json` and `content/projects.json` so the website and backend can use the same records. Verify project status and counts before publishing. Never add real Volvo data, screenshots, or internal links; demos must use synthetic data.

## Run the site locally

Copy `.env.example` to `.env.local` in the repository root and fill in the provider keys and `DATABASE_URL`. Keep real values only in local environment files or deployment settings; never commit them. The backend reads `.env` and `.env.local`; deployed environments should inject variables directly.

Backend (FastAPI, port 8000), from the repository root:

```powershell
uv venv backend\.venv --python 3.12
uv pip install --python backend\.venv\Scripts\python.exe -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000
```

Frontend (Next.js, port 3000):

```powershell
cd frontend
npm install
npm run dev
```

The browser only talks to Next.js. Its `/api/chat` and `/api/providers` routes forward to FastAPI at `CHAT_API_URL`, so no keys or backend URLs reach the client.

Tests and checks: `backend\.venv\Scripts\python.exe -m pytest -q`, and `npm run lint`, `npm run typecheck`, `npm run build` in `frontend/`.

On a corporate network that re-signs TLS traffic, the backend uses the operating system certificate store (`truststore`). Outbound PostgreSQL (port 5432) may also be blocked there, which stops contact saving locally but not chat.

## Current migration status

The Gradio prototype remains in the original `Digital Twin/` folder and has a verified backup at `legacy/digital-twin-gradio/`. Windows still blocks moving the original directory. Both copies currently match by path and SHA-256; keep the legacy copy and remove the duplicate original only after it is no longer open and the move succeeds.

The FastAPI backend, the Next.js site (About, Resume, Projects and the full-screen chat) and the shared content are in place and run locally. Contact requests target Neon Postgres through `DATABASE_URL`; run `database/schema.sql` in the Neon SQL editor before testing inserts. Supabase Pro is a future provider migration: apply its schema/policies and change `DATABASE_URL` after copying any existing contact rows. The remaining stage is deploying both services; see `docs/superpowers/plans/2026-10-15-personal-digital-cv.md`.