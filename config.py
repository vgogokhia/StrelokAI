"""
StrelokAI Configuration
Add your API keys here or use environment variables
Version: 1.0.0
"""
import os

# API keys — never hardcode. Loaded from .streamlit/secrets.toml (written
# from the STREAMLIT_SECRETS_TOML variable on Railway, see deploy/start.sh)
# or from environment variables.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")

# Default location (Tbilisi, Georgia)
DEFAULT_LATITUDE = 41.7151
DEFAULT_LONGITUDE = 44.8271

# App settings
APP_NAME = "ballistics.ge"
SITE_URL = "https://ballistics.ge"
TAGLINE = "Ballistic calculator for precision shooters — MRAD/MOA, .308, .22 LR, dope cards"
VERSION = "0.9.0"

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
