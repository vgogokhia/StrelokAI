"""
StrelokAI Configuration
Add your API keys here or use environment variables
"""
import os

# API Keys (use environment variables in production)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCgT-3jBCQlM84yGhNzPWJHRTrR_0Mm6dk")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "your-openweathermap-api-key-here")

# Default location (Tbilisi, Georgia)
DEFAULT_LATITUDE = 41.7151
DEFAULT_LONGITUDE = 44.8271

# App settings
APP_NAME = "StrelokAI"
VERSION = "0.1.0"

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
