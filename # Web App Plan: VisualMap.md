# Web App Plan: VisualMap

_Last updated: 2026-10-05 · Owner: Tejas_

## 1. Overview
- **One-line pitch:** <What it is, in one sentence>
- **Problem:** <What pain point does this solve?>
- **Who it's for:** <Primary users and their context>
- **Why now / why me:** <Motivation, existing workaround it replaces>

## 2. Goals & Non-Goals
**Goals (v1)**
- [ ] <Goal 1: measurable if possible>
- [ ] <Goal 2>

**Non-goals (explicitly out of scope for v1)**
- User accounts / login
- Users editing or saving data
- <Other things you won't build yet>

**Success looks like:** <e.g., "X people use it monthly">

## 3. Users & Key Scenarios
| User type | What they need to do | How often |
|-----------|----------------------|-----------|
| <User> | <Task> | <Frequency> |

**Core user stories**
1. As a <user>, I want to <action> so that <outcome>.
2. ...

## 4. Features
| Feature | Description | Priority (Must/Should/Could) | Status |
|---------|-------------|------------------------------|--------|
| <Map view> | <Description> | Must | Not started |
| <Dashboard> | <Charts of X by Y> | Must | Not started |

## 5. Screens / Pages
- **<Page name>**: purpose, main components, key actions
- Sketch / wireframe links: <Figma, photo, ASCII>

## 6. Data
- **Source(s):** <URL / provider of the public data>
- **License:** <Confirm redistribution is allowed; add attribution in app>
- **Key entities:** <e.g., Region, Plant, Reading (fields + relationships)>
- **Size:** <MB / rows> (must stay < 100 MB per file to live in the repo)
- **Refresh rate:** <daily / monthly / static>

## 7. Tech Stack (all free, public data)
| Layer | Choice | Why |
|-------|--------|-----|
| App | Streamlit (Python) | Already in use; single language |
| Charts / maps | Plotly + Folium (OpenStreetMap) | Interactive, no API keys |
| Data storage | Parquet files in repo, queried with DuckDB | No database to manage |
| Data refresh | GitHub Actions on a schedule | Free automated updates |
| Caching | st.cache_data | Fast loads within 1 GB RAM limit |
| Auth | None for v1 | Public, read-only app |
| Hosting | Streamlit Community Cloud | Free deploy from a public GitHub repo |

**Upgrade path:** Supabase/Neon Postgres if data > ~100 MB or users need to save/edit data.

**Free-tier limits to keep in mind**
- Streamlit Community Cloud: ~1 GB RAM; app sleeps when idle (first visit after sleep is slow)
- GitHub: warns at 50 MB per file, blocks at 100 MB; limited monthly Actions minutes on private repos (unlimited on public)

## 8. Architecture
```
[Public data source] → [GitHub Actions (scheduled)] → [Parquet files in repo]
                                                            ↓
                              [User] → [Streamlit app on Community Cloud]
                                          (DuckDB/pandas + st.cache_data)
```

## 9. Non-Functional Requirements
- **Performance:** <e.g., pages load < 3s after wake-up>
- **Accessibility / mobile support:** <...>
- **Cost ceiling:** $0/month

## 10. Milestones
| Milestone | Scope | Target date | Done? |
|-----------|-------|-------------|-------|
| M0: Prototype | Core page with sample data (local) | | [ ] |
| M1: MVP | Must-have features, real data, deployed | | [ ] |
| M2: Automation | Scheduled data refresh via GitHub Actions | | [ ] |
| M3: Launch | Polish, attribution, share link | | [ ] |

## 11. Risks & Open Questions
- **Risk:** Data grows past repo limits → **Mitigation:** Parquet compression, or move to Supabase/Neon
- **Risk:** Source data format/URL changes → **Mitigation:** Refresh job fails loudly; keep last good copy
- **Open question:** What is the data source and how big is it?

## 12. Testing & Launch
- [ ] Manual test checklist for each page
- [ ] Data validation in refresh job (row counts, nulls, schema)
- [ ] Deployment steps documented in README
- [ ] Data source attribution shown in app
- [ ] Feedback channel for users

## 13. Future Ideas (Parking Lot)
- <Nice-to-haves for v2+>

## 14. Decision Log
| Date | Decision | Reason |
|------|----------|--------|
| 2026-10-05 | Free stack: Streamlit + Parquet/DuckDB + Community Cloud | Public data, $0 budget, builds on existing Streamlit code |
| 2026-10-05 | No auth for v1 | Public, read-only app |
