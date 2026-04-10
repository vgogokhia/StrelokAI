"""
StrelokAI - Atmosphere & Weather Component
Weather sync API integration and atmospheric override inputs.
Version: 1.2.0 - full imperial support
"""
import streamlit as st
from config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE
from ai.weather_api import get_weather
from ballistics.atmosphere import Atmosphere, AtmosphericConditions
from core.units import (
    is_imperial, fmt_temperature, fmt_pressure, fmt_velocity,
    temp_label, pressure_label, alt_label,
    input_temp_from_c, input_temp_to_c,
    input_pressure_from_mbar, input_pressure_to_mbar,
    input_alt_from_m, input_alt_to_m,
)


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
        return (
            f"**DA** {da_ft:,.0f} ft  |  **ρ** {rho:.3f} kg/m³  |  "
            f"**a** {fmt_velocity(sos)}  |  **T** {fmt_temperature(temp_c)}"
        )
    except Exception:
        return f"T {fmt_temperature(temp_c)} | P {fmt_pressure(pressure)} | RH {humidity:.0f}%"


def render_atmosphere_section():
    # Compact always-visible summary line from current state
    temp_c_cur = float(st.session_state.temp_c)
    pressure_cur = float(st.session_state.pressure)
    humidity_cur = float(st.session_state.humidity)
    altitude_cur = float(st.session_state.get("altitude_m", 0.0))
    st.caption(_atmosphere_summary(temp_c_cur, pressure_cur, humidity_cur, altitude_cur))

    with st.expander("🌡️ Atmosphere & Weather Sync", expanded=False):
        weather_clicked = st.button("🌍 Sync All Weather Data", type="primary")
        if weather_clicked:
            weather = get_weather(DEFAULT_LATITUDE, DEFAULT_LONGITUDE)
            if weather:
                st.session_state.temp_c = float(weather.temperature_c)
                st.session_state.pressure = float(weather.pressure_mbar)
                st.session_state.humidity = float(weather.humidity_pct)
                st.session_state.wind_speed = float(weather.wind_speed_mps)
                st.session_state.wind_dir_deg = float(weather.wind_direction_deg)
                st.session_state.weather_status = (
                    f"✅ {fmt_temperature(weather.temperature_c)} | "
                    f"Wind: {fmt_velocity(weather.wind_speed_mps)} from {weather.wind_direction_deg:.0f}°"
                )
                st.rerun()

        if "weather_status" in st.session_state:
            st.success(st.session_state.weather_status)

        imp = is_imperial()
        t_label = temp_label()
        p_label = pressure_label()
        a_label = alt_label()

        atm_cols = st.columns(2)
        with atm_cols[0]:
            # Temperature
            disp_temp = input_temp_from_c(float(st.session_state.temp_c))
            t_min, t_max = (-22.0, 122.0) if imp else (-30.0, 50.0)
            temp_input = st.number_input(
                f"Temp ({t_label})", t_min, t_max,
                float(round(disp_temp, 1)), 1.0,
            )
            st.session_state.temp_c = input_temp_to_c(temp_input)
            temp_c = st.session_state.temp_c

            # Pressure
            disp_press = input_pressure_from_mbar(float(st.session_state.pressure))
            p_min, p_max = (23.6, 32.5) if imp else (800.0, 1100.0)
            p_step = 0.01 if imp else 1.0
            p_fmt = "%.2f" if imp else "%.0f"
            press_input = st.number_input(
                f"Pressure ({p_label})", p_min, p_max,
                float(round(disp_press, 2)), p_step, format=p_fmt,
            )
            st.session_state.pressure = input_pressure_to_mbar(press_input)
            pressure = st.session_state.pressure

        with atm_cols[1]:
            # Humidity (unitless %)
            humidity = st.number_input(
                "Humidity (%)", 0.0, 100.0,
                float(st.session_state.humidity), 5.0,
            )
            st.session_state.humidity = humidity

            # Altitude
            disp_alt = input_alt_from_m(float(st.session_state.get("altitude_m", 0.0)))
            a_max = 16400.0 if imp else 5000.0
            a_step = 100.0 if imp else 100.0
            alt_input = st.number_input(
                f"Altitude ({a_label})", 0.0, a_max,
                float(round(disp_alt, 0)), a_step,
            )
            altitude = input_alt_to_m(alt_input)
            st.session_state.altitude_m = altitude

        return temp_c, pressure, humidity, altitude
