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
_M_TO_YD = 1.09361
_KG_TO_LB = 2.20462
_MBAR_TO_INHG = 0.02953


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
