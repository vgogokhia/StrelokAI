"""
Weather API integration for ballistics.ge
Uses Open-Meteo API (free, no registration required).
Version: 1.1.0 - returns None on failure (no silent fake data), adds elevation
"""
import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherData:
    """Weather data from API"""
    temperature_c: float
    pressure_mbar: float       # station (surface) pressure
    humidity_pct: float
    wind_speed_mps: float
    wind_direction_deg: float  # meteorological: direction wind comes FROM
    description: str
    location_name: str
    elevation_m: float = 0.0

    @property
    def temperature_f(self) -> float:
        return self.temperature_c * 9 / 5 + 32


def get_weather(latitude: float, longitude: float) -> Optional[WeatherData]:
    """Fetch current conditions from Open-Meteo.

    Returns ``None`` when the request fails so the caller can tell the user
    instead of silently overwriting their inputs with defaults.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,surface_pressure,"
                       "wind_speed_10m,wind_direction_10m",
            "wind_speed_unit": "ms",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current") or {}
        if "temperature_2m" not in current:
            return None
        return WeatherData(
            temperature_c=float(current.get("temperature_2m", 15.0)),
            pressure_mbar=float(current.get("surface_pressure", 1013.25)),
            humidity_pct=float(current.get("relative_humidity_2m", 50.0)),
            wind_speed_mps=float(current.get("wind_speed_10m", 0.0)),
            wind_direction_deg=float(current.get("wind_direction_10m", 0.0)),
            description="Live data from Open-Meteo",
            location_name=f"{latitude:.3f}, {longitude:.3f}",
            elevation_m=float(data.get("elevation", 0.0) or 0.0),
        )
    except Exception as e:  # network, JSON, HTTP errors
        print(f"Weather API error: {e}")
        return None
