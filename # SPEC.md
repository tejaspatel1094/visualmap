# SPEC.md — US Electricity Generation Explorer

> This file describes **what** we are building and **why**.
> `PLAN.md` describes the ordered steps to build it.
> `CLAUDE.md` describes the conventions Claude Code should follow.
>
> Keep this file updated. If the app changes, change this file first.

---

## 1. Problem statement

I want to see how much electricity the United States produces, broken down by
state and by generation source (solar, wind, nuclear, natural gas, coal, hydro,
petroleum, other).

Today, getting this requires downloading spreadsheets from EIA or clicking
through several separate government pages. This app puts the whole picture on
one screen: pick a year, see every state, see the mix.

**Done for v1 means:** I can open the app in a browser, see a map and a table of
all 50 states for a selected year, click a state, and see its generation
broken down by fuel type as both numbers and a chart.

**Non-goals for v1** (explicitly out of scope, do not build these):

- User accounts, login, or saved preferences
- Real-time / hourly data
- Forecasting or projections
- Emissions, pricing, or capacity data
- Mobile-specific layouts (it should not be broken on mobile, but desktop is the target)
- Deployment to a public host

---

## 2. Users

One user: me. The app is read-only and the data is identical for everyone, so
there is no authentication, no authorization, and no per-user state.

This is the single biggest simplification in the project. Do not add auth.

---

## 3. User stories

Each of these should be independently testable. They are the acceptance
criteria for the milestones in `PLAN.md`.

| # | Story |
|---|-------|
| US-1 | As a user, I can select a year and see total electricity generation for every state. |
| US-2 | As a user, I can see a US map where each state is shaded by its total generation. |
| US-3 | As a user, I can click a state on the map or in the table to select it. |
| US-4 | As a user, I can see the selected state's generation broken down by fuel type in a table. |
| US-5 | As a user, I can see that same breakdown as a bar or pie chart, with percentages. |
| US-6 | As a user, I can see the national (US total) breakdown when no state is selected. |
| US-7 | As a user, I can sort the state table by name or by total generation. |
| US-8 | As a user, I see a clear loading state while data loads and a clear error message if it fails. |

### Deferred to v2 (do not build yet)

- Compare two states side by side
- Time series of one state across many years
- Filter the map by a single fuel type ("show me solar only")
- CSV export

---

## 4. Data

### Source

**EIA Open Data API v2** — https://api.eia.gov/v2/

- Base URL: `https://api.eia.gov/v2/`
- Route used: `electricity/electric-power-operational-data/data`
- Underlying survey: Form EIA-923
- **Requires a free API key.** Register at https://www.eia.gov/opendata/register.php

The API is self-documenting. Open `https://api.eia.gov/v2/electricity/electric-power-operational-data?api_key=YOUR_KEY`
in a browser and it will list the available facets, frequencies, and data
columns. **Do this before writing any ingest code** — confirm the exact facet
names rather than trusting this document.

Relevant query parameters:

- `frequency=annual` (also supports `monthly`)
- `data[]=generation`
- `facets[location][]=CO` — two-letter state code, or `US` for the national total
- `facets[sectorid][]=98` — "electric power" sector (all utility-scale generators)
- `start=2015&end=2024`
- `length` / `offset` for paging (the API caps rows per request)

A response row looks roughly like:

```json
{
  "period": "2023",
  "location": "CO",
  "fueltypeid": "SUN",
  "fuelTypeDescription": "solar",
  "sectorid": "98",
  "generation": "4521.3",
  "generation-units": "thousand megawatthours"
}
```

### Important data caveats

Write these down now so they don't surprise you later:

1. **Not all fuel types are returned for every state.** A state with no nuclear
   plants simply has no nuclear rows. The frontend must handle missing fuels as
   zero, not as an error.
2. **Fuel type codes overlap.** EIA returns both aggregate codes (e.g. `ALL`,
   `REN` for all renewables) and specific ones (`SUN`, `WND`, `NUC`). If you sum
   everything naively you will **double count**. Pick an explicit allow-list of
   non-overlapping fuel codes and ignore the rest. This is the single most
   likely bug in this project.
3. **Units are thousand megawatthours (= gigawatthours).** Store the raw number
   and the unit string. Do unit conversion for display only, never in the database.
4. **The data lags.** The most recent complete year is typically 1–2 years
   behind the current year. Do not hardcode the current year as the default;
   query the database for the latest year that has data.
5. **Generation can be negative.** Pumped-storage hydro consumes more than it
   produces in some states. Charts must not break on negative values.

### Data model

Two tables. Keep it this simple.

```
states
  code          TEXT PRIMARY KEY     -- 'CO', 'TX', 'US'
  name          TEXT NOT NULL        -- 'Colorado'
  is_national   BOOLEAN NOT NULL     -- true only for the 'US' row

generation
  id            SERIAL PRIMARY KEY
  state_code    TEXT NOT NULL REFERENCES states(code)
  year          INTEGER NOT NULL
  fuel_code     TEXT NOT NULL        -- 'SUN', 'WND', 'NUC', 'NG', 'COW', ...
  fuel_name     TEXT NOT NULL        -- 'solar', 'wind', ...
  generation    NUMERIC NOT NULL     -- raw value from EIA
  units         TEXT NOT NULL        -- 'thousand megawatthours'

  UNIQUE (state_code, year, fuel_code)
```

The `UNIQUE` constraint matters: it lets the ingest script re-run safely using
an upsert instead of creating duplicate rows. Re-running ingest must be
idempotent.

---

## 5. Stack

Everything here is open source and runs on the laptop.

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React 18 + Vite + TypeScript | Fast dev server, no hidden magic, types catch data-shape bugs early |
| Charts | Recharts | Declarative, React-native, good enough for bars and pies |
| Map | react-simple-maps + us-atlas TopoJSON | No API key, no tile server, renders offline |
| Backend | FastAPI (Python 3.11+) | Reuses Python knowledge; auto-generated API docs at `/docs` |
| ORM | SQLAlchemy 2.x | Standard, well documented |
| Migrations | Alembic | Schema changes get versioned like code |
| Database | PostgreSQL 16, in Docker | Same database locally as anywhere it would later be hosted |
| HTTP client (ingest) | httpx | Async-capable, modern requests replacement |
| Package manager (py) | uv or pip + venv | Either is fine; be consistent |
| Package manager (js) | npm | Default, already installed with Node |

### Why Postgres in Docker rather than SQLite

SQLite would work for v1. Postgres in Docker is chosen because it costs about
one hour now and makes this project deployable later without a database
migration. The tradeoff is that the database must be running before the API
starts — `docker compose up -d db`.

---

## 6. Architecture

```
┌──────────────────────┐
│  Browser             │
│  React + Vite        │  localhost:5173
└──────────┬───────────┘
           │  fetch()  JSON over HTTP
           ▼
┌──────────────────────┐
│  FastAPI             │  localhost:8000
│  - /api/years        │
│  - /api/states       │
│  - /api/generation   │
└──────────┬───────────┘
           │  SQLAlchemy
           ▼
┌──────────────────────┐
│  PostgreSQL          │  localhost:5432  (Docker)
└──────────▲───────────┘
           │
           │  one-off, run manually
┌──────────┴───────────┐
│  ingest.py           │ ──► EIA API v2
└──────────────────────┘
```

**Key decision: the EIA API is called by the ingest script, never by the
frontend and never by a live request.** The frontend only ever talks to our own
API, which only ever reads our own database. This means the app works offline
once seeded, it is fast, and the EIA API key never leaves the server.

### API contract

```
GET /api/years
  -> { "years": [2015, 2016, ..., 2024], "latest": 2024 }

GET /api/states?year=2023
  -> { "year": 2023,
       "units": "thousand megawatthours",
       "states": [ { "code": "TX", "name": "Texas", "total": 512345.6 }, ... ] }

GET /api/generation?year=2023&state=TX
  -> { "year": 2023, "state": "TX", "name": "Texas",
       "units": "thousand megawatthours",
       "total": 512345.6,
       "fuels": [ { "code": "NG", "name": "natural gas",
                    "generation": 250000.0, "percent": 48.8 }, ... ] }
  state defaults to "US" when omitted.
```

Percentages are computed on the server, not in the browser, so there is one
definition of "percent of total" in one place.

---

## 7. Repository layout

```
gridmap/
├── README.md
├── SPEC.md
├── PLAN.md
├── CLAUDE.md
├── .gitignore
├── .env.example           # committed, no real secrets
├── .env                   # NEVER committed
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py        # FastAPI app + CORS
│       ├── config.py      # env var loading
│       ├── db.py          # engine + session
│       ├── models.py      # SQLAlchemy tables
│       ├── schemas.py     # Pydantic response models
│       ├── routes.py      # the three endpoints
│       └── ingest.py      # EIA -> Postgres
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api.ts         # all fetch calls, one file
        ├── types.ts       # mirrors backend schemas
        └── components/
            ├── YearPicker.tsx
            ├── StateMap.tsx
            ├── StateTable.tsx
            └── FuelBreakdown.tsx
```

---

## 8. Configuration

All configuration is environment variables. Nothing is hardcoded.

`.env.example` (committed to git):

```
EIA_API_KEY=your_key_here
DATABASE_URL=postgresql+psycopg://gridmap:gridmap@localhost:5432/gridmap
CORS_ORIGINS=http://localhost:5173
```

`.env` is the real file and is listed in `.gitignore`. **If a real API key ever
gets committed, it is burned** — revoke it at eia.gov and generate a new one.
Rewriting git history does not un-publish a pushed secret.

---

## 9. Definition of done for v1

- [ ] `docker compose up -d` starts Postgres
- [ ] `alembic upgrade head` creates the schema from scratch
- [ ] `python -m app.ingest` populates 10 years of data for all states plus US
- [ ] `uvicorn app.main:app --reload` serves all three endpoints, documented at `/docs`
- [ ] `npm run dev` serves the UI, which loads real data from the API
- [ ] All eight user stories US-1 through US-8 pass by hand
- [ ] `README.md` explains setup well enough that I could rebuild this on a fresh laptop
- [ ] No secrets in git history