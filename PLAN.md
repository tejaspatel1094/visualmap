# PLAN.md — Build Plan

> Read `SPEC.md` first. This file is the ordered list of steps.
>
> **How to use this file:** do one milestone at a time. Each milestone ends with
> a working app and a git commit. Do not start the next milestone until the
> checkboxes in the current one are ticked.
>
> When working with Claude Code, say: *"Read SPEC.md and PLAN.md. Do Milestone 3
> only. Stop when the verify steps pass."* Do not ask it to do the whole plan at
> once — you will get a large pile of code you don't understand and can't debug.

---

## Milestone 0 — Prerequisites (do this yourself, not with Claude)

Before any code exists.

- [ ] Register for an EIA API key: https://www.eia.gov/opendata/register.php
- [ ] Paste the key somewhere safe. You'll put it in `.env` in Milestone 1.
- [ ] Confirm the key works. In a browser, open:
      `https://api.eia.gov/v2/electricity/electric-power-operational-data?api_key=YOUR_KEY`
      You should get JSON describing the route, not an error.
- [ ] Install Node 20+ — `node --version`
- [ ] Install Python 3.11+ — `python3 --version`
- [ ] Install Docker Desktop and confirm it is running — `docker ps`
- [ ] Create an empty public repo on GitHub named `gridmap`. **Do not** let
      GitHub add a README — an auto-created README causes the "unrelated
      histories" push error.

**Why first:** every one of these can block you for an hour. Hitting them while
also debugging code makes both harder.

---

## Milestone 1 — Skeleton that runs end to end

**Goal:** a browser page that displays a string fetched from the API, which got
it from Postgres. No real data yet. This proves all three layers talk to each
other, which is the part that breaks.

- [ ] `git init`, create `.gitignore` (Python, Node, `.env`, `__pycache__`, `node_modules`, `dist`)
- [ ] Add `SPEC.md`, `PLAN.md`, `CLAUDE.md`, `README.md`
- [ ] Write `docker-compose.yml` with one `db` service: Postgres 16, named
      volume for persistence, port 5432, user/password/db all `gridmap`
- [ ] `docker compose up -d` and connect to confirm it's alive
- [ ] `backend/` — venv, install `fastapi uvicorn sqlalchemy psycopg[binary] alembic pydantic-settings httpx python-dotenv`
- [ ] `app/config.py` reads `DATABASE_URL`, `EIA_API_KEY`, `CORS_ORIGINS` from `.env`
- [ ] `app/main.py` — FastAPI app, CORS middleware allowing the Vite origin, and
      a `GET /api/health` that runs `SELECT 1` against Postgres and returns `{"db": "ok"}`
- [ ] `frontend/` — `npm create vite@latest frontend -- --template react-ts`
- [ ] `App.tsx` fetches `/api/health` on mount and renders the result
- [ ] Set up the Vite dev proxy so `/api` forwards to `localhost:8000`
      (avoids CORS problems entirely in development)

**Verify:** three terminals — `docker compose up -d`, `uvicorn app.main:app --reload`,
`npm run dev`. Open localhost:5173 and see "db: ok" on the page.

**Commit:** `feat: end-to-end skeleton with health check`

> **This is the most important milestone.** Everything after it is adding
> features to a working system. Do not move on until the browser genuinely
> displays a value that came from the database.

---

## Milestone 2 — Schema and migrations

- [ ] `app/models.py` — `State` and `Generation` tables exactly as in SPEC §4,
      including the `UNIQUE (state_code, year, fuel_code)` constraint
- [ ] `alembic init alembic`, point it at `DATABASE_URL` from config
- [ ] Autogenerate the first migration, **then read it before applying it** —
      autogenerate gets things wrong and this is a good habit to build now
- [ ] `alembic upgrade head`
- [ ] Confirm both tables exist in Postgres
- [ ] Test the reset path: `alembic downgrade base` then `upgrade head` again

**Verify:** tables exist, migration runs cleanly from an empty database.

**Commit:** `feat: database schema and initial migration`

---

## Milestone 3 — Ingest EIA data

The riskiest milestone. Budget real time for it.

- [ ] Hardcode the 50 state codes + `DC` + `US` and their names; seed the `states` table
- [ ] Define the fuel allow-list as an explicit constant. Start with:
      `COW` (coal), `NG` (natural gas), `NUC` (nuclear), `HYC` (conventional hydro),
      `WND` (wind), `SUN` (solar), `PEL`+`PC` (petroleum), `GEO` (geothermal),
      `WWW`/`WAS` (biomass/waste), `OTH` (other).
      **Verify these codes against the live API before trusting them.**
      Anything not on the list is skipped — this is what prevents double counting.
- [ ] `app/ingest.py`:
      - fetch one state, one year first and print the raw JSON
      - page through results using `offset`/`length` until exhausted
      - upsert into `generation` using `ON CONFLICT (state_code, year, fuel_code) DO UPDATE`
      - respect rate limits: sleep briefly between requests
      - log progress per state so a long run isn't silent
- [ ] Run it for a single state and a single year. Check the numbers against
      EIA's own website for that state. **Do not skip this.** If the numbers are
      wrong here, every chart you build later is wrong.
- [ ] Run the full ingest: all states, 2015 to the latest available year
- [ ] Run it a second time and confirm the row count does not change (idempotent)

**Verify:** `SELECT COUNT(*) FROM generation;` returns thousands of rows.
Spot-check your home state's total against eia.gov.

**Commit:** `feat: EIA ingest script with idempotent upsert`

---

## Milestone 4 — API endpoints

- [ ] `app/schemas.py` — Pydantic models for all three responses in SPEC §6
- [ ] `GET /api/years` — distinct years present, plus the max as `latest`
- [ ] `GET /api/states?year=` — per-state totals, excluding the `US` row
- [ ] `GET /api/generation?year=&state=` — fuel breakdown with server-computed percents
- [ ] Handle the error cases: unknown state code → 404, missing year → 400,
      year with no data → empty list and 200, not a crash
- [ ] Open `/docs` and exercise every endpoint by hand

**Verify:** all three endpoints return correct JSON at `/docs`. Percentages for
any one state sum to approximately 100.

**Commit:** `feat: generation API endpoints`

---

## Milestone 5 — Table view (US-1, US-7, US-8)

First real UI. Table before map — a table is easy to debug and makes wrong data
obvious, whereas a map will happily render nonsense in a pretty color.

- [ ] `src/types.ts` — TypeScript types mirroring the API responses
- [ ] `src/api.ts` — one function per endpoint, all fetch calls live here
- [ ] `YearPicker.tsx` — dropdown populated from `/api/years`, defaults to `latest`
- [ ] `StateTable.tsx` — all states for the selected year, sortable by name and total
- [ ] Loading and error states that are actually visible, not a blank screen

**Verify:** change the year, the table changes. Sorting works. Kill the backend
and confirm you see an error message rather than a white page.

**Commit:** `feat: state totals table with year picker`

---

## Milestone 6 — Fuel breakdown (US-3, US-4, US-5, US-6)

- [ ] Selected-state React state in `App.tsx`, defaulting to `null` (= national view)
- [ ] Clicking a table row selects that state; a "Back to US" control clears it
- [ ] `FuelBreakdown.tsx` — table of fuel, generation, percent
- [ ] Add a Recharts bar chart of the same data
- [ ] A fixed color per fuel type, defined once in a shared constant and reused
      everywhere (solar yellow, wind blue, nuclear purple, etc.)
- [ ] Handle negative values (pumped storage) without breaking the chart

**Verify:** click Texas, see a gas-dominated mix. Click Washington, see hydro
dominant. Click Vermont, see almost no fossil. If those look wrong, the ingest
is wrong — go back to Milestone 3.

**Commit:** `feat: fuel type breakdown with chart`

---

## Milestone 7 — Map (US-2, US-3)

Last, because it is the most fiddly and the least essential.

- [ ] `npm i react-simple-maps` and add the us-atlas TopoJSON
- [ ] Render all states, shade by total generation using a sequential color scale
- [ ] Clicking a state selects it — same handler the table uses
- [ ] Hover tooltip with state name and total
- [ ] Highlight the currently selected state
- [ ] Legend explaining the color scale

**Verify:** Texas is the darkest state. Clicking the map and clicking the table
produce identical results.

**Commit:** `feat: choropleth map of state generation`

---

## Milestone 8 — Polish and document

- [ ] `README.md` with real setup steps, written as if for a stranger
- [ ] Format the big numbers with thousands separators and sensible units
- [ ] Add the units and a "data source: EIA Form EIA-923" footer with a link
- [ ] Make it not broken at tablet width
- [ ] Fresh-clone test: clone into a new folder, follow only the README, confirm
      it runs. This catches every undocumented step.

**Commit:** `docs: setup instructions and final polish`

---

## Working rules

**One milestone per Claude Code session.** Start the session by pointing at
`SPEC.md`, `PLAN.md`, and the milestone number. Long sessions accumulate
context and drift.

**Commit at every milestone boundary**, with the app in a working state. A
milestone that doesn't run doesn't get committed to `main`.

**Read the code before accepting it.** If you can't explain what a file does,
ask for an explanation before moving on. The point of this project is that you
understand it afterwards. Code you can't read is code you can't debug, and you
will need to debug it.

**When something breaks, read the actual error.** The full traceback or console
error, top to bottom. Paste it in full when asking for help — the useful line is
usually not the last one.

**If a milestone is taking far longer than the others, stop and reconsider the
approach** rather than pushing through. That's usually a sign the design is
fighting you, not that you're doing it wrong.