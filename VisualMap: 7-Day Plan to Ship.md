 VisualMap: 7-Day Plan to Ship

**Goal:** Ship a working, deployed VisualMap web app that someone else can open and use, with no hand-holding.

**Rules for the week**
- Scope is frozen after Day 1. New ideas go in the "Later" list at the bottom.
- Ship something you can show at the end of each day, even if it's rough.
- When a choice is close, pick the simpler option.

---

## Day 1: Lock scope and set up
- [ ] Re-read the plan of action and pick the 3–5 must-have features for v1
- [ ] Write one sentence defining "done" (e.g. "User can open the URL, pick a region, and see electricity data on the map")
- [ ] Move everything else to the "Later" list
- [ ] Settle the stack (keep Streamlit for v1 or move to the planned web stack). Don't revisit it after today.
- [ ] Clean up the repo structure, add `requirements.txt` / `package.json`, and get `.gitignore` right
- [ ] App runs locally from a fresh clone with one command

**End of day:** Scope list is written down and the app skeleton runs locally.

## Day 2: Data pipeline
- [ ] Find the data sources and confirm you have access (API keys, files, rate limits)
- [ ] Write the load/clean step as its own module, separate from the UI
- [ ] Cache or store processed data so the app doesn't re-fetch on every load
- [ ] Spot-check numbers against the source and confirm they look right
- [ ] Handle missing or bad data without crashing

**End of day:** One function returns clean, correct data in the shape the map needs.

## Day 3: Core map view
- [ ] Render the base map
- [ ] Put the data on the map (choropleth, points, or heat layer, whatever v1 needs)
- [ ] Add a legend and units so the colours mean something
- [ ] Tooltips or popups show the key values

**End of day:** Opening the app shows a correct, readable map. This is the core of the product.

## Day 4: Interactions
- [ ] Add filters and controls (region, time period, metric)
- [ ] Add any summary stats or side charts that are in scope
- [ ] Make sure the map responds quickly when controls change
- [ ] Choose sensible defaults so the first screen is useful

**End of day:** A user can explore the data without help.

## Day 5: Polish and edge cases
- [ ] Add a page title, short intro text, and data source attribution
- [ ] Show loading states and friendly error messages
- [ ] Check it on a laptop screen and on a phone
- [ ] Remove dead code, debug prints, and hardcoded paths
- [ ] Move secrets into environment variables

**End of day:** The app looks finished and doesn't break on bad input.

## Day 6: Deploy and test
- [ ] Deploy (Streamlit Community Cloud, Vercel, Render, or an internal host)
- [ ] Set the environment variables and secrets on the host
- [ ] Test the live URL from a clean browser
- [ ] Give it to 1–2 people and watch them use it without helping
- [ ] Fix the top 3 issues they hit

**End of day:** The live URL works for someone who isn't you.

## Day 7: Buffer, docs, launch
- [ ] Finish anything that slipped
- [ ] Update the README with what it is, how to run it locally, how to deploy, and where the data comes from
- [ ] Tag a release (`v1.0`)
- [ ] Share the link with your intended audience
- [ ] Write a short "what's next" list from feedback

**End of day:** v1 is shipped and announced.

---

## Definition of Done (v1)
- [ ] Deployed at a stable URL
- [ ] Core map shows correct data
- [ ] Main filters work
- [ ] No crashes on normal use
- [ ] README explains how to run and deploy

## Later (not this week)
- 