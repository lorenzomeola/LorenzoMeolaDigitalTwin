# Lorenzo Meola Digital CV

Employer-focused personal website with About, Resume, Projects, and a Digital Twin chat.

## Project layout

- `frontend/` - Next.js website and chat interface.
- `backend/` - FastAPI service for the Digital Twin, prompt loading, OpenAI tool dispatch, and consent-gated Supabase contact storage.
- `content/` - shared, verified profile and project records.
- `supabase/` - SQL schema for this portfolio's contact requests.
- `legacy/digital-twin-gradio/` - preserved copy of the original Gradio prototype.
- `docs/` - product, technical, design, and implementation documentation.
- `PRODUCT_PLAN.md` - product scope and delivery phases.
- `TECH_STACK.md` - architecture and technology choices.

## Content source

Keep public profile and project facts in `content/profile.json` and `content/projects.json` so the website and backend can use the same records. Verify project status and counts before publishing. Never add real Volvo data, screenshots, or internal links; demos must use synthetic data.

## Run the Digital Twin API locally

Create a local `.env` from `.env.example`, then set `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `ALLOWED_ORIGINS`. Keep actual values in local environment files or backend deployment settings; never commit them or expose the service-role key to the browser.

Install backend dependencies and start FastAPI from the repository root:

```powershell
uv venv backend\.venv --python 3.12
uv pip install --python backend\.venv\Scripts\python.exe -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --port 8000
```

Run backend tests with `backend\.venv\Scripts\python.exe -m pytest -q`.

The health check is `http://localhost:8000/health`; the chat endpoint is `POST http://localhost:8000/api/chat`. `NEXT_PUBLIC_CHAT_API_URL` is the public API origin used by the future frontend.

## Current migration status

The Gradio prototype remains in the original `Digital Twin/` folder and has a verified backup at `legacy/digital-twin-gradio/`. Windows still blocks moving the original directory. Both copies currently match by path and SHA-256; keep the legacy copy and remove the duplicate original only after it is no longer open and the move succeeds.

The FastAPI backend, shared content, and Supabase schema are in place. The Next.js frontend routes and the production Supabase project are not yet scaffolded/configured. Follow `docs/superpowers/plans/2026-10-15-personal-digital-cv.md` for the remaining stages.