"""
Weather API integration for StrelokAI
Uses Open-Meteo API (FREE, no registration required!)
"""
import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherData:
    """Weather data from API"""
    temperature_c: float
    pressure_mbar: float
    humidity_pct: float
    wind_speed_mps: float
    wind_direction_deg: float
    description: str
    location_name: str
    
    @property
    def temperature_f(self) -> float:
        return self.temperature_c * 9/5 + 32


def get_weather(
    latitude: float, 
    longitude: float
) -> Optional[WeatherData]:
    """
    Get current weather conditions from Open-Meteo API (FREE, no API key needed!)
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        
    Returns:
        WeatherData object or None if request fails
    """
    try:
        # Open-Meteo free API - no registration required
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m",
            "wind_speed_unit": "ms"  # meters per second
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        
        return WeatherData(
            temperature_c=current.get("temperature_2m", 15.0),
            pressure_mbar=current.get("surface_pressure", 1013.25),
            humidity_pct=current.get("relative_humidity_2m", 50.0),
            wind_speed_mps=current.get("wind_speed_10m", 0.0),
            wind_direction_deg=current.get("wind_direction_10m", 0.0),
            description="Live data from Open-Meteo",
            location_name=f"{latitude:.2f}°N, {longitude:.2f}°E"
        )
        
    except Exception as e:
        print(f"Weather API error: {e}")
        # Return fallback data
        return WeatherData(
            temperature_c=15.0,
            pressure_mbar=1013.25,
            humidity_pct=50.0,
            wind_speed_mps=0.0,
            wind_direction_deg=0.0,
            description="Offline - using defaults",
            location_name="Unknown"
        )


if __name__ == "__main__":
    # Test with Tbilisi coordinates
    weather = get_weather(41.6941, 44.8337)
    if weather:
        print(f"Location: {weather.location_name}")
        print(f"Temperature: {weather.temperature_c:.1f}°C")
        print(f"Pressure: {weather.pressure_mbar:.1f} mbar")
        print(f"Humidity: {weather.humidity_pct:.0f}%")
        print(f"Wind: {weather.wind_speed_mps:.1f} m/s from {weather.wind_direction_deg:.0f}°")
        print(f"Status: {weather.description}")
