"""
StrelokAI - Target & Wind Component
Renders target distance slider, wind speed/direction inputs, and phone compass widget.
Version: 2.1.0 - full imperial support
"""
import streamlit as st
import streamlit.components.v1 as components

from core.units import (
    is_imperial, range_label, speed_label,
    input_range_from_m, input_range_to_m,
    input_speed_from_mps, input_speed_to_mps,
)

# Quick-range presets — round numbers in both systems.
_QUICK_RANGES_M = [100, 300, 500, 800, 1000]
_QUICK_RANGES_YD = [100, 300, 500, 800, 1000]


# ---------------------------------------------------------------------------
# Range sync (always stores metres in session_state.target_range)
# ---------------------------------------------------------------------------

def _display_to_m(display_val: int) -> int:
    """Convert a display-unit value to metres."""
    return int(round(input_range_to_m(display_val)))


def _m_to_display(meters: int) -> int:
    """Convert metres to the current display unit (rounded)."""
    return int(round(input_range_from_m(meters)))


def _sync_range_from_display(display_val: int):
    """Called when the user changes the number/slider/chip in display units."""
    m = _display_to_m(display_val)
    st.session_state.target_range = m
    disp = _m_to_display(m)
    st.session_state.target_range_num = disp
    st.session_state.target_range_slider = disp


def _sync_quick(meters: int):
    """Quick chip callback — value is in metres."""
    st.session_state.target_range = meters
    disp = _m_to_display(meters)
    st.session_state.target_range_num = disp
    st.session_state.target_range_slider = disp


def _on_num_change():
    _sync_range_from_display(st.session_state.target_range_num)


def _on_slider_change():
    _sync_range_from_display(st.session_state.target_range_slider)


# ---------------------------------------------------------------------------
# Target section
# ---------------------------------------------------------------------------

def render_target_section(col):
    with col:
      with st.expander("🎯 Target", expanded=True):
        imp = is_imperial()
        unit = range_label()  # "yd" or "m"
        disp = _m_to_display(int(st.session_state.target_range))
        max_disp = _m_to_display(2000)
        min_disp = _m_to_display(50)
        step_disp = 5 if not imp else 5

        # Seed widget keys
        if st.session_state.get("target_range_num") != disp:
            st.session_state.target_range_num = disp
        if st.session_state.get("target_range_slider") != disp:
            st.session_state.target_range_slider = disp

        # Row 1: number + slider
        num_col, slider_col = st.columns([1, 3], gap="small")
        with num_col:
            st.number_input(
                f"Distance ({unit})",
                min_value=min_disp, max_value=max_disp,
                step=step_disp,
                key="target_range_num",
                on_change=_on_num_change,
                label_visibility="collapsed",
            )
        with slider_col:
            st.slider(
                f"Distance ({unit})",
                min_value=min_disp, max_value=max_disp,
                step=step_disp,
                key="target_range_slider",
                on_change=_on_slider_change,
                label_visibility="collapsed",
            )

        # Unit label + current value
        st.caption(f"Distance: **{disp} {unit}**")

        # Row 2: quick chips + angle/cant popover
        # Use round numbers in both systems; for imperial, chip values are
        # in yards and get converted to metres on click.
        if imp:
            chip_values_display = _QUICK_RANGES_YD
            chip_values_m = [int(round(y * 0.9144)) for y in _QUICK_RANGES_YD]
        else:
            chip_values_display = _QUICK_RANGES_M
            chip_values_m = _QUICK_RANGES_M

        current_disp = disp
        chip_cols = st.columns(len(chip_values_display) + 1, gap="small")
        for i, (r_m, label) in enumerate(zip(chip_values_m, chip_values_display)):
            active = (current_disp == label)
            if chip_cols[i].button(
                f"{label}",
                key=f"qr_{label}_{unit}",
                use_container_width=True,
                type="primary" if active else "secondary",
                on_click=_sync_quick,
                args=(r_m,),
            ):
                pass
        with chip_cols[-1]:
            try:
                with st.popover("⚙", use_container_width=True):
                    _render_angle_cant_inputs()
            except Exception:
                with st.expander("⚙ Angle/Cant", expanded=False):
                    _render_angle_cant_inputs()


def _render_angle_cant_inputs():
    shot_angle = st.number_input(
        "Shot Angle (°)",
        min_value=-60.0, max_value=60.0,
        value=float(st.session_state.get("shot_angle_deg", 0.0)),
        step=1.0,
        help="Positive = uphill, negative = downhill. Reduces effective drop.",
    )
    st.session_state.shot_angle_deg = shot_angle
    cant_angle = st.number_input(
        "Cant Angle (°)",
        min_value=-45.0, max_value=45.0,
        value=float(st.session_state.get("cant_angle_deg", 0.0)),
        step=1.0,
        help="Rifle roll angle. Positive = rifle tilted right.",
    )
    st.session_state.cant_angle_deg = cant_angle


# ---------------------------------------------------------------------------
# Wind section
# ---------------------------------------------------------------------------

def render_wind_section(col):
    with col:
      with st.expander("💨 Wind", expanded=False):
        imp = is_imperial()
        s_label = speed_label()  # "mph" or "m/s"

        # Wind speed — display in user's units, store in m/s
        stored_mps = float(st.session_state.wind_speed)
        disp_speed = input_speed_from_mps(stored_mps)
        max_speed = 35.0 if imp else 15.0  # ~35 mph ≈ 15 m/s

        wind_speed_disp = st.slider(
            f"Speed ({s_label})", 0.0, max_speed,
            float(round(disp_speed, 1)), 0.5,
        )
        st.session_state.wind_speed = input_speed_to_mps(wind_speed_disp)

        # Wind direction
        wind_dir_deg = st.slider(
            "Wind Direction ° (from North)", 0, 360,
            int(st.session_state.wind_dir_deg), 15,
        )
        st.session_state.wind_dir_deg = wind_dir_deg

        # Compass heading
        if st.session_state.compass_heading > 0:
            st.success(f"🧭 Heading: **{int(st.session_state.compass_heading)}°**")

        shooting_dir = st.number_input(
            "Shooting Direction (°)",
            min_value=0, max_value=359,
            value=int(st.session_state.compass_heading),
            step=5,
            help="Direction you are aiming (0=N, 90=E). Enter manually or tap compass.",
        )
        st.session_state.compass_heading = shooting_dir

        # Phone compass widget
        from pathlib import Path
        _compass_dir = Path(__file__).parent / "compass"
        _compass_comp = components.declare_component("compass_widget", path=str(_compass_dir))
        _compass_val = _compass_comp(key="compass_input", default=None)
        if isinstance(_compass_val, dict) and "heading" in _compass_val:
            new_h = int(_compass_val["heading"])
            if new_h != st.session_state.compass_heading:
                st.session_state.compass_heading = new_h
                st.rerun()

        compass_heading = st.session_state.compass_heading
        wind_deg = (wind_dir_deg - compass_heading) % 360

        if 337 <= wind_deg or wind_deg < 23:
            rel_desc = "↓ Headwind"
        elif 23 <= wind_deg < 67:
            rel_desc = "↙ 2 o'clock"
        elif 67 <= wind_deg < 113:
            rel_desc = "← From Right"
        elif 113 <= wind_deg < 157:
            rel_desc = "↖ 4 o'clock"
        elif 157 <= wind_deg < 203:
            rel_desc = "↑ Tailwind"
        elif 203 <= wind_deg < 247:
            rel_desc = "↗ 8 o'clock"
        elif 247 <= wind_deg < 293:
            rel_desc = "→ From Left"
        else:
            rel_desc = "↘ 10 o'clock"
        st.caption(f"**Relative: {rel_desc}**")

        return wind_deg
