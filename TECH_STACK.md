# Personal Digital CV - Technical Stack

## Architecture

One repository contains a public Next.js frontend, a separate Python API for the Digital Twin, shared structured profile/project content, and Supabase schema. The existing Gradio implementation remains under a legacy directory until the replacement has been verified. The frontend and API communicate over HTTPS; API credentials and database service credentials stay server-side.

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
- **Supabase Python client** for the consent-gated contact request insertion.
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

- **Supabase Postgres** stores contact requests in a dedicated `twin_contact_requests` table for the Digital Twin, separate from MatchKeeper.
- Enable Row Level Security. Do not grant direct `anon` or `authenticated` access; only the backend service role may insert.
- Store `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` only in backend environment variables.
- Store `OPENAI_API_KEY` only in backend environment variables.
- `NEXT_PUBLIC_CHAT_API_URL` may contain the public API origin; it must not contain a secret.
- Keep `.env` out of version control; commit only `.env.example` with placeholders.

## Deployment

- **Frontend**: Vercel.
- **Python API**: a separate Python-capable host, to be selected before release. The deployment must support FastAPI, HTTPS, environment secrets, and the required response duration for model calls.
- Configure the frontend's allowed origin in backend CORS settings; do not use a wildcard in production.
- Set separate development and production credentials. Do not reuse MatchKeeper's Supabase project or service key.
- Free tiers may have usage limits, cold starts, or suspend idle services; verify current provider limits before launch. OpenAI usage is billed separately from hosting.

## Quality and Security Checks

- Frontend: TypeScript check, lint, Vitest/React Testing Library component tests, Playwright browser checks, and production build.
- Backend: Pytest for request validation, tool consent, Supabase writes (mocked in unit tests), and error responses.
- Verify all four routes, responsive mobile layout, chat open/close, direct `/chat`, and API-unavailable state.
- Verify secrets are absent from frontend output and logs.
- Validate and bound message length/history and contact fields at the API boundary.
- Restrict production CORS to the portfolio origin and use HTTPS.

## Initial Dependency Files

- `frontend/package.json` and lock file: Next.js, React, TypeScript, Tailwind, and selected test tooling.
- `backend/requirements.txt`: FastAPI, Uvicorn, OpenAI SDK, Supabase client, and Pytest.
- Avoid adding a database abstraction, authentication provider, analytics vendor, or agent framework until an MVP requirement needs it.