# StrelokAI - AI-Powered Ballistic Calculator

## Overview

**StrelokAI** is an AI-powered external ballistic calculator built with [Streamlit](https://streamlit.io). It computes elevation and windage adjustments for long-range shooting, and integrates live weather data, phone compass heading, scope recognition via AI, and user profile persistence.

The application is deployed at: **https://strelokai.streamlit.app**

---

## Architecture

The codebase is split into small, focused modules for efficient AI-assisted development. Each file can be sent to an LLM independently for targeted changes, minimizing token usage per iteration.

```
StrelokAI/
├── app.py                          # Entry point: layout skeleton, assembles all components
├── config.py                       # API keys, constants, default units, solver settings
├── auth.py                         # File-based user authentication (SHA-256 hashing)
├── profiles.py                     # Rifle/Cartridge/Full profile dataclasses & persistence
├── requirements.txt                # Python dependencies
├── START.bat                       # Windows launcher script
│
├── core/                           # Application infrastructure
│   ├── __init__.py
│   ├── state.py                    # Session state initialization for all variables
│   ├── theme.py                    # CSS theme injection (Dark, Red/NVG modes)
│   └── url_handler.py              # URL query parameter processing (compass heading)
│
├── components/                     # UI rendering modules (each is a self-contained widget)
│   ├── __init__.py
│   ├── sidebar_auth.py             # Login/Signup forms (Email + Google OAuth)
│   ├── sidebar_profiles.py         # Profile editor, save/load controls
│   ├── target_wind.py              # Target distance slider, wind inputs, compass widget
│   ├── atmosphere.py               # Weather sync API, temperature/pressure/humidity inputs
│   ├── solution.py                 # Ballistic calculation execution & results display
│   └── ai_features.py              # Scope recognition uploader & supported scopes list
│
├── ballistics/                     # Domain logic (physics engine)
│   ├── __init__.py                 # Exports BallisticSolver
│   ├── solver.py                   # Core ballistic solver (trajectory, drop, windage)
│   ├── atmosphere.py               # Atmospheric model (density, speed of sound)
│   └── drag_models.py              # G1/G7 drag coefficient tables
│
└── ai/                             # AI-powered features
    ├── __init__.py
    ├── weather_api.py              # OpenWeatherMap API integration
    └── scope_recognition.py        # Gemini AI scope identification from photos
```

---

## How the System Works

### 1. Entry Point (`app.py`)
The main file configures the Streamlit page, initializes session state, applies the theme, processes URL parameters, and then renders all components in order:
- **Sidebar**: Theme selector → Auth → Profiles
- **Main Area**: Target & Wind → Atmosphere → Ballistic Solution → AI Features → Footer

### 2. Core Infrastructure (`core/`)
| Module | Purpose |
|---|---|
| `state.py` | Defines all `st.session_state` defaults (profile, weather, theme, auth flags) |
| `theme.py` | Injects CSS for Dark and Red (NVG) themes via `st.markdown` |
| `url_handler.py` | Reads `?heading=` query param from phone compass and updates state |

### 3. UI Components (`components/`)
Each component renders a specific section of the app:

| Module | What it renders |
|---|---|
| `sidebar_auth.py` | Email login/signup + Google OAuth in sidebar |
| `sidebar_profiles.py` | Rifle/bullet parameter inputs + Save/Load profile controls |
| `target_wind.py` | Target distance slider with ±5 buttons, wind speed/direction, HTML compass widget |
| `atmosphere.py` | Weather sync button + manual temp/pressure/humidity/altitude inputs |
| `solution.py` | Calls `calculate_solution()`, displays elevation/windage clicks + trajectory table |
| `ai_features.py` | Scope photo uploader + list of supported scopes |

### 4. Ballistics Engine (`ballistics/`)
Pure Python physics engine:
- **`solver.py`**: Takes projectile, rifle, wind, and atmospheric parameters → computes trajectory points with drop (MRAD), windage, velocity, energy, time of flight
- **`atmosphere.py`**: Calculates air density and speed of sound from temperature, pressure, humidity, altitude
- **`drag_models.py`**: G1 and G7 drag coefficient lookup tables

### 5. AI Features (`ai/`)
- **`weather_api.py`**: Fetches live weather from OpenWeatherMap API (temperature, pressure, humidity, wind)
- **`scope_recognition.py`**: Uses Google Gemini API to identify rifle scopes from photos and return specs (click value, max elevation, reticle options)

### 6. Authentication & Profiles (`auth.py`, `profiles.py`)
- **`auth.py`**: File-based auth with SHA-256 + salt hashing. User data stored in `~/.strelokai/users.json`
- **`profiles.py`**: Dataclass-based profile system. Saves rifle/cartridge/full profiles as JSON in per-user directories

---

## File Version Registry

> **How to use**: After modifying a file, increment its version below. When reviewing this README, check if the description for that file still matches the new version — if not, update the corresponding section above.

| File | Version | Last Updated | Description |
|---|---|---|---|
| `app.py` | 1.0.0 | 2026-03-06 | Entry point, layout skeleton |
| `config.py` | 1.0.0 | 2026-03-06 | API keys, app constants, solver defaults |
| `auth.py` | 1.0.0 | 2026-03-06 | User authentication (create, login, verify) |
| `profiles.py` | 1.0.0 | 2026-03-06 | Profile dataclasses & CRUD operations |
| `core/state.py` | 1.0.0 | 2026-03-06 | Session state initialization |
| `core/theme.py` | 1.0.0 | 2026-03-06 | CSS theme definitions (Dark, Red) |
| `core/url_handler.py` | 1.0.0 | 2026-03-06 | URL query parameter processing |
| `components/sidebar_auth.py` | 1.0.0 | 2026-03-06 | Sidebar login/signup UI |
| `components/sidebar_profiles.py` | 1.0.0 | 2026-03-06 | Sidebar profile editor & save/load |
| `components/target_wind.py` | 1.0.0 | 2026-03-06 | Target distance & wind input controls |
| `components/atmosphere.py` | 1.0.0 | 2026-03-06 | Weather sync & atmospheric inputs |
| `components/solution.py` | 1.0.0 | 2026-03-06 | Ballistic calculation & results display |
| `components/ai_features.py` | 1.0.0 | 2026-03-06 | AI scope recognition UI |
| `ballistics/solver.py` | 1.0.0 | 2026-03-06 | Core ballistic trajectory solver |
| `ballistics/atmosphere.py` | 1.0.0 | 2026-03-06 | Atmospheric model calculations |
| `ballistics/drag_models.py` | 1.0.0 | 2026-03-06 | G1/G7 drag coefficient tables |
| `ai/weather_api.py` | 1.0.0 | 2026-03-06 | OpenWeatherMap API integration |
| `ai/scope_recognition.py` | 1.0.0 | 2026-03-06 | Gemini AI scope identification |

---

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

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
