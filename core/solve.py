"""
StrelokAI - Shared "solve the current state" helper.

Every tab (Calculator, Reticle, Turret) used to call the solver on its
own, each with a slightly different set of inputs — the Calculator used
wind relative to the shooting direction, while Reticle/Turret passed the
absolute wind direction, so the same target showed different holds on
different tabs. This module is the single source of truth: it reads the
session state, derives relative wind, azimuth and latitude, and returns
one cached solution that every tab renders.
Version: 1.0.0
"""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from ballistics.solver import calculate_solution, BallisticSolution
from ballistics.mv_curve import apply_mv_curve
from config import DEFAULT_LATITUDE


@dataclass
class CurrentInputs:
    """Snapshot of everything the solver needs, in metric."""
    muzzle_velocity: float      # temperature-compensated MV, m/s
    base_mv: float
    mv_temp_c: float
    drag_model: str
    bc_val: float
    mass_grains: float
    diameter: float
    zero_range: float
    target_range: float
    temp_c: float
    pressure: float
    humidity: float
    altitude: float
    wind_speed: float
    wind_deg_relative: float    # wind FROM, relative to shooting direction
    bullet_length_in: float
    twist_rate_inches: float
    twist_direction: str
    sight_height_mm: float
    elevation_angle_deg: float
    cant_angle_deg: float
    latitude_deg: float
    azimuth_deg: float


def _q(value: float, step: float) -> float:
    """Quantize to reduce cache-key churn on tiny widget jitter."""
    return round(value / step) * step


def relative_wind_deg() -> float:
    """Wind direction relative to the shooting direction (0 = headwind)."""
    wind_from = float(st.session_state.get("wind_dir_deg", 270.0))
    heading = float(st.session_state.get("compass_heading", 0.0))
    return (wind_from - heading) % 360


def gather_inputs() -> CurrentInputs:
    p = st.session_state.profile
    ss = st.session_state
    temp_c = float(ss.get("temp_c", 15.0))
    base_mv = float(p["muzzle_velocity"])
    mv_temp_c = float(p.get("mv_temp_c", 15.0))
    actual_mv = apply_mv_curve(
        base_mv=base_mv,
        base_temp_c=mv_temp_c,
        current_temp_c=temp_c,
        temp_sensitivity_pct_per_c=float(p.get("temp_sensitivity", 0.1)),
        mv_curve=p.get("mv_curve"),
    )
    return CurrentInputs(
        muzzle_velocity=actual_mv,
        base_mv=base_mv,
        mv_temp_c=mv_temp_c,
        drag_model=p.get("drag_model", "G7"),
        bc_val=float(p["bc_g7"]),
        mass_grains=float(p["mass_grains"]),
        diameter=float(p["diameter"]),
        zero_range=float(p["zero_range"]),
        target_range=float(ss.get("target_range", 500)),
        temp_c=temp_c,
        pressure=float(ss.get("pressure", 1013.0)),
        humidity=float(ss.get("humidity", 50.0)),
        altitude=float(ss.get("altitude_m", 0.0)),
        wind_speed=float(ss.get("wind_speed", 0.0)),
        wind_deg_relative=relative_wind_deg(),
        bullet_length_in=float(p.get("bullet_length_in", 1.0)),
        twist_rate_inches=float(p.get("twist_rate", 10.0)),
        twist_direction=p.get("twist_direction", "right"),
        sight_height_mm=float(p.get("sight_height", 40.0)),
        elevation_angle_deg=float(ss.get("shot_angle_deg", 0.0)),
        cant_angle_deg=float(ss.get("cant_angle_deg", 0.0)),
        latitude_deg=float(ss.get("location_lat", DEFAULT_LATITUDE)),
        azimuth_deg=float(ss.get("compass_heading", 0.0)),
    )


@st.cache_data(ttl=600, show_spinner=False, max_entries=256)
def _cached_solution(**kw) -> BallisticSolution:
    return calculate_solution(
        muzzle_velocity_mps=kw["muzzle_velocity"],
        bc_g7=kw["bc_val"] if kw["drag_model"] == "G7" else None,
        bc_g1=kw["bc_val"] if kw["drag_model"] == "G1" else None,
        mass_grains=kw["mass_grains"],
        diameter_inches=kw["diameter"],
        zero_range_m=kw["zero_range"],
        target_range_m=kw["target_range"],
        temperature_c=kw["temp_c"],
        pressure_mbar=kw["pressure"],
        humidity_pct=kw["humidity"],
        altitude_m=kw["altitude"],
        wind_speed_mps=kw["wind_speed"],
        wind_direction_deg=kw["wind_deg_relative"],
        latitude_deg=kw["latitude_deg"],
        azimuth_deg=kw["azimuth_deg"],
        bullet_length_in=kw["bullet_length_in"],
        twist_rate_inches=kw["twist_rate_inches"],
        twist_direction=kw["twist_direction"],
        sight_height_mm=kw["sight_height_mm"],
        elevation_angle_deg=kw["elevation_angle_deg"],
        cant_angle_deg=kw["cant_angle_deg"],
    )


def solve_current() -> tuple[CurrentInputs, BallisticSolution]:
    """Solve for the current session state (cached)."""
    i = gather_inputs()
    solution = _cached_solution(
        muzzle_velocity=_q(i.muzzle_velocity, 0.1),
        drag_model=i.drag_model,
        bc_val=_q(i.bc_val, 0.001),
        mass_grains=_q(i.mass_grains, 0.1),
        diameter=_q(i.diameter, 0.001),
        zero_range=_q(i.zero_range, 1.0),
        target_range=_q(i.target_range, 1.0),
        temp_c=_q(i.temp_c, 0.1),
        pressure=_q(i.pressure, 0.1),
        humidity=_q(i.humidity, 1.0),
        altitude=_q(i.altitude, 1.0),
        wind_speed=_q(i.wind_speed, 0.1),
        wind_deg_relative=_q(i.wind_deg_relative, 1.0),
        bullet_length_in=_q(i.bullet_length_in, 0.01),
        twist_rate_inches=_q(i.twist_rate_inches, 0.1),
        twist_direction=i.twist_direction,
        sight_height_mm=_q(i.sight_height_mm, 0.5),
        elevation_angle_deg=_q(i.elevation_angle_deg, 0.5),
        cant_angle_deg=_q(i.cant_angle_deg, 0.5),
        latitude_deg=_q(i.latitude_deg, 0.1),
        azimuth_deg=_q(i.azimuth_deg, 5.0),
    )
    return i, solution
