"""
Read a weather meter (Kestrel, WeatherFlow, station display) from a photo
with Gemini Vision and return the numbers the calculator needs.

Kestrel's Bluetooth protocol is not public and Web Bluetooth does not work
on iPhone, so a photo of the screen is the portable alternative.
Version: 1.0.0
"""
from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherReading:
    temperature_c: Optional[float] = None
    pressure_mbar: Optional[float] = None       # station pressure
    humidity_pct: Optional[float] = None
    wind_speed_mps: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    density_altitude_m: Optional[float] = None
    raw: str = ""

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "raw" and v is not None}


_PROMPT = """You are reading the display of a handheld weather meter (Kestrel 5700/5500/3500,
WeatherFlow, or a weather station) photographed by a shooter. Extract the values shown.

Return ONLY a JSON object with these keys (use null when a value is not visible):
{
  "temperature_c": number,        // convert F to C if the display shows F
  "pressure_mbar": number,        // STATION/absolute pressure in hPa/mbar (inHg * 33.8639). NOT barometric/sea-level "BARO" if a separate "STATION"/"ABS"/"PRES" is shown; if only BARO is shown, return it under "baro_mbar" instead.
  "baro_mbar": number,
  "humidity_pct": number,
  "wind_speed_mps": number,       // convert mph*0.44704, km/h/3.6, kt*0.5144
  "wind_direction_deg": number,   // direction the wind comes FROM, if shown
  "density_altitude_m": number,   // convert ft*0.3048
  "notes": string                 // anything ambiguous
}"""


def _parse(text: str) -> WeatherReading:
    m = re.search(r"\{.*\}", text, re.S)
    data = json.loads(m.group(0)) if m else {}
    def f(k):
        v = data.get(k)
        try:
            return None if v is None else float(v)
        except (TypeError, ValueError):
            return None
    pressure = f("pressure_mbar")
    if pressure is None and f("baro_mbar") is not None:
        pressure = None  # sea-level pressure would be wrong for ballistics; leave for the UI to explain
    return WeatherReading(
        temperature_c=f("temperature_c"),
        pressure_mbar=pressure,
        humidity_pct=f("humidity_pct"),
        wind_speed_mps=f("wind_speed_mps"),
        wind_direction_deg=f("wind_direction_deg"),
        density_altitude_m=f("density_altitude_m"),
        raw=text,
    )


def read_weather_photo(image_bytes: bytes, api_key: str) -> WeatherReading:
    import google.generativeai as genai
    from PIL import Image

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-flash-latest")
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    resp = model.generate_content([_PROMPT, img])
    return _parse(resp.text or "")
