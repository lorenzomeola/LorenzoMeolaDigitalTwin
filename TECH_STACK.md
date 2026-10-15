# Personal Digital CV - Technical Stack

## Architecture

One repository contains a public Next.js frontend, a separate Python API for the Digital Twin, shared structured profile/project content, and a provider-neutral PostgreSQL schema. Neon Postgres is the initial database provider; the same SQL table can be migrated to Supabase Pro later. The existing Gradio implementation remains under a legacy directory until the replacement has been verified. The frontend and API communicate over HTTPS; API credentials and database credentials stay server-side.

## Frontend

- **Next.js 16 App Router** for routing, server rendering, and the site shell.
- **React 19** for interactive components, including the chat dialog.
- **TypeScript** for frontend type checking and structured content contracts.
- **Tailwind CSS 4** for responsive styling and design tokens.
- **Routes**: `/`, `/resume`, `/projects`, and `/chat`.
- **Chat UI**: shared full-screen dialog that opens from any page; `/chat` exposes the same experience directly.
- **CV asset**: `frontend/public/cv.pdf`.
- **Hosting**: Vercel for the frontend.

No additional component or animation library is selected for the MVP; use native platform features unless a specific interface requirement justifies a dependency.

## Backend

- **Python 3.12** as the initial runtime target.
- **FastAPI** for the HTTP API, request validation, and OpenAPI documentation.
- **OpenAI Python SDK** for model requests and function/tool calling.
- **Psycopg 3** for parameterized, consent-gated PostgreSQL contact inserts.
- **Pydantic** request/response models through FastAPI's validation layer.
- **Pytest** for backend unit and endpoint tests.
- **Vitest and React Testing Library** for frontend component tests.
- **Playwright** for browser-level route and chat interaction checks.

Initial API responsibility:

- `POST /api/chat`: accept a user message and bounded conversation history, build the system context, run the model/tool loop, and return the assistant response.
- The `record_user_details` tool may write to `twin_contact_requests` only after a valid email and explicit consent from a visible visitor-controlled UI action.
- Consent state comes from the visitor-facing UI request, never from a model-generated tool argument; record its timestamp when saving.
- No endpoint stores unknown questions or conversation transcripts.

## Shared Content

- `content/profile.json`: verified short biography, education, experience, skills, and public profile links.
- `content/projects.json`: the three project cards, contribution, stack, status, evidence, privacy constraints, and public links.
- Both apps consume the same repository content. The backend deployment must package the `content/` directory with its service.
- Keep confidential Volvo material out of shared content and tests; any demo dataset must be synthetic.

## Data and Secrets

- **Neon Postgres** stores contact requests in a dedicated `twin_contact_requests` table, separate from MatchKeeper. Use the Vercel Preview-scoped `DATABASE_URL` for preview deployments and keep the database credentials backend-only.
- `database/schema.sql` is provider-neutral. The backend uses parameterized SQL through Psycopg and does not rely on Supabase Data APIs or auth roles.
- When migrating to Supabase Pro, copy the table/schema and contact rows, apply Supabase-specific RLS policies, and replace `DATABASE_URL` with the Supabase Postgres connection string.
- Store `OPENAI_API_KEY` only in backend environment variables.
- `NEXT_PUBLIC_CHAT_API_URL` may contain the public API origin; it must not contain a secret.
- Keep `.env` and `.env.local` out of version control; commit only `.env.example` with placeholders.

## Deployment

- **Frontend**: Vercel.
- **Python API**: a separate Python-capable host, to be selected before release. The deployment must support FastAPI, HTTPS, environment secrets, and the required response duration for model calls.
- Configure the frontend's allowed origin in backend CORS settings; do not use a wildcard in production.
- Set separate Preview and Production database credentials. Do not reuse MatchKeeper's database.
- Free tiers may have usage limits, cold starts, or suspend idle services; verify current provider limits before launch. OpenAI usage is billed separately from hosting.

## Quality and Security Checks

- Frontend: TypeScript check, lint, Vitest/React Testing Library component tests, Playwright browser checks, and production build.
- Backend: Pytest for request validation, tool consent, PostgreSQL writes (mocked in unit tests), and error responses.
- Verify all four routes, responsive mobile layout, chat open/close, direct `/chat`, and API-unavailable state.
- Verify secrets are absent from frontend output and logs.
- Validate and bound message length/history and contact fields at the API boundary.
- Restrict production CORS to the portfolio origin and use HTTPS.

## Initial Dependency Files

- `frontend/package.json` and lock file: Next.js, React, TypeScript, Tailwind, and selected test tooling.
- `backend/requirements.txt`: FastAPI, Uvicorn, OpenAI SDK, Psycopg, python-dotenv, and Pytest.
- Avoid adding a database abstraction, authentication provider, analytics vendor, or agent framework until an MVP requirement needs it.