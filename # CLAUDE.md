# CLAUDE.md

Conventions for this repository. Claude Code reads this file automatically at
the start of every session.

## Project

A read-only web app showing US electricity generation by state and fuel type,
sourced from the EIA Open Data API v2. See `SPEC.md` for the full specification
and `PLAN.md` for the build order.

## Working style

- **Do one milestone from `PLAN.md` at a time.** Do not jump ahead or
  implement future milestones "while you're in there."
- **Explain before writing.** For anything non-trivial, describe the approach in
  a few sentences and wait for confirmation before generating files.
- **Prefer boring, explicit code over clever code.** The owner of this repo is
  learning. Readability beats concision every time.
- **Comment the why, not the what.** Skip `# increment counter`. Explain why a
  fuel code is excluded or why a query is shaped a certain way.
- **Do not add dependencies** that aren't in `SPEC.md` §5 without asking first.
- **Do not add features** not listed in the current milestone. If something
  seems missing, say so rather than building it.

## Hard rules

- **Never commit `.env`** or any real API key. `.env.example` holds placeholders only.
- **Never call the EIA API from the frontend.** Only `ingest.py` talks to EIA.
- **Never bypass Alembic.** Schema changes go through a migration, never a
  manual `ALTER TABLE` or `create_all()`.
- **No authentication.** This app has no users. If a change seems to require
  login, the change is wrong.
- **Never hardcode the current year.** Query the database for the latest year
  with data.

## Code conventions

### Python (backend)

- Python 3.11+, type hints on every function signature
- SQLAlchemy 2.0 style (`select()`, not legacy `Query`)
- Pydantic models for every response; no bare dicts out of a route
- Business logic in functions, not inline in route handlers
- `snake_case` for everything

### TypeScript (frontend)

- Functional components with hooks only
- Explicit types for all props and all API responses — no `any`
- All `fetch` calls go in `src/api.ts`; components never fetch directly
- Component files are `PascalCase.tsx`
- Keep shared state in `App.tsx`; no state management library for v1

### Shared

- Fuel type colors are defined **once** and imported wherever needed
- Units ("thousand megawatthours") come from the API; never hardcode them in the UI
- Numbers are stored raw and formatted only at display time

## Commands

```bash
docker compose up -d                        # start Postgres
cd backend && source .venv/bin/activate     # activate the Python venv (every new terminal)
alembic upgrade head                        # apply migrations
python -m app.ingest                        # load EIA data
uvicorn app.main:app --reload               # run the API on :8000
cd frontend && npm run dev                  # run the UI on :5173
```

## Known pitfalls

- **Fuel code double counting.** EIA returns both aggregate codes (`ALL`, `REN`)
  and specific ones (`SUN`, `WND`). Only the explicit allow-list in `ingest.py`
  is used. Adding a code to that list without checking for overlap will silently
  inflate every total in the app.
- **Missing fuels are not errors.** A state with no nuclear plants returns no
  nuclear rows. Treat absence as zero.
- **Negative generation is real.** Pumped-storage hydro can be net negative.
- **The venv must be re-activated in every new terminal session**, or
  `uvicorn`/`alembic` will appear to be "not found."
- **Postgres must be running** before the API starts, or you get a connection
  refused error that looks like an application bug.