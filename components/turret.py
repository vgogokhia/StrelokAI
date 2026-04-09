"""
StrelokAI - Turret Visualization
Simple SVG clock-face showing the elevation dial position for the
current solution.
Version: 1.0.0
"""
import math
import streamlit as st
import streamlit.components.v1 as components

from ballistics.solver import calculate_solution
from config import DEFAULT_LATITUDE


_SIZE = 320
_TURRET_RANGE_MRAD = 15.0  # full rotation = 15 mrad (matches common MIL turrets)


def _turret_svg(elev_mrad: float) -> str:
    cx = cy = _SIZE / 2
    r = _SIZE / 2 - 10
    # Normalize elevation to a positive value (we only dial up)
    val = max(0.0, abs(elev_mrad))
    frac = (val % _TURRET_RANGE_MRAD) / _TURRET_RANGE_MRAD
    # 0 at top (12 o'clock), clockwise
    angle_deg = -90 + frac * 360
    nx = cx + r * 0.82 * math.cos(math.radians(angle_deg))
    ny = cy + r * 0.82 * math.sin(math.radians(angle_deg))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SIZE}" height="{_SIZE}" '
        f'viewBox="0 0 {_SIZE} {_SIZE}" style="background:#0a0a0a;border-radius:50%;">',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#101010" stroke="#3a3a3a" stroke-width="2"/>',
    ]
    # Tick marks and labels every 1 mrad
    for i in range(int(_TURRET_RANGE_MRAD)):
        a = -90 + (i / _TURRET_RANGE_MRAD) * 360
        x1 = cx + (r - 4) * math.cos(math.radians(a))
        y1 = cy + (r - 4) * math.sin(math.radians(a))
        x2 = cx + (r - 16) * math.cos(math.radians(a))
        y2 = cy + (r - 16) * math.sin(math.radians(a))
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#8a8" stroke-width="2"/>')
        lx = cx + (r - 30) * math.cos(math.radians(a))
        ly = cy + (r - 30) * math.sin(math.radians(a)) + 4
        parts.append(f'<text x="{lx}" y="{ly}" fill="#8a8" font-size="12" font-family="monospace" text-anchor="middle">{i}</text>')

    # Minor ticks at 0.1 mrad
    for j in range(int(_TURRET_RANGE_MRAD * 10)):
        a = -90 + (j / (_TURRET_RANGE_MRAD * 10)) * 360
        x1 = cx + (r - 4) * math.cos(math.radians(a))
        y1 = cy + (r - 4) * math.sin(math.radians(a))
        x2 = cx + (r - 10) * math.cos(math.radians(a))
        y2 = cy + (r - 10) * math.sin(math.radians(a))
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#4a4" stroke-width="1"/>')

    # Pointer from centre
    parts.append(
        f'<line x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}" stroke="#ff3030" stroke-width="3"/>'
    )
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#ff3030"/>')
    parts.append(
        f'<text x="{cx}" y="{cy + 50}" fill="#fff" font-size="18" font-family="monospace" text-anchor="middle">{val:.2f} MRAD</text>'
    )
    parts.append('</svg>')
    return ''.join(parts)


def render_turret():
    st.markdown("### 🎛️ Turret Dial")
    st.caption("Shows the elevation dial position for the current target range.")

    profile = st.session_state.profile
    target_range = float(st.session_state.get("target_range", 500))

    try:
        solution = calculate_solution(
            muzzle_velocity_mps=profile["muzzle_velocity"],
            bc_g7=profile["bc_g7"] if profile.get("drag_model", "G7") == "G7" else None,
            bc_g1=profile["bc_g7"] if profile.get("drag_model", "G7") == "G1" else None,
            mass_grains=profile["mass_grains"],
            diameter_inches=profile["diameter"],
            zero_range_m=profile["zero_range"],
            target_range_m=target_range,
            temperature_c=float(st.session_state.get("temp_c", 15.0)),
            pressure_mbar=float(st.session_state.get("pressure", 1013.0)),
            humidity_pct=float(st.session_state.get("humidity", 50.0)),
            wind_speed_mps=float(st.session_state.get("wind_speed", 0.0)),
            wind_direction_deg=float(st.session_state.get("wind_dir_deg", 270.0)),
            latitude_deg=DEFAULT_LATITUDE,
            bullet_length_in=profile.get("bullet_length_in", 1.0),
            twist_rate_inches=profile["twist_rate"],
            twist_direction=profile.get("twist_direction", "right"),
            sight_height_mm=profile["sight_height"],
            elevation_angle_deg=float(st.session_state.get("shot_angle_deg", 0.0)),
            cant_angle_deg=float(st.session_state.get("cant_angle_deg", 0.0)),
        )
    except Exception as exc:
        st.error(f"Solver error: {exc}")
        return

    pt = solution.at_range(target_range)
    if pt is None:
        st.warning("No trajectory point at that range.")
        return

    svg = _turret_svg(pt.drop_mrad)
    components.html(svg, height=_SIZE + 20)
    full_turns = int(abs(pt.drop_mrad) // _TURRET_RANGE_MRAD)
    remainder = abs(pt.drop_mrad) % _TURRET_RANGE_MRAD
    st.caption(
        f"Dial UP: **{abs(pt.drop_mrad):.2f} MRAD** "
        f"({full_turns} full turn{'s' if full_turns != 1 else ''} + {remainder:.2f})"
    )
