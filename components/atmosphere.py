"""
StrelokAI - Atmosphere & Weather Component
Weather sync API integration and atmospheric override inputs.
Version: 1.1.0
"""
import streamlit as st
from config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE
from ai.weather_api import get_weather
from ballistics.atmosphere import Atmosphere, AtmosphericConditions


def _atmosphere_summary(temp_c: float, pressure: float, humidity: float, altitude: float) -> str:
    """One-liner with density altitude, air density, speed of sound."""
    try:
        atm = Atmosphere(AtmosphericConditions(
            temperature_c=temp_c,
            pressure_mbar=pressure,
            humidity_pct=humidity,
            altitude_m=altitude,
        ))
        da_ft = atm.density_altitude_ft()
        rho = atm.air_density()
        sos = atm.speed_of_sound()
        return f"**DA** {da_ft:,.0f} ft  |  **ρ** {rho:.3f} kg/m³  |  **a** {sos:.1f} m/s  |  **T** {temp_c:.1f}°C"
    except Exception:
        return f"T {temp_c:.1f}°C | P {pressure:.0f} mbar | RH {humidity:.0f}%"


def render_atmosphere_section():
    # Compact always-visible summary line from current state
    temp_c_cur = float(st.session_state.temp_c)
    pressure_cur = float(st.session_state.pressure)
    humidity_cur = float(st.session_state.humidity)
    altitude_cur = float(st.session_state.get("altitude_m", 0.0))
    st.caption(_atmosphere_summary(temp_c_cur, pressure_cur, humidity_cur, altitude_cur))

    with st.expander("🌡️ Atmosphere & Weather Sync", expanded=False):
        # Weather sync button - now syncs wind too!
        weather_clicked = st.button("🌍 Sync All Weather Data", type="primary")
        if weather_clicked:
            weather = get_weather(DEFAULT_LATITUDE, DEFAULT_LONGITUDE)
            if weather:
                st.session_state.temp_c = float(weather.temperature_c)
                st.session_state.pressure = float(weather.pressure_mbar)
                st.session_state.humidity = float(weather.humidity_pct)
                st.session_state.wind_speed = float(weather.wind_speed_mps)
                st.session_state.wind_dir_deg = float(weather.wind_direction_deg)
                st.session_state.weather_status = f"✅ {weather.temperature_c:.1f}°C | Wind: {weather.wind_speed_mps:.1f}m/s from {weather.wind_direction_deg:.0f}°"
                st.rerun()
        
        if "weather_status" in st.session_state:
            st.success(st.session_state.weather_status)
        
        atm_cols = st.columns(2)
        with atm_cols[0]:
            temp_c = st.number_input("Temp (°C)", -30.0, 50.0, float(st.session_state.temp_c), 1.0)
            st.session_state.temp_c = temp_c
            pressure = st.number_input("Pressure (mbar)", 800.0, 1100.0, float(st.session_state.pressure), 1.0)
            st.session_state.pressure = pressure
        with atm_cols[1]:
            humidity = st.number_input("Humidity (%)", 0.0, 100.0, float(st.session_state.humidity), 5.0)
            st.session_state.humidity = humidity
            altitude = st.number_input("Altitude (m)", 0.0, 5000.0, 0.0, 100.0)
            
        return temp_c, pressure, humidity, altitude
