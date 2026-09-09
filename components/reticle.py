"""
ballistics.ge - Reticle Holdover Visualization
Renders a MIL-based reticle with a red aiming dot at the current
(windage, drop) solution, plus a few simple reticle options.
Version: 1.2.0 — shared solver (same wind/heading as Calculator), unit-aware
"""
import os
import time
import streamlit as st

from core.solve import solve_current
from core.units import fmt_range, fmt_angular
from ai.scope_recognition import identify_scope
from config import GEMINI_API_KEY as _CONFIG_GEMINI_KEY
from core.secrets import secret_value


# ---------------------------------------------------------------------------
# Scope recognition helpers (gated + rate limited)
# ---------------------------------------------------------------------------

# Per-process in-memory rate limit. Resets when the Streamlit container
# restarts, which is acceptable for abuse protection on a hobby app.
_SCOPE_UPLOAD_LOG: dict[str, list[float]] = {}
_SCOPE_LIMIT = 10
_SCOPE_WINDOW_SEC = 3600


def _resolve_gemini_key() -> str:
    return str(secret_value("GEMINI_API_KEY", _CONFIG_GEMINI_KEY) or "").strip()


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
    from components.reticle_lib import RETICLES, BY_NAME, render_svg, hold_in_reticle_units
    st.markdown("### 🔭 Reticle Holdover")
    st.caption("Red dot = the reticle mark to hold on the target at the current range (holdover / wind hold).")

    _render_scope_recognition()

    names = [r.name for r in RETICLES]
    st.session_state.setdefault("reticle_selector", st.session_state.get("reticle_name", names[0]))
    if st.session_state.reticle_selector not in BY_NAME:
        st.session_state.reticle_selector = names[0]
    c1, c2 = st.columns([3, 2])
    with c1:
        selected = st.selectbox("Reticle", names, key="reticle_selector")
    spec = BY_NAME[selected]
    st.session_state.reticle_name = selected
    with c2:
        fp = st.radio("Focal plane", ["FFP", "SFP"], horizontal=True,
                      index=1 if st.session_state.get("reticle_fp") == "SFP" else 0, key="reticle_fp_radio",
                      help="FFP: marks are true at every zoom. SFP: marks are true only at one magnification.")
    st.session_state.reticle_fp = fp
    sfp_scale = 1.0
    if fp == "SFP":
        m1, m2 = st.columns(2)
        cal = m1.number_input("Reticle true at (×)", 1.0, 50.0, float(st.session_state.get("reticle_cal_mag", 10.0)), 0.5, key="reticle_cal_mag_in",
                              help="Usually max magnification (check the manual).")
        cur = m2.number_input("Current magnification (×)", 1.0, 50.0, float(st.session_state.get("reticle_cur_mag", cal)), 0.5, key="reticle_cur_mag_in")
        st.session_state.reticle_cal_mag, st.session_state.reticle_cur_mag = cal, cur
        sfp_scale = cur / cal if cal else 1.0
    if spec.note:
        st.caption(spec.note + ("" if spec.unit == "MRAD" else "  (MOA reticle)"))

    try:
        inputs, solution = solve_current()
    except Exception as exc:
        st.error(f"Solver error: {exc}")
        return
    target_range = inputs.target_range
    pt = solution.at_range(target_range)
    if pt is None:
        st.warning("No trajectory point at that range.")
        return

    # The red dot is the reticle mark you place ON the target: the bullet
    # impacts low/left, so the mark to use is the same distance below/left.
    hold_x = hold_in_reticle_units(pt.windage_mrad, spec, sfp_scale)
    hold_y = hold_in_reticle_units(-pt.drop_mrad, spec, sfp_scale)

    # Optional: draw the target size at range around the hold point
    tgt = st.session_state.get("reticle_target_cm", 0.0)
    ring = None
    if tgt and target_range:
        ring_mrad = (tgt / 100.0) / target_range * 1000.0
        ring = hold_in_reticle_units(ring_mrad, spec, sfp_scale)

    svg = render_svg(spec, hold_x, hold_y, show_target_ring=ring)
    _, mid, _ = st.columns([1, 6, 1])
    with mid:
        st.image(svg, width="stretch")

    c1, c2, c3 = st.columns(3)
    c1.metric("Range", fmt_range(target_range))
    c2.metric("Elev hold", f"{hold_y:+.2f} {spec.unit}" + (" (reticle)" if sfp_scale != 1.0 else ""))
    c3.metric("Wind hold", f"{hold_x:+.2f} {spec.unit}" + (" (reticle)" if sfp_scale != 1.0 else ""))
    if sfp_scale != 1.0:
        st.caption(f"SFP at {st.session_state.reticle_cur_mag:g}× of {st.session_state.reticle_cal_mag:g}×: "
                   f"each mark subtends {1/sfp_scale:.2f} {spec.unit}; true hold is "
                   f"{fmt_angular(-pt.drop_mrad)} up / {fmt_angular(pt.windage_mrad, signed=True)}.")
    if abs(hold_y) > spec.view or abs(hold_x) > spec.view:
        st.warning("Hold is outside the reticle — dial some elevation on the turret and hold the rest.")
    st.number_input("Show target size on reticle (cm, 0 = off)", 0.0, 500.0,
                    float(st.session_state.get("reticle_target_cm", 0.0)), 5.0, key="reticle_target_cm_in",
                    on_change=lambda: st.session_state.__setitem__("reticle_target_cm", st.session_state.reticle_target_cm_in))
