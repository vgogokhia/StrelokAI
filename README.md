# StrelokAI - AI-Powered Ballistic Calculator

## Overview

**StrelokAI** is an external ballistic calculator built with [Streamlit](https://streamlit.io).
It computes elevation and windage for long-range shooting (RK4 point-mass solver, G1/G7 and
custom drag curves, spin drift, aero jump, Coriolis, inclination, cant, powder-temperature MV
compensation), and adds live weather for your location, phone compass heading, a dope card,
reticle/turret views, a rangefinder, scope recognition via AI, and cloud-saved profiles.

The application is deployed at: **https://strelokai.streamlit.app**

The solver is validated against an independent implementation (py_ballisticcalc, same BRL/JBM
drag tables): velocities match to <1 % and drop to ~2 % out to 1000 m (`tests/`).

---

## Layout

```
StrelokAI/
├── app.py                      # Entry point: settings sidebar + tabs
├── config.py                   # Constants, default location, version
├── auth.py                     # Username/password accounts (Firestore)
├── profiles.py                 # Rifle / cartridge profile persistence (Firestore)
│
├── core/
│   ├── state.py                # Session-state defaults
│   ├── units.py                # Metric/imperial + MRAD/MOA + click formatting
│   ├── solve.py                # ONE cached solver call shared by every tab
│   ├── secrets.py              # Safe st.secrets access (app runs without secrets.toml)
│   ├── firestore_client.py     # Firestore client + "is configured" check
│   ├── session_persist.py      # Signed "stay logged in" cookie
│   ├── google_auth.py          # Google OAuth flow
│   ├── theme.py                # CSS
│   └── url_handler.py          # ?heading= query param
│
├── components/                 # UI
│   ├── sidebar_auth.py         # Login / sign-up / Google
│   ├── sidebar_profiles.py     # Rifle & ammo editor (unit-aware), bullet library, save/load
│   ├── target_wind.py          # Distance, quick ranges, angle/cant, wind, phone compass
│   ├── atmosphere.py           # Location (+ browser geolocation), weather sync, atmosphere
│   ├── solution.py             # Clicks / MRAD / MOA solution, graph, MV truing
│   ├── dope_card.py            # Range card + CSV
│   ├── reticle.py              # Holdover on a MIL reticle + scope photo recognition
│   ├── turret.py               # Turret dial view
│   ├── range_estimator.py      # Reticle rangefinder
│   ├── compass/index.html      # Custom component: device compass
│   └── geolocation/index.html  # Custom component: browser geolocation
│
├── ballistics/                 # Physics engine (pure Python, no Streamlit)
│   ├── solver.py               # RK4 point-mass solver
│   ├── atmosphere.py           # Air density / speed of sound
│   ├── drag_models.py          # G1/G7 tables (BRL/JBM)
│   ├── cdm.py, mv_curve.py, truing.py, dope_card.py, bc_tables.py, bullet_library.py
│
├── ai/
│   ├── weather_api.py          # Open-Meteo (free, no key)
│   └── scope_recognition.py    # Gemini scope identification
│
├── data/bullet_library.json    # Published bullet presets
└── tests/                      # pytest suite incl. reference-table validation
```

## Conventions

- The solver is always metric. Unit conversion happens only in `core/units.py` at the
  widget/display boundary (`input_*_to_*`, `fmt_*`, `roundtrip`).
- Every tab renders the same solution from `core/solve.py` (`solve_current()`), so the
  Calculator, Reticle and Turret never disagree. Wind is stored as the direction it blows
  FROM (meteorological, absolute); `solve.py` converts it relative to the shooting direction.
- All secret lookups go through `core/secrets.py`. Every integration is optional and the app
  must keep working when a section is missing.

---

## Configuration (all optional)

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in what you use:

| Section | Enables |
|---|---|
| `[gcp_service_account]` | Accounts and saved rifle/ammo profiles (Firestore) |
| `[auth] cookie_secret` | "Stay logged in" cookies that survive server restarts |
| `[google]` | Sign in with Google |
| `GEMINI_API_KEY` | Scope identification from a photo |

Without any secrets the calculator, dope card, reticle, turret and rangefinder all work; the
sidebar simply says that accounts are not configured.

---

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with `pytest` (install `py_ballisticcalc` too to enable the cross-check test).

Or use the included Windows launcher:
```bash
START.bat
```

---

## AI Iteration Workflow

When using an LLM to make changes:

1. **Identify the file** from the table above that needs modification
2. **Send only that file** (+ `app.py` if layout changes are needed) to the LLM
3. **After changes**, bump the file version in both the file header and this README table
4. **Check** if the README description for that file still matches — update if needed

This keeps each AI interaction under ~200 lines instead of 700+, saving significant token costs.
