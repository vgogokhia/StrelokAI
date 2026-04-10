"""
StrelokAI - Unit System Formatters
Centralized formatters that respect ``st.session_state.units``
("metric" | "imperial"). Use these helpers anywhere user-facing
numbers are rendered so the toggle flips everything consistently.

Internally, the solver always works in metric. These helpers convert
only at display time.
"""
from typing import Literal

import streamlit as st

UnitSystem = Literal["metric", "imperial"]

_MPS_TO_FPS = 3.28084
_FPS_TO_MPS = 1 / _MPS_TO_FPS
_M_TO_YD = 1.09361
_YD_TO_M = 1 / _M_TO_YD
_KG_TO_LB = 2.20462
_MBAR_TO_INHG = 0.02953
_INHG_TO_MBAR = 1 / _MBAR_TO_INHG
_MPH_TO_MPS = 0.44704
_MPS_TO_MPH = 1 / _MPH_TO_MPS
_M_TO_FT = 3.28084
_FT_TO_M = 1 / _M_TO_FT


def current_system() -> UnitSystem:
    return st.session_state.get("units", "metric")


def is_imperial() -> bool:
    return current_system() == "imperial"


# --- Distance --------------------------------------------------------------

def fmt_range(meters: float, precision: int = 0) -> str:
    if is_imperial():
        return f"{meters * _M_TO_YD:.{precision}f} yd"
    return f"{meters:.{precision}f} m"


def fmt_distance_short(meters: float) -> str:
    """Short inline form without unit suffix — handy for table cells."""
    return f"{meters * _M_TO_YD:.0f}" if is_imperial() else f"{meters:.0f}"


def range_label() -> str:
    return "yd" if is_imperial() else "m"


# --- Velocity --------------------------------------------------------------

def fmt_velocity(mps: float, precision: int = 0) -> str:
    if is_imperial():
        return f"{mps * _MPS_TO_FPS:.{precision}f} fps"
    return f"{mps:.{precision}f} m/s"


def velocity_label() -> str:
    return "fps" if is_imperial() else "m/s"


# --- Temperature -----------------------------------------------------------

def fmt_temperature(celsius: float, precision: int = 0) -> str:
    if is_imperial():
        return f"{celsius * 9 / 5 + 32:.{precision}f} °F"
    return f"{celsius:.{precision}f} °C"


# --- Pressure --------------------------------------------------------------

def fmt_pressure(mbar: float) -> str:
    if is_imperial():
        return f"{mbar * _MBAR_TO_INHG:.2f} inHg"
    return f"{mbar:.0f} mbar"


# --- Energy ----------------------------------------------------------------

def fmt_energy(joules: float) -> str:
    if is_imperial():
        # 1 J = 0.737562 ft·lbf
        return f"{joules * 0.737562:.0f} ft·lb"
    return f"{joules:.0f} J"


# --- Input-side converters (imperial user-input → metric internal) ----------

def input_range_to_m(value: float) -> float:
    """Convert a range from the user's unit system to metres."""
    return value * _YD_TO_M if is_imperial() else value


def input_range_from_m(meters: float) -> float:
    """Convert metres to the user's display unit for pre-filling inputs."""
    return meters * _M_TO_YD if is_imperial() else meters


def input_speed_to_mps(value: float) -> float:
    """Convert wind speed from user's unit (mph/m/s) to m/s."""
    return value * _MPH_TO_MPS if is_imperial() else value


def input_speed_from_mps(mps: float) -> float:
    return mps * _MPS_TO_MPH if is_imperial() else mps


def input_temp_to_c(value: float) -> float:
    return (value - 32) * 5 / 9 if is_imperial() else value


def input_temp_from_c(celsius: float) -> float:
    return celsius * 9 / 5 + 32 if is_imperial() else celsius


def input_pressure_to_mbar(value: float) -> float:
    return value * _INHG_TO_MBAR if is_imperial() else value


def input_pressure_from_mbar(mbar: float) -> float:
    return mbar * _MBAR_TO_INHG if is_imperial() else mbar


def input_alt_to_m(value: float) -> float:
    return value * _FT_TO_M if is_imperial() else value


def input_alt_from_m(meters: float) -> float:
    return meters * _M_TO_FT if is_imperial() else meters


def speed_label() -> str:
    return "mph" if is_imperial() else "m/s"


def temp_label() -> str:
    return "°F" if is_imperial() else "°C"


def pressure_label() -> str:
    return "inHg" if is_imperial() else "mbar"


def alt_label() -> str:
    return "ft" if is_imperial() else "m"
