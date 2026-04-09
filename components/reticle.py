"""
StrelokAI - Reticle Holdover Visualization
Renders a MIL-based reticle with a red aiming dot at the current
(windage, drop) solution, plus a few simple reticle options.
Version: 1.0.0
"""
import streamlit as st
import streamlit.components.v1 as components

from ballistics.solver import calculate_solution
from config import DEFAULT_LATITUDE


# Reticle view spans ±10 mrad square. Bullet impact dot is placed in this frame.
_VIEW_MRAD = 10.0
_SVG_SIZE = 480  # pixels


def _mrad_to_px(mrad: float) -> float:
    return (mrad / _VIEW_MRAD) * (_SVG_SIZE / 2)


def _mildot_svg(x_mrad: float, y_mrad: float) -> str:
    """Standard MIL-Dot reticle: dots at every 1 mrad on main crosshair."""
    cx = _SVG_SIZE / 2
    cy = _SVG_SIZE / 2
    px = _mrad_to_px(x_mrad) + cx
    py = _mrad_to_px(y_mrad) + cy

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SVG_SIZE}" height="{_SVG_SIZE}" '
        f'viewBox="0 0 {_SVG_SIZE} {_SVG_SIZE}" style="background:#0a0a0a;">',
        f'<circle cx="{cx}" cy="{cy}" r="{_SVG_SIZE/2 - 2}" fill="none" stroke="#1a1a1a" stroke-width="2"/>',
        # main crosshair
        f'<line x1="{cx - _SVG_SIZE/2 + 20}" y1="{cy}" x2="{cx + _SVG_SIZE/2 - 20}" y2="{cy}" stroke="#8a8" stroke-width="1"/>',
        f'<line x1="{cx}" y1="{cy - _SVG_SIZE/2 + 20}" x2="{cx}" y2="{cy + _SVG_SIZE/2 - 20}" stroke="#8a8" stroke-width="1"/>',
    ]
    # mil dots and labels
    for m in range(-9, 10):
        if m == 0:
            continue
        dx = _mrad_to_px(m) + cx
        dy = _mrad_to_px(m) + cy
        parts.append(f'<circle cx="{dx}" cy="{cy}" r="2.5" fill="#8a8"/>')
        parts.append(f'<circle cx="{cx}" cy="{dy}" r="2.5" fill="#8a8"/>')
        if m % 5 == 0:
            parts.append(
                f'<text x="{dx + 4}" y="{cy - 6}" fill="#6a6" font-size="10" font-family="monospace">{m}</text>'
            )
            parts.append(
                f'<text x="{cx + 6}" y="{dy + 3}" fill="#6a6" font-size="10" font-family="monospace">{-m}</text>'
            )

    # holdover aim point
    parts.append(f'<circle cx="{px}" cy="{py}" r="6" fill="#ff3030" stroke="#fff" stroke-width="1.5"/>')
    parts.append(f'<line x1="{px - 10}" y1="{py}" x2="{px + 10}" y2="{py}" stroke="#ff3030" stroke-width="1"/>')
    parts.append(f'<line x1="{px}" y1="{py - 10}" x2="{px}" y2="{py + 10}" stroke="#ff3030" stroke-width="1"/>')
    parts.append('</svg>')
    return ''.join(parts)


def _tmr_svg(x_mrad: float, y_mrad: float) -> str:
    """Simplified TMR-style with 0.5 mrad hashes."""
    cx = _SVG_SIZE / 2
    cy = _SVG_SIZE / 2
    px = _mrad_to_px(x_mrad) + cx
    py = _mrad_to_px(y_mrad) + cy
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SVG_SIZE}" height="{_SVG_SIZE}" '
        f'viewBox="0 0 {_SVG_SIZE} {_SVG_SIZE}" style="background:#0a0a0a;">',
        f'<circle cx="{cx}" cy="{cy}" r="{_SVG_SIZE/2 - 2}" fill="none" stroke="#1a1a1a" stroke-width="2"/>',
        f'<line x1="{cx - _SVG_SIZE/2 + 20}" y1="{cy}" x2="{cx + _SVG_SIZE/2 - 20}" y2="{cy}" stroke="#8a8" stroke-width="1"/>',
        f'<line x1="{cx}" y1="{cy - _SVG_SIZE/2 + 20}" x2="{cx}" y2="{cy + _SVG_SIZE/2 - 20}" stroke="#8a8" stroke-width="1"/>',
    ]
    for half in range(-18, 19):
        if half == 0:
            continue
        m = half * 0.5
        dx = _mrad_to_px(m) + cx
        dy = _mrad_to_px(m) + cy
        length = 8 if half % 2 == 0 else 4
        parts.append(f'<line x1="{dx}" y1="{cy - length}" x2="{dx}" y2="{cy + length}" stroke="#8a8" stroke-width="1"/>')
        parts.append(f'<line x1="{cx - length}" y1="{dy}" x2="{cx + length}" y2="{dy}" stroke="#8a8" stroke-width="1"/>')
        if half % 4 == 0:
            parts.append(f'<text x="{dx + 4}" y="{cy - 10}" fill="#6a6" font-size="9" font-family="monospace">{int(m)}</text>')

    parts.append(f'<circle cx="{px}" cy="{py}" r="6" fill="#ff3030" stroke="#fff" stroke-width="1.5"/>')
    parts.append(f'<line x1="{px - 10}" y1="{py}" x2="{px + 10}" y2="{py}" stroke="#ff3030" stroke-width="1"/>')
    parts.append(f'<line x1="{px}" y1="{py - 10}" x2="{px}" y2="{py + 10}" stroke="#ff3030" stroke-width="1"/>')
    parts.append('</svg>')
    return ''.join(parts)


_RETICLES = {
    "MIL-Dot": _mildot_svg,
    "TMR": _tmr_svg,
}


def render_reticle():
    st.markdown("### 🔭 Reticle Holdover")
    st.caption("Red dot marks aim-point at the current target range.")

    profile = st.session_state.profile
    target_range = float(st.session_state.get("target_range", 500))

    selected = st.selectbox(
        "Reticle",
        list(_RETICLES.keys()),
        index=0,
        key="reticle_selector",
    )

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

    # Hold UP means aim above target → dot appears below center (y positive downward in SVG)
    hold_x = pt.windage_mrad
    hold_y = -pt.drop_mrad  # drop_mrad negative = need to aim UP → dot goes BELOW center in view
    # In our view, positive y is downward. Aiming "up" means holdover dot is below the target dot,
    # so we mirror accordingly. Keep simple and consistent.

    svg = _RETICLES[selected](hold_x, hold_y)
    components.html(svg, height=_SVG_SIZE + 20)

    c1, c2, c3 = st.columns(3)
    c1.metric("Range", f"{int(target_range)} m")
    c2.metric("Elev Hold", f"{pt.drop_mrad:+.2f} MRAD")
    c3.metric("Wind Hold", f"{pt.windage_mrad:+.2f} MRAD")
