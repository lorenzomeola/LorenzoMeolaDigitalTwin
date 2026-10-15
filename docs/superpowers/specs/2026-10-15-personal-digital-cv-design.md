# Personal Digital CV Design

## Goal

Create one personal website for Lorenzo Meola with About, Resume, Projects, and a Digital Twin chat, organized in the `Lorenzo Meola Digital CV` directory. The site is aimed at employers evaluating Lorenzo for AI Engineer roles and should grow as he completes courses and projects.

## Architecture

The repository root will be `Lorenzo Meola Digital CV/`. A Next.js App Router application in `frontend/` will render the public pages and the full-screen twin chat. A separate Python FastAPI application in `backend/` will own LLM requests, prompt assembly, tool dispatch, and server-side Supabase access.

Shared profile and project facts will live as structured content at the repository root, so the site and backend can use the same verified information. Contact requests will be stored in a Supabase project dedicated to this website, not in MatchKeeper's database. The current Gradio app will be preserved under a legacy directory until the replacement is working.

## Routes and Experience

- `/` presents About, a concise professional introduction, and entry points to the other pages and twin.
- `/resume` presents experience, education, skills, and a downloadable CV.
- `/projects` presents the three current project cards: CCA Fleet Analytics & Predictive Maintenance, AI Assets Directory, and MatchKeeper.
- `/chat` opens the Digital Twin chat directly. The same chat can open as a full-screen dialog over the other pages, following the interaction pattern observed on Alex Boivin's site.
- Closing the dialog returns the visitor to the page they came from. The chat includes a greeting, suggested questions, message input, loading/error states, and responsive mobile layout.

## Proposed Structure

```text
Lorenzo Meola Digital CV/
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── resume/page.tsx
│   │   ├── projects/page.tsx
│   │   └── chat/page.tsx
│   ├── components/
│   │   └── chat/
│   ├── lib/
│   └── public/cv.pdf
├── backend/
│   ├── app.py
│   ├── context.py
│   ├── tools.py
│   ├── requirements.txt
│   └── tests/
├── content/
│   ├── profile.json
│   └── projects.json
├── supabase/schema.sql
├── legacy/digital-twin-gradio/
├── .env.example
└── README.md
```

The existing `Digital Twin/` folder and its files will be moved intact to `legacy/digital-twin-gradio/` during migration, then the relevant backend code and tests will be adapted into `backend/`. The CV PDF will move to `frontend/public/cv.pdf`; profile and project facts will move into `content/`. No files will be deleted as part of the initial organization.

## Content and Evidence Rules

- About and Resume content will be based on the current summary and CV, without inventing experience, seniority, or outcomes.
- Project cards will distinguish professional work, personal products, ongoing work, and learning.
- The Volvo project must not expose real company data, screenshots, or internal links. Any public demo uses synthetic data only. No performance, downtime, or savings claims without validated evidence.
- AI Assets Directory's functionality may be described, but Lorenzo's exact role remains unconfirmed and must not be overstated.
- MatchKeeper is in free-beta release preparation on staging. Stripe Connect paid bookings are inactive and have only been sandbox-tested; no real payment or adoption claims may be made.
- The GitHub profile link is `https://github.com/lorenzomeola`; project repository links retain the URLs supplied for each project.

## Contact Storage and Security

The backend exposes the `record_user_details` model tool and keeps generic tool dispatch in the chat flow. It stores a visitor's contact only after a valid email and explicit consent through a visible visitor-controlled UI action. The model cannot grant consent on the visitor's behalf. The tool may store the visitor's name and brief professional follow-up notes only when provided.

Supabase uses a dedicated `twin_contact_requests` table with Row Level Security enabled. The service-role key is backend-only and must never be exposed to the browser. Public and authenticated browser roles receive no direct table access. Unknown questions are not stored. Contact data is not sent through Pushover or another notification service in this version.

## Deployment

The frontend is designed for Vercel. The Python API is deployed as a separate backend service with server-side OpenAI and Supabase credentials. The API origin is configured through a frontend server environment variable; secrets are never embedded in client bundles. The application remains usable as a portfolio if the chat API is unavailable.

## Verification

- Confirm each route renders and navigation links work.
- Confirm the chat opens and closes as an overlay and `/chat` loads directly.
- Test chat loading, empty input, API error, and mobile layout states.
- Test a factual question about each project and verify the answer respects its status and evidence constraints.
- Test that contact storage is refused without explicit consent and succeeds with consent against a mocked Supabase client.
- Verify that the browser bundle contains neither the OpenAI key nor Supabase service-role key.
- Run frontend build/lint and backend unit tests before deployment.

## Out of Scope for the Initial Release

- User accounts, visitor chat history, a CMS, analytics dashboards, paid services, and automated meeting scheduling.
- Multi-agent orchestration, RAG, or additional tools without a demonstrated need.
- Public Volvo data, screenshots, repositories, or a production demo.
- Claiming that MatchKeeper processes real payments.