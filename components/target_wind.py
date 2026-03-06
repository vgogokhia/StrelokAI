"""
StrelokAI - Target & Wind Component
Renders target distance slider, wind speed/direction inputs, and phone compass widget.
Version: 1.0.0
"""
import streamlit as st
import streamlit.components.v1 as components

def render_target_section(col):
    with col:
        # Target Range Input
        st.markdown("### 🎯 Target")
        
        # Slider first
        target_range = st.slider(
            "Distance",
            min_value=50,
            max_value=2000,
            value=int(st.session_state.target_range),
            step=5,
            format="%d m"
        )
        st.session_state.target_range = target_range
        
        # Two buttons side by side
        c1, c2 = st.columns(2)
        if c1.button("◀ -5", key="dist_m5", use_container_width=True):
            st.session_state.target_range = max(50, st.session_state.target_range - 5)
            st.rerun()
        if c2.button("+5 ▶", key="dist_p5", use_container_width=True):
            st.session_state.target_range = min(2000, st.session_state.target_range + 5)
            st.rerun()

def render_wind_section(col):
    with col:
        # Wind Input
        st.markdown("### 💨 Wind")
        wind_speed = st.slider("Speed (m/s)", 0.0, 15.0, float(st.session_state.wind_speed), 0.5)
        st.session_state.wind_speed = wind_speed
        
        # Wind direction - degrees from North (meteorological)
        wind_dir_deg = st.slider("Wind Direction ° (Relative to North)", 0, 360, int(st.session_state.wind_dir_deg), 15)
        st.session_state.wind_dir_deg = wind_dir_deg
        
        # Phone compass - auto updates on click
        # Show current heading if set
        if st.session_state.compass_heading > 0:
            st.success(f"🧭 Heading: **{int(st.session_state.compass_heading)}°**")
        
        # Manual Shooting Direction Input
        shooting_dir = st.number_input(
            "Shooting Direction (°)",
            min_value=0, max_value=359,
            value=int(st.session_state.compass_heading),
            step=5,
            help="Direction you are aiming (0 = North, 90 = East). You can enter this manually or tap the compass block on a mobile device to auto-fill."
        )
        st.session_state.compass_heading = shooting_dir
        
        # declare_component is the ONLY way to get data back from JS to Python in Streamlit
        # components.html() is one-way (Python→JS only), it cannot return values
        from pathlib import Path
        _compass_dir = Path(__file__).parent / "compass"
        _compass_comp = components.declare_component("compass_widget", path=str(_compass_dir))
        
        _compass_val = _compass_comp(key="compass_input", default=None)
        if isinstance(_compass_val, dict) and "heading" in _compass_val:
            new_h = int(_compass_val["heading"])
            if new_h != st.session_state.compass_heading:
                st.session_state.compass_heading = new_h
                st.rerun()
        
        # Use session state heading for wind calculation
        compass_heading = st.session_state.compass_heading
        
        # Always calculate relative wind difference
        wind_deg = (wind_dir_deg - compass_heading) % 360
        
        # Show relative wind description (arrows point DOWNWIND, where the wind is going)
        if 337 <= wind_deg or wind_deg < 23:
            rel_desc = "↓ Headwind"      # Wind from front, blowing towards you
        elif 23 <= wind_deg < 67:
            rel_desc = "↙ 2 o'clock"      # Wind from 2 o'clock, blowing towards 8 o'clock
        elif 67 <= wind_deg < 113:
            rel_desc = "← From Right"     # Wind from right, blowing towards left
        elif 113 <= wind_deg < 157:
            rel_desc = "↖ 4 o'clock"      # Wind from 4 o'clock, blowing towards 10 o'clock
        elif 157 <= wind_deg < 203:
            rel_desc = "↑ Tailwind"       # Wind from behind, blowing forward
        elif 203 <= wind_deg < 247:
            rel_desc = "↗ 8 o'clock"      # Wind from 8 o'clock, blowing towards 2 o'clock
        elif 247 <= wind_deg < 293:
            rel_desc = "→ From Left"      # Wind from left, blowing towards right
        else:
            rel_desc = "↘ 10 o'clock"     # Wind from 10 o'clock, blowing towards 4 o'clock
        st.caption(f"**Relative: {rel_desc}**")
        
        return wind_deg  # Important to return the effective wind degree for calculations
