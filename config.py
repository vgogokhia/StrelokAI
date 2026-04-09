"""
StrelokAI Configuration
Add your API keys here or use environment variables
Version: 1.0.0
"""
import os

# API Keys — NEVER hardcode. Load from env / Streamlit secrets only.
# On Streamlit Cloud, set these under "Manage app → Secrets" as TOML:
#   GEMINI_API_KEY = "your-key"
#   OPENWEATHERMAP_API_KEY = "your-key"
# Streamlit Cloud exposes st.secrets entries as env vars automatically.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")

# Default location (Tbilisi, Georgia)
DEFAULT_LATITUDE = 41.7151
DEFAULT_LONGITUDE = 44.8271

# App settings
APP_NAME = "StrelokAI"
VERSION = "0.5.14"

# Unit preferences
DEFAULT_DISTANCE_UNIT = "meters"  # meters or yards
DEFAULT_VELOCITY_UNIT = "mps"     # mps (m/s) or fps (ft/s)
DEFAULT_ANGLE_UNIT = "mrad"       # mrad or moa
DEFAULT_TEMP_UNIT = "celsius"     # celsius or fahrenheit
DEFAULT_PRESSURE_UNIT = "mbar"    # mbar or inhg

# Solver settings
STANDARD_ATMOSPHERE = {
    "temperature_c": 15.0,
    "pressure_mbar": 1013.25,
    "humidity_pct": 0.0,
    "altitude_m": 0.0,
}
