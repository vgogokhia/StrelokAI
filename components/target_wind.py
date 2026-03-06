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
        wind_dir_deg = st.slider("Wind Direction (°)", 0, 360, int(st.session_state.wind_dir_deg), 15)
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
        
        # Compass widget - reads phone magnetometer, tap to apply heading
        # On tap, appends ?heading=X to current URL so url_handler.py picks it up
        components.html("""
        <div id="compass" onclick="apply()" style="font-family: sans-serif; text-align: center; cursor: pointer; background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%); padding: 15px; border-radius: 10px; border: 2px solid #4CAF50;">
            <div style="font-size: 14px; color: #888;">🧭 COMPASS (tap to apply)</div>
            <div id="deg" style="font-size: 42px; color: #4CAF50; font-weight: bold; margin: 5px 0;">---</div>
            <div id="dir" style="font-size: 18px; color: #aaa;">Initializing...</div>
        </div>
        <script>
        let currentHeading = null;
        let eventFired = false;
        function getDir(d) {
            if (d >= 337.5 || d < 22.5) return 'N';
            if (d < 67.5) return 'NE';
            if (d < 112.5) return 'E';
            if (d < 157.5) return 'SE';
            if (d < 202.5) return 'S';
            if (d < 247.5) return 'SW';
            if (d < 292.5) return 'W';
            return 'NW';
        }
        function updateDisplay(h) {
            eventFired = true;
            h = Math.round(h);
            if (h < 0) h += 360;
            if (h >= 360) h -= 360;
            currentHeading = h;
            document.getElementById('deg').textContent = h + '°';
            document.getElementById('dir').textContent = getDir(h);
        }
        function handleOrientation(e) {
            let heading;
            if (e.webkitCompassHeading !== undefined) heading = e.webkitCompassHeading;
            else if (e.alpha !== null) heading = 360 - e.alpha;
            if (heading !== undefined) updateDisplay(heading);
        }
        function apply() {
            if (currentHeading !== null) {
                // Navigate the TOP window (escaping iframe) to current app URL with heading param
                var baseUrl = window.top.location.origin + window.top.location.pathname;
                window.top.location.href = baseUrl + '?heading=' + currentHeading;
            }
        }
        function startCompass() {
            if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
                DeviceOrientationEvent.requestPermission().then(function(r) {
                    if (r === 'granted') {
                        window.addEventListener('deviceorientationabsolute', handleOrientation);
                        window.addEventListener('deviceorientation', handleOrientation);
                    } else { document.getElementById('dir').textContent = 'Permission denied'; }
                }).catch(function() { document.getElementById('dir').textContent = 'Tap to enable'; });
            } else if (window.DeviceOrientationEvent) {
                window.addEventListener('deviceorientationabsolute', handleOrientation);
                window.addEventListener('deviceorientation', handleOrientation);
            } else {
                document.getElementById('dir').textContent = 'Not available';
            }
            setTimeout(function() {
                if (!eventFired) {
                    document.getElementById('deg').textContent = 'N/A';
                    document.getElementById('dir').textContent = 'Use manual input above';
                }
            }, 1500);
        }
        setTimeout(startCompass, 300);
        </script>
        """, height=130)
        
        # Use session state heading for wind calculation
        compass_heading = st.session_state.compass_heading
        
        # Calculate relative wind if heading is set
        if compass_heading > 0:
            wind_deg = (wind_dir_deg - compass_heading) % 360
            # Show relative wind description
            if 337 <= wind_deg or wind_deg < 23:
                rel_desc = "↑ Headwind"
            elif 23 <= wind_deg < 67:
                rel_desc = "↗ 2 o'clock"
            elif 67 <= wind_deg < 113:
                rel_desc = "→ From Right"
            elif 113 <= wind_deg < 157:
                rel_desc = "↘ 4 o'clock"
            elif 157 <= wind_deg < 203:
                rel_desc = "↓ Tailwind"
            elif 203 <= wind_deg < 247:
                rel_desc = "↙ 8 o'clock"
            elif 247 <= wind_deg < 293:
                rel_desc = "← From Left"
            else:
                rel_desc = "↖ 10 o'clock"
            st.caption(f"**Relative: {rel_desc}**")
        else:
            wind_deg = wind_dir_deg
            # Show absolute wind description
            if 337 <= wind_deg or wind_deg < 23:
                wind_desc = "From North"
            elif 23 <= wind_deg < 67:
                wind_desc = "From NE"
            elif 67 <= wind_deg < 113:
                wind_desc = "From East"
            elif 113 <= wind_deg < 157:
                wind_desc = "From SE"
            elif 157 <= wind_deg < 203:
                wind_desc = "From South"
            elif 203 <= wind_deg < 247:
                wind_desc = "From SW"
            elif 247 <= wind_deg < 293:
                wind_desc = "From West"
            else:
                wind_desc = "From NW"
            st.caption(f"🌬️ {wind_desc}")
        
        return wind_deg  # Important to return the effective wind degree for calculations
