# Personal Digital CV Implementation Plan

> **For agentic workers:** Use inline execution with task-by-task review. Steps use checkbox syntax for tracking.

**Goal:** Build one employer-focused personal website with About, Resume, Projects, and a full-screen Digital Twin chat backed by a Python API.

**Architecture:** A Next.js 16 frontend in `frontend/` renders the public site and communicates with a separate FastAPI service in `backend/`. Verified profile/project content is shared from `content/`; a dedicated Neon Postgres table stores contact requests only after explicit consent. The provider-neutral schema supports a later migration to Supabase Pro. The existing Gradio application is preserved under `legacy/` until replacement verification.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, Python 3.12, FastAPI, OpenAI Python SDK, Psycopg 3, Neon Postgres, Pytest, Vercel frontend hosting.

**Spec:** `docs/superpowers/specs/2026-10-15-personal-digital-cv-design.md`

## Global Constraints

- The website targets employers evaluating Lorenzo for AI Engineer roles.
- The three initial projects are Volvo CCA Fleet Analytics, AI Assets Directory, and MatchKeeper.
- Do not expose Volvo data, screenshots, or internal links; any demo uses synthetic data.
- Do not claim AI Assets Directory ownership until Lorenzo confirms his role.
- MatchKeeper paid bookings are inactive and sandbox-tested only; do not claim real payment processing or adoption.
- Store contact information only after explicit consent through a visible visitor-controlled UI action; the model cannot grant consent. Unknown questions and chat transcripts are not stored.
- Keep OpenAI and database credentials on the backend; frontend output contains no secrets.
- No existing files are deleted during initial organization; preserve the Gradio prototype under `legacy/`.

---

### Task 1: Preserve the Prototype and Establish Shared Content

**Files:**
- Copy: `Digital Twin/` to `legacy/digital-twin-gradio/`, preserving the original until Windows releases its lock.
- Create: `content/profile.json`.
- Create: `content/projects.json`.
- Create: `README.md`.
- Test: `legacy/digital-twin-gradio/test_context.py` and `legacy/digital-twin-gradio/test_tools.py`.

**Interfaces:**
- `profile.json` contains verified biography, education, employment facts, current job goal, and public GitHub link.
- `projects.json` contains exactly three project records with `slug`, `title`, `status`, `summary`, `contribution`, `technology`, `evidence`, `privacyNotes`, and `links` fields. `evidence` and `links` are arrays of strings; `technology` and `privacyNotes` are arrays of strings.
- Volvo `privacyNotes` excludes all real data/screenshots/internal URLs and requires synthetic demo data.
- AI Assets Directory contribution remains explicitly unconfirmed.
- MatchKeeper status records staging/free-beta readiness and inactive sandbox-only paid bookings.

- [x] **Step 1: Preserve the current folder under legacy**

Run from the parent workspace directory:

```powershell
New-Item -ItemType Directory -Force legacy | Out-Null
Copy-Item -LiteralPath "Digital Twin" -Destination "legacy/digital-twin-gradio" -Recurse
```

Expected: every original prototype file, including the updated context, Supabase schema, and tests, is preserved under `legacy/digital-twin-gradio/`. Keep `Digital Twin/` untouched until the lock is released; remove the duplicate only after a verified move.

- [x] **Step 2: Create profile and project content from verified facts**

Create `content/profile.json` with the current `summary.txt` facts and `https://github.com/lorenzomeola`. Create three project records from the approved project briefs. Do not add unverified AI Assets Directory ownership or invented Volvo/MatchKeeper metrics.

- [x] **Step 3: Add a README with local setup and folder ownership**

Document `frontend/` as the website, `backend/` as the Python API, `content/` as shared factual source, `supabase/` as database schema, and `legacy/digital-twin-gradio/` as the preserved prototype. List required environment variable names without secret values.

- [x] **Step 4: Run the preserved prototype's tests from its new location**

Run:

```powershell
Push-Location "legacy/digital-twin-gradio"
python -m unittest discover -v
Pop-Location
```

Expected: the current four unit tests pass from the preserved directory.

### Task 2: Scaffold the Next.js Portfolio

**Files:**
- Create: `frontend/` Next.js App Router application and lock file.
- Create: `frontend/app/page.tsx`, `frontend/app/resume/page.tsx`, `frontend/app/projects/page.tsx`, `frontend/app/chat/page.tsx`.
- Create: `frontend/components/SiteNav.tsx`, `frontend/components/ProjectList.tsx`.
- Create: `frontend/lib/content.ts`.
- Create: `frontend/public/cv.pdf` by copying the existing CV PDF.
- Test: frontend route/build checks.

**Interfaces:**
- `getProfile()` reads and validates `content/profile.json`.
- `getProjects()` reads and validates `content/projects.json` and returns all three cards.

- [ ] **Step 1: Scaffold Next.js in `frontend/`**

Initialize Next.js with App Router, TypeScript, Tailwind CSS 4, and linting. Keep package scripts for `dev`, `lint`, `typecheck`, `build`, and `test`.

- [ ] **Step 2: Add content loading and a failing test for the project records**

Implement `getProjects()` to load shared JSON from the repository root. Add a test asserting that the returned slugs are `volvo-cca-fleet-analytics`, `ai-assets-directory`, and `matchkeeper`, and that no record has empty `status`, `contribution`, or `privacyNotes`.

- [ ] **Step 3: Implement shared navigation and the three content routes**

Render About at `/`, CV experience and a PDF download at `/resume`, and the three project records at `/projects`. Use common navigation rather than separate page apps.

- [ ] **Step 4: Add the direct chat route and API-not-configured state**

Render a route-level chat view at `/chat` with greeting, suggested questions, input, loading, and error states. At this task boundary, message submission may show an explicit API-not-configured state; do not pretend it has contacted a model.

- [ ] **Step 5: Verify frontend routes and production build**

Run from `frontend/`:

```powershell
npm run lint
npm run typecheck
npm run build
```

Expected: all three commands succeed and the four routes appear in the build output.

### Task 3: Build the FastAPI Twin Service

**Files:**
- Create: `backend/app.py`, `backend/context.py`, `backend/tools.py`, `backend/requirements.txt`.
- Create: `backend/tests/test_chat.py`, `backend/tests/test_contact_tool.py`.
- Move/copy: shared content remains at `content/` and is included in the backend deployment bundle.
- Create: `database/schema.sql` for the provider-neutral contact table.
- Retain: `supabase/schema.sql` for future Supabase-specific RLS policies; do not use it to initialize Neon.

**Interfaces:**
- `POST /api/chat` accepts `{ "message": string, "history": [{"role": "user" | "assistant", "content": string}], "contactConsent": boolean }` and returns `{ "reply": string }`.
- `contactConsent` is set by the visitor's visible consent control. The API offers the contact tool only when consent is true and at least one email address appears in visitor-authored messages.
- `record_user_details(email, consent_confirmed, visitor_emails, name=None, notes=None)` saves only when consent is true and the requested email appears in `visitor_emails`; the model cannot provide consent or invent an email. The tool inserts a consent timestamp into `twin_contact_requests`.
- `handle_tool_calls(tool_calls)` dispatches only registered tool names and returns OpenAI tool-result messages.

- [x] **Step 1: Write API and contact tests before implementation**

Test that `/api/chat` rejects blank or oversized messages, returns a reply for a valid request through a mocked model client, and that contact storage rejects requests without UI-supplied consent but inserts a validated record when consent is present.

- [x] **Step 2: Run backend tests to establish the red baseline**

Run from `backend/`:

```powershell
python -m pytest -q
```

Expected: tests fail because the API, validation, and PostgreSQL tool are not implemented yet.

- [x] **Step 3: Implement the request schema and health endpoint**

Add Pydantic chat request/response models, a `GET /health` endpoint, and `POST /api/chat`. Reject empty messages, messages over 4000 characters, histories over 20 messages, or history entries with roles other than `user` and `assistant`.

- [x] **Step 4: Port verified context and generic OpenAI tool dispatch**

Build the system prompt from the shared profile/project records. Keep one contact tool. Preserve the model tool-call loop, handle unknown tool names without invoking arbitrary functions, and return model/provider errors as non-sensitive HTTP errors.

- [x] **Step 5: Implement consent-gated PostgreSQL contact insertion**

Validate email format and field lengths, require literal boolean consent from the visitor-controlled request state, and do not accept consent as a model tool argument. Use `DATABASE_URL` only in this process, then insert with parameterized Psycopg SQL into `public.twin_contact_requests` using `database/schema.sql`.

- [x] **Step 6: Run backend tests**

Run:

```powershell
python -m pytest -q
```

Expected: request validation, model-call/tool-call behavior, consent rejection, visitor-email origin checks, and mocked PostgreSQL insertion tests pass. Run `backend\\.venv\\Scripts\\python.exe -m pytest -q` from the repository root; twelve backend tests pass.

### Task 4: Connect the Full-Screen Chat

**Files:**
- Create: `frontend/components/chat/DigitalTwinChat.tsx`.
- Create: `frontend/components/chat/ChatDialog.tsx`.
- Modify: `frontend/app/chat/page.tsx` and shared site navigation.
- Test: frontend chat component and browser interaction tests.

**Interfaces:**
- `DigitalTwinChat` submits `{message, history}` to `${NEXT_PUBLIC_CHAT_API_URL}/api/chat` and renders the returned `reply`.
- `ChatDialog` opens from any route, closes to the originating route, and uses the same chat component as `/chat`.

- [ ] **Step 1: Write UI tests for open/close and submission states**

Test that the chat opens from navigation, exposes a close button, renders suggested prompts, submits a message, displays a reply, and shows an error when the API is unavailable.

- [ ] **Step 2: Run the chat UI tests and confirm the expected failures**

Run from `frontend/`:

```powershell
npm test -- DigitalTwinChat
```

Expected: tests fail until the dialog and API client exist.

- [ ] **Step 3: Implement the shared chat component and overlay**

Use a full-screen accessible dialog on desktop and mobile, keep message input reachable, prevent background interaction while open, and return focus to the opening control after closing.

- [ ] **Step 4: Connect the direct route and overlay to the same component**

Use the same message rendering and submit logic for `/chat` and the dialog. Do not duplicate chat state handling.

- [ ] **Step 5: Run frontend tests, lint, typecheck, and build**

Run `npm test`, `npm run lint`, `npm run typecheck`, and `npm run build` from `frontend/`. Expected: all pass.

### Task 5: Verify Privacy and Prepare Deployment

**Files:**
- Modify: `frontend/next.config.ts` or backend CORS configuration as needed.
- Create/update: root `.env.example` and deployment instructions in `README.md`.
- Verify: `content/projects.json`, built frontend output, Neon schema, and deployed routes.

- [ ] **Step 1: Test factual answers and refusal boundaries**

Use fixed evaluation prompts covering all three projects, Volvo privacy, MatchKeeper payment status, AI Assets Directory role uncertainty, and an unknown fact. Confirm responses do not make unsupported claims.

- [ ] **Step 2: Verify no secrets or sensitive Volvo data reach the frontend**

Search the production frontend build for `OPENAI_API_KEY` and `DATABASE_URL`; neither may appear. Inspect content and demo fixtures for real Volvo data or internal URLs; none may be present.

- [ ] **Step 3: Verify contact consent and database permissions**

Run `database/schema.sql` in the Neon SQL editor. Confirm an unconsented request is rejected by the API and that database credentials are only configured on the backend.

- [ ] **Step 4: Deploy frontend and backend separately**

Deploy `frontend/` to Vercel. Choose a Python-capable backend host, configure HTTPS, restrict CORS to the production site, and set backend secrets through the provider environment settings. Set `NEXT_PUBLIC_CHAT_API_URL` to the API's public origin.

- [ ] **Step 5: Run release checks against production**

Verify `/`, `/resume`, `/projects`, `/chat`, opening/closing the chat overlay, one question per project, API-unavailable behavior, and consent-gated contact storage. Keep the previous Gradio prototype intact until these checks pass.

## Handoff

Execute inline in order. Do not deploy, publish contact data, or remove the legacy prototype until the relevant task's verification passes.