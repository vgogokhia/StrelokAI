"""
StrelokAI - Reticle Holdover Visualization
Renders a MIL-based reticle with a red aiming dot at the current
(windage, drop) solution, plus a few simple reticle options.
Version: 1.1.0 — responsive SVG + scope recognition moved in here.
"""
import os
import time
import streamlit as st
import streamlit.components.v1 as components

from ballistics.solver import calculate_solution
from ai.scope_recognition import identify_scope
from config import DEFAULT_LATITUDE, GEMINI_API_KEY as _CONFIG_GEMINI_KEY


# ---------------------------------------------------------------------------
# Scope recognition helpers (gated + rate limited)
# ---------------------------------------------------------------------------

# Per-process in-memory rate limit. Resets when the Streamlit container
# restarts, which is acceptable for abuse protection on a hobby app.
_SCOPE_UPLOAD_LOG: dict[str, list[float]] = {}
_SCOPE_LIMIT = 10
_SCOPE_WINDOW_SEC = 3600


def _resolve_gemini_key() -> str:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    return (os.getenv("GEMINI_API_KEY") or _CONFIG_GEMINI_KEY or "").strip()


def _check_rate_limit(username: str):
    now = time.time()
    hist = [t for t in _SCOPE_UPLOAD_LOG.get(username, []) if now - t < _SCOPE_WINDOW_SEC]
    _SCOPE_UPLOAD_LOG[username] = hist
    remaining = _SCOPE_LIMIT - len(hist)
    if remaining <= 0:
        oldest = min(hist)
        wait_min = max(1, int((_SCOPE_WINDOW_SEC - (now - oldest)) / 60) + 1)
        return False, 0, wait_min
    return True, remaining, 0


def _record_upload(username: str) -> None:
    _SCOPE_UPLOAD_LOG.setdefault(username, []).append(time.time())


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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
        f'viewBox="0 0 {_SVG_SIZE} {_SVG_SIZE}" preserveAspectRatio="xMidYMid meet" '
        f'style="background:#0a0a0a;display:block;">',
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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
        f'viewBox="0 0 {_SVG_SIZE} {_SVG_SIZE}" preserveAspectRatio="xMidYMid meet" '
        f'style="background:#0a0a0a;display:block;">',
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


def _render_scope_recognition():
    """Photo → Gemini → scope info. Gated on login + 10/hour rate limit."""
    with st.expander("📷 Identify scope from photo", expanded=False):
        if not st.session_state.get("logged_in"):
            st.info("Sign in to use scope photo recognition.")
            return

        username = st.session_state.get("username") or "anonymous"
        allowed, remaining, wait_min = _check_rate_limit(username)
        st.caption(
            f"Uploads remaining this hour: **{remaining}** / {_SCOPE_LIMIT}"
            if allowed else
            f"⏱ Rate limit reached. Try again in ~{wait_min} min."
        )
        if not allowed:
            return

        uploaded = st.file_uploader(
            "Scope photo",
            type=["jpg", "jpeg", "png", "webp"],
            key="scope_photo_uploader",
        )
        if not uploaded:
            return

        key = _resolve_gemini_key()
        if not key:
            st.error("Scope recognition is not configured on this server.")
            return

        # Consume one slot BEFORE the call so repeated failures still count.
        _record_upload(username)

        scope_info = None
        try:
            with st.spinner("Analyzing scope image..."):
                scope_info = identify_scope(
                    image_bytes=uploaded.getvalue(),
                    api_key=key,
                )
        except Exception as e:
            st.error(f"Scope recognition failed: {e}")
            return

        if scope_info is None or scope_info.manufacturer in ("Demo", "Unknown"):
            st.warning(
                "Couldn't read a brand/model off this image. "
                "Try a closer shot of the turret or zoom ring."
            )
            return

        st.success(f"Identified: **{scope_info.manufacturer} {scope_info.model}**")
        st.write(f"- Click Value: {scope_info.click_value_mrad} MRAD")
        st.write(f"- Max Elevation: {scope_info.max_elevation_mrad} MRAD")
        st.write(f"- Reticles: {', '.join(scope_info.reticle_options)}")
        st.caption(f"Confidence: {scope_info.confidence*100:.0f}%")


def render_reticle():
    st.markdown("### 🔭 Reticle Holdover")
    st.caption("Red dot marks aim-point at the current target range.")

    _render_scope_recognition()

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
    # Responsive wrapper: square that fills available width up to _SVG_SIZE,
    # so it never gets clipped on narrow mobile viewports.
    wrapper = (
        f'<div style="width:100%;max-width:{_SVG_SIZE}px;aspect-ratio:1/1;'
        f'margin:0 auto;">{svg}</div>'
    )
    components.html(wrapper, height=_SVG_SIZE + 20)

    c1, c2, c3 = st.columns(3)
    c1.metric("Range", f"{int(target_range)} m")
    c2.metric("Elev Hold", f"{pt.drop_mrad:+.2f} MRAD")
    c3.metric("Wind Hold", f"{pt.windage_mrad:+.2f} MRAD")
