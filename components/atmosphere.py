"""
ballistics.ge - Atmosphere & Weather Component
Weather sync (Open-Meteo, for the user's own location) and atmospheric inputs.
Version: 1.3.0 - location picker + browser geolocation, honest failure handling
"""
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE
from ai.weather_api import get_weather
from ballistics.atmosphere import Atmosphere, AtmosphericConditions
from core.units import (
    is_imperial, fmt_temperature, fmt_pressure, fmt_velocity,
    temp_label, pressure_label, alt_label,
    input_temp_from_c, input_temp_to_c,
    input_pressure_from_mbar, input_pressure_to_mbar,
    input_alt_from_m, input_alt_to_m, roundtrip,
)

_geo_component = components.declare_component(
    "geolocation_widget", path=str(Path(__file__).parent / "geolocation")
)


def _atmosphere_summary(temp_c: float, pressure: float, humidity: float, altitude: float) -> str:
    """One-liner with density altitude, air density, speed of sound."""
    try:
        atm = Atmosphere(AtmosphericConditions(
            temperature_c=temp_c, pressure_mbar=pressure,
            humidity_pct=humidity, altitude_m=altitude,
        ))
        da_ft = atm.density_altitude_ft()
        rho = atm.air_density()
        sos = atm.speed_of_sound()
        return (
            f"**DA** {da_ft:,.0f} ft  |  **ρ** {rho:.3f} kg/m³  |  "
            f"**a** {fmt_velocity(sos)}  |  **T** {fmt_temperature(temp_c)}  |  "
            f"**P** {fmt_pressure(pressure)}"
        )
    except Exception:
        return f"T {fmt_temperature(temp_c)} | P {fmt_pressure(pressure)} | RH {humidity:.0f}%"


def _apply_weather(weather) -> None:
    st.session_state.temp_c = float(weather.temperature_c)
    st.session_state.pressure = float(weather.pressure_mbar)
    st.session_state.humidity = float(weather.humidity_pct)
    st.session_state.wind_speed = float(weather.wind_speed_mps)
    st.session_state.wind_dir_deg = float(weather.wind_direction_deg)
    if weather.elevation_m:
        st.session_state.altitude_m = float(weather.elevation_m)
    st.session_state.weather_status = (
        f"✅ {fmt_temperature(weather.temperature_c)} · {fmt_pressure(weather.pressure_mbar)} · "
        f"RH {weather.humidity_pct:.0f}% · wind {fmt_velocity(weather.wind_speed_mps)} "
        f"from {weather.wind_direction_deg:.0f}° · synced {datetime.now():%H:%M}"
    )
    st.session_state.weather_error = None


def _render_location_row():
    """Lat/lon inputs + a 'use my location' browser geolocation button."""
    geo = _geo_component(key="geo_input", default=None)
    if isinstance(geo, dict) and "lat" in geo and geo.get("ts") != st.session_state.get("_geo_ts"):
        st.session_state._geo_ts = geo.get("ts")
        st.session_state.location_lat = float(geo["lat"])
        st.session_state.location_lon = float(geo["lon"])
        if geo.get("alt") is not None:
            st.session_state.altitude_m = max(0.0, float(geo["alt"]))
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        lat = st.number_input(
            "Latitude", -90.0, 90.0,
            float(st.session_state.get("location_lat", DEFAULT_LATITUDE)),
            0.01, format="%.4f", key="loc_lat_input",
            help="Also used for the Coriolis correction.",
        )
    with c2:
        lon = st.number_input(
            "Longitude", -180.0, 180.0,
            float(st.session_state.get("location_lon", DEFAULT_LONGITUDE)),
            0.01, format="%.4f", key="loc_lon_input",
        )
    st.session_state.location_lat = lat
    st.session_state.location_lon = lon


def render_atmosphere_section():
    temp_c_cur = float(st.session_state.temp_c)
    pressure_cur = float(st.session_state.pressure)
    humidity_cur = float(st.session_state.humidity)
    altitude_cur = float(st.session_state.get("altitude_m", 0.0))
    st.caption(_atmosphere_summary(temp_c_cur, pressure_cur, humidity_cur, altitude_cur))

    with st.expander("🌡️ Atmosphere & Weather Sync", expanded=False):
        _render_location_row()

        if st.button("🌍 Sync weather for this location", type="primary", width="stretch"):
            with st.spinner("Fetching weather…"):
                weather = get_weather(
                    st.session_state.location_lat, st.session_state.location_lon
                )
            if weather is None:
                st.session_state.weather_error = (
                    "Weather service unreachable. Your current values were left unchanged — "
                    "enter conditions manually."
                )
            else:
                _apply_weather(weather)
            st.rerun()

        if st.session_state.get("weather_error"):
            st.error(st.session_state.weather_error)
        elif st.session_state.get("weather_status"):
            st.success(st.session_state.weather_status)

        imp = is_imperial()
        t_label, p_label, a_label = temp_label(), pressure_label(), alt_label()

        atm_cols = st.columns(2)
        with atm_cols[0]:
            disp_temp = input_temp_from_c(float(st.session_state.temp_c))
            t_min, t_max = (-40.0, 130.0) if imp else (-40.0, 55.0)
            t_seed = float(min(max(round(disp_temp, 1), t_min), t_max))
            temp_input = st.number_input(f"Temp ({t_label})", t_min, t_max, t_seed, 1.0)
            st.session_state.temp_c = roundtrip(st.session_state.temp_c, t_seed, temp_input, input_temp_to_c)
            temp_c = st.session_state.temp_c

            disp_press = input_pressure_from_mbar(float(st.session_state.pressure))
            p_min, p_max = (17.0, 32.5) if imp else (580.0, 1100.0)
            p_step = 0.01 if imp else 1.0
            p_fmt = "%.2f" if imp else "%.0f"
            p_seed = float(min(max(round(disp_press, 2), p_min), p_max))
            press_input = st.number_input(
                f"Station pressure ({p_label})", p_min, p_max, p_seed, p_step, format=p_fmt,
                help="Absolute pressure at the shooting site (not sea-level corrected).",
            )
            st.session_state.pressure = roundtrip(st.session_state.pressure, p_seed, press_input, input_pressure_to_mbar)
            pressure = st.session_state.pressure

        with atm_cols[1]:
            humidity = st.number_input(
                "Humidity (%)", 0.0, 100.0, float(st.session_state.humidity), 5.0,
            )
            st.session_state.humidity = humidity

            disp_alt = input_alt_from_m(float(st.session_state.get("altitude_m", 0.0)))
            a_max = 16400.0 if imp else 5000.0
            a_seed = float(min(max(round(disp_alt, 0), 0.0), a_max))
            alt_input = st.number_input(f"Altitude ({a_label})", 0.0, a_max, a_seed, 100.0)
            altitude = roundtrip(st.session_state.get("altitude_m", 0.0), a_seed, alt_input, input_alt_to_m)
            st.session_state.altitude_m = altitude

        return temp_c, pressure, humidity, altitude
