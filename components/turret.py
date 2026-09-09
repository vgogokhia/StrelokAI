"""
ballistics.ge - Turret Visualization
SVG clock-face showing the elevation dial position for the current solution.
Version: 1.1.0 - shared solver, MRAD/MOA aware
"""
import math
import streamlit as st

from core.solve import solve_current
from core.units import angular_unit, to_angular, fmt_angular, clicks_for, fmt_range


_SIZE = 320


def _turret_svg(val: float, per_rev: float, unit: str) -> str:
    cx = cy = _SIZE / 2
    r = _SIZE / 2 - 10
    frac = (val % per_rev) / per_rev
    angle_deg = -90 + frac * 360
    nx = cx + r * 0.82 * math.cos(math.radians(angle_deg))
    ny = cy + r * 0.82 * math.sin(math.radians(angle_deg))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SIZE}" height="{_SIZE}" '
        f'viewBox="0 0 {_SIZE} {_SIZE}" style="background:#0a0a0a;">',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#101010" stroke="#3a3a3a" stroke-width="2"/>',
    ]
    major = int(per_rev)
    minor_per_major = 10 if unit == "MRAD" else 4
    for i in range(major):
        a = -90 + (i / per_rev) * 360
        x1 = cx + (r - 4) * math.cos(math.radians(a)); y1 = cy + (r - 4) * math.sin(math.radians(a))
        x2 = cx + (r - 16) * math.cos(math.radians(a)); y2 = cy + (r - 16) * math.sin(math.radians(a))
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#8a8" stroke-width="2"/>')
        lx = cx + (r - 30) * math.cos(math.radians(a)); ly = cy + (r - 30) * math.sin(math.radians(a)) + 4
        parts.append(f'<text x="{lx}" y="{ly}" fill="#8a8" font-size="12" font-family="monospace" text-anchor="middle">{i}</text>')
    for j in range(major * minor_per_major):
        a = -90 + (j / (per_rev * minor_per_major)) * 360
        x1 = cx + (r - 4) * math.cos(math.radians(a)); y1 = cy + (r - 4) * math.sin(math.radians(a))
        x2 = cx + (r - 10) * math.cos(math.radians(a)); y2 = cy + (r - 10) * math.sin(math.radians(a))
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#4a4" stroke-width="1"/>')
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}" stroke="#ff3030" stroke-width="3"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#ff3030"/>')
    parts.append(
        f'<text x="{cx}" y="{cy + 50}" fill="#fff" font-size="18" font-family="monospace" text-anchor="middle">{val:.2f} {unit}</text>'
    )
    parts.append('</svg>')
    return ''.join(parts)


def render_turret():
    st.markdown("### 🎛️ Turret Dial")
    st.caption("Elevation dial position for the current target range (same solution as the Calculator tab).")

    unit = angular_unit()
    per_rev = st.number_input(
        f"{unit} per turret revolution", min_value=1.0, max_value=60.0,
        value=float(st.session_state.get("turret_per_rev", 10.0 if unit == "MRAD" else 25.0)),
        step=1.0, key="turret_per_rev_input",
        help="Printed on your turret, e.g. 10 MRAD/rev or 25 MOA/rev.",
    )
    st.session_state.turret_per_rev = per_rev

    try:
        inputs, solution = solve_current()
    except Exception as exc:
        st.error(f"Solver error: {exc}")
        return

    pt = solution.at_range(inputs.target_range)
    if pt is None:
        st.warning("No trajectory point at that range.")
        return

    val = abs(to_angular(pt.drop_mrad))
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        st.image(_turret_svg(val, per_rev, unit), width="stretch")
    full_turns = int(val // per_rev)
    remainder = val % per_rev
    direction = "UP" if pt.drop_mrad < 0 else "DOWN"
    st.caption(
        f"{fmt_range(inputs.target_range)} → dial **{direction} {fmt_angular(pt.drop_mrad).replace('-', '')}** "
        f"= **{clicks_for(pt.drop_mrad)} clicks** "
        f"({full_turns} full turn{'s' if full_turns != 1 else ''} + {remainder:.2f} {unit})"
    )
