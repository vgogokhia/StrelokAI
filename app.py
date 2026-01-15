"""
StrelokAI - AI-Powered Ballistic Calculator
Main Streamlit Application
"""
import streamlit as st
import math
from typing import Optional

# Import our modules
from ballistics import BallisticSolver
from ballistics.solver import (
    Projectile, Rifle, Wind, ShootingConditions, 
    calculate_solution, BallisticSolution
)
from ballistics.atmosphere import Atmosphere, AtmosphericConditions
from ai.weather_api import get_weather
from ai.scope_recognition import identify_scope, list_supported_scopes, SCOPE_DATABASE
from config import (
    APP_NAME, VERSION, DEFAULT_LATITUDE, DEFAULT_LONGITUDE,
    STANDARD_ATMOSPHERE
)

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME} - Ballistic Calculator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and styling
def apply_theme(theme: str = "dark"):
    if theme == "dark":
        st.markdown("""
        <style>
        .stApp {
            background-color: #121212;
            color: #E0E0E0;
        }
        .main-solution {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 20px 0;
            border: 1px solid #0f3460;
        }
        .elevation-display {
            font-size: 72px;
            font-weight: 700;
            color: #4CAF50;
            text-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
        }
        .windage-display {
            font-size: 36px;
            font-weight: 600;
            color: #42A5F5;
        }
        .metric-card {
            background: #1E1E1E;
            border-radius: 12px;
            padding: 15px;
            margin: 5px;
            border-left: 4px solid #4CAF50;
        }
        .section-header {
            color: #BB86FC;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
    elif theme == "red":
        st.markdown("""
        <style>
        .stApp {
            background-color: #000000;
            color: #660000;
        }
        .main-solution {
            background: #0a0000;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 20px 0;
            border: 1px solid #330000;
        }
        .elevation-display {
            font-size: 72px;
            font-weight: 700;
            color: #990000;
        }
        .windage-display {
            font-size: 36px;
            font-weight: 600;
            color: #660000;
        }
        </style>
        """, unsafe_allow_html=True)

# Initialize session state
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "Default Profile",
        "muzzle_velocity": 850.0,
        "bc_g7": 0.243,
        "mass_grains": 175.0,
        "diameter": 0.308,
        "zero_range": 100.0,
        "sight_height": 40.0,
        "twist_rate": 10.0,
    }

if "weather" not in st.session_state:
    st.session_state.weather = None

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "target_range" not in st.session_state:
    st.session_state.target_range = 500

if "temp_c" not in st.session_state:
    st.session_state.temp_c = 15.0
if "pressure" not in st.session_state:
    st.session_state.pressure = 1013.0
if "humidity" not in st.session_state:
    st.session_state.humidity = 50.0
if "wind_speed" not in st.session_state:
    st.session_state.wind_speed = 3.0
if "wind_dir_deg" not in st.session_state:
    st.session_state.wind_dir_deg = 270.0  # From left (West)
if "compass_heading" not in st.session_state:
    st.session_state.compass_heading = 0.0
if "use_compass" not in st.session_state:
    st.session_state.use_compass = False

# Apply theme
apply_theme(st.session_state.theme)

# Header - compact for mobile
st.markdown(f"**🎯 {APP_NAME}** | Ballistic Calculator")


# Sidebar - Settings
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Theme selector - use index to set correct initial state
    theme_index = 1 if st.session_state.theme == "red" else 0
    theme = st.radio("Theme", ["Dark", "Red (NVG)"], index=theme_index, horizontal=True,
                     key="theme_radio", on_change=lambda: setattr(st.session_state, 'theme', 'red' if 'Red' in st.session_state.theme_radio else 'dark'))
    
    # Apply theme immediately
    if "Red" in theme:
        st.session_state.theme = "red"
    else:
        st.session_state.theme = "dark"
    
    st.divider()
    
    # Profile section
    st.markdown("### 📋 Active Profile")
    profile_name = st.text_input("Profile Name", st.session_state.profile["name"])
    
    st.markdown("#### Rifle")
    muzzle_velocity = st.number_input(
        "Muzzle Velocity (m/s)", 
        min_value=200.0, max_value=1500.0,
        value=st.session_state.profile["muzzle_velocity"],
        step=1.0
    )
    zero_range = st.number_input(
        "Zero Range (m)",
        min_value=25.0, max_value=500.0,
        value=st.session_state.profile["zero_range"],
        step=25.0
    )
    sight_height = st.number_input(
        "Sight Height (mm)",
        min_value=20.0, max_value=80.0,
        value=st.session_state.profile["sight_height"],
        step=1.0
    )
    twist_rate = st.number_input(
        "Twist Rate (1:X inches)",
        min_value=6.0, max_value=20.0,
        value=st.session_state.profile["twist_rate"],
        step=0.5
    )
    
    st.markdown("#### Bullet")
    bc_g7 = st.number_input(
        "Ballistic Coefficient (G7)",
        min_value=0.100, max_value=0.500,
        value=st.session_state.profile["bc_g7"],
        step=0.001,
        format="%.3f"
    )
    mass_grains = st.number_input(
        "Bullet Weight (grains)",
        min_value=50.0, max_value=400.0,
        value=st.session_state.profile["mass_grains"],
        step=1.0
    )
    diameter = st.number_input(
        "Bullet Diameter (inches)",
        min_value=0.172, max_value=0.510,
        value=st.session_state.profile["diameter"],
        step=0.001,
        format="%.3f"
    )
    
    # Update profile
    st.session_state.profile.update({
        "name": profile_name,
        "muzzle_velocity": muzzle_velocity,
        "bc_g7": bc_g7,
        "mass_grains": mass_grains,
        "diameter": diameter,
        "zero_range": zero_range,
        "sight_height": sight_height,
        "twist_rate": twist_rate,
    })

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
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

with col2:
    # Wind Input
    st.markdown("### 💨 Wind")
    wind_speed = st.slider("Speed (m/s)", 0.0, 15.0, float(st.session_state.wind_speed), 0.5)
    st.session_state.wind_speed = wind_speed
    
    # Wind direction - degrees from North (meteorological)
    wind_dir_deg = st.slider("Direction (°)", 0, 360, int(st.session_state.wind_dir_deg), 15)
    st.session_state.wind_dir_deg = wind_dir_deg
    
    # Phone compass button (works on HTTPS with device sensor)
    import streamlit.components.v1 as components
    components.html("""
    <div style="font-family: sans-serif;">
        <button onclick="getCompass()" style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #4CAF50; 
            border: 1px solid #4CAF50; 
            padding: 12px; 
            border-radius: 8px; 
            cursor: pointer;
            width: 100%;
            font-size: 16px;
            margin-bottom: 8px;
        ">🧭 Get Phone Compass</button>
        <div id="result" style="padding: 10px; background: #1a1a2e; border-radius: 8px; text-align: center;">
            <span id="deg" style="font-size: 24px; color: #4CAF50; font-weight: bold;">--°</span>
            <span id="dir" style="color: #aaa; margin-left: 8px;">Tap button</span>
        </div>
    </div>
    <script>
    function getDir(d) {
        if (d >= 337.5 || d < 22.5) return 'North';
        if (d < 67.5) return 'NE';
        if (d < 112.5) return 'East';
        if (d < 157.5) return 'SE';
        if (d < 202.5) return 'South';
        if (d < 247.5) return 'SW';
        if (d < 292.5) return 'West';
        return 'NW';
    }
    function update(h) {
        h = Math.round(h);
        document.getElementById('deg').innerHTML = h + '°';
        document.getElementById('dir').innerHTML = getDir(h);
    }
    function getCompass() {
        document.getElementById('dir').innerHTML = 'Reading...';
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            DeviceOrientationEvent.requestPermission().then(r => {
                if (r === 'granted') window.addEventListener('deviceorientation', e => { if(e.alpha) update(e.alpha); });
                else document.getElementById('dir').innerHTML = 'Denied';
            }).catch(() => document.getElementById('dir').innerHTML = 'Error');
        } else if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', e => { if(e.alpha) update(e.alpha); });
        } else {
            document.getElementById('dir').innerHTML = 'Not available';
        }
    }
    </script>
    """, height=100)
    
    # Quick heading buttons (backup)
    st.caption("Or tap direction:")
    dir_cols = st.columns(4)
    directions = [("N", 0), ("E", 90), ("S", 180), ("W", 270)]
    for i, (name, deg) in enumerate(directions):
        if dir_cols[i].button(name, key=f"dir_{name}", use_container_width=True):
            st.session_state.compass_heading = deg
            st.rerun()
    
    # Manual heading input
    compass_heading = st.number_input("Manual (°)", 0, 360, int(st.session_state.compass_heading), 15)
    
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

# Atmospheric Conditions - Collapsible
with st.expander("🌡️ Atmosphere & Weather Sync", expanded=False):
    # Weather sync button - now syncs wind too!
    weather_clicked = st.button("🌍 Sync All Weather Data", type="primary")
    if weather_clicked:
        weather = get_weather(DEFAULT_LATITUDE, DEFAULT_LONGITUDE)
        if weather:
            st.session_state.temp_c = float(weather.temperature_c)
            st.session_state.pressure = float(weather.pressure_mbar)
            st.session_state.humidity = float(weather.humidity_pct)
            st.session_state.wind_speed = float(weather.wind_speed_mps)
            st.session_state.wind_dir_deg = float(weather.wind_direction_deg)
            st.session_state.weather_status = f"✅ {weather.temperature_c:.1f}°C | Wind: {weather.wind_speed_mps:.1f}m/s from {weather.wind_direction_deg:.0f}°"
            st.rerun()
    
    if "weather_status" in st.session_state:
        st.success(st.session_state.weather_status)
    
    atm_cols = st.columns(2)
    with atm_cols[0]:
        temp_c = st.number_input("Temp (°C)", -30.0, 50.0, float(st.session_state.temp_c), 1.0)
        st.session_state.temp_c = temp_c
        pressure = st.number_input("Pressure (mbar)", 800.0, 1100.0, float(st.session_state.pressure), 1.0)
        st.session_state.pressure = pressure
    with atm_cols[1]:
        humidity = st.number_input("Humidity (%)", 0.0, 100.0, float(st.session_state.humidity), 5.0)
        st.session_state.humidity = humidity
        altitude = st.number_input("Altitude (m)", 0.0, 5000.0, 0.0, 100.0)

# Calculate Solution
st.divider()

try:
    solution = calculate_solution(
        muzzle_velocity_mps=muzzle_velocity,
        bc_g7=bc_g7,
        mass_grains=mass_grains,
        diameter_inches=diameter,
        zero_range_m=zero_range,
        target_range_m=target_range,
        temperature_c=temp_c,
        pressure_mbar=pressure,
        humidity_pct=humidity,
        altitude_m=altitude,
        wind_speed_mps=wind_speed,
        wind_direction_deg=wind_deg,
        latitude_deg=DEFAULT_LATITUDE,
        azimuth_deg=0
    )
    
    # Get point at target
    target_point = solution.at_range(target_range)
    
    if target_point:
        # Calculate clicks (0.1 MRAD per click)
        click_value = 0.1
        elevation_clicks = int(abs(target_point.drop_mrad) / click_value)
        windage_clicks = int(abs(target_point.windage_mrad) / click_value)
        elev_dir = 'UP' if target_point.drop_mrad < 0 else 'DOWN'
        wind_dir = 'L' if target_point.windage_mrad < 0 else 'R'
        
        # Main Solution Display - CLICKS
        st.markdown(f"""
        <div class="main-solution">
            <div class="elevation-display">{elevation_clicks} CLICKS</div>
            <div style="font-size: 24px; color: #888;">ELEVATION {elev_dir}</div>
            <div style="font-size: 14px; color: #666;">({abs(target_point.drop_mrad):.2f} MRAD)</div>
            <div style="margin-top: 20px;"></div>
            <div class="windage-display">{windage_clicks} {wind_dir}</div>
            <div style="font-size: 18px; color: #666;">WINDAGE</div>
            <div style="font-size: 14px; color: #555;">({abs(target_point.windage_mrad):.2f} MRAD)</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact metrics in expander
        with st.expander("📊 Details", expanded=False):
            data_cols = st.columns(4)
            with data_cols[0]:
                st.metric("ToF", f"{target_point.time_s:.2f}s")
            with data_cols[1]:
                st.metric("Velocity", f"{target_point.velocity_mps:.0f} m/s")
            with data_cols[2]:
                st.metric("Energy", f"{target_point.energy_j:.0f} J")
            with data_cols[3]:
                st.metric("Mach", f"{target_point.mach:.2f}")
        
        # Trajectory Table
        with st.expander("📊 Full Trajectory Table"):
            st.markdown("| Range | Drop | Drop | Windage | Velocity | ToF |")
            st.markdown("|:---:|:---:|:---:|:---:|:---:|:---:|")
            st.markdown("| (m) | (m) | (MRAD) | (MRAD) | (m/s) | (s) |")
            
            for pt in solution.trajectory:
                if pt.range_m % 100 == 0 or pt.range_m == target_range:
                    st.markdown(
                        f"| {pt.range_m:.0f} | {pt.drop_m:.3f} | {pt.drop_mrad:.2f} | "
                        f"{pt.windage_mrad:.2f} | {pt.velocity_mps:.0f} | {pt.time_s:.3f} |"
                    )

except Exception as e:
    st.error(f"Calculation error: {e}")
    st.exception(e)

# AI Features Section
st.divider()
st.markdown("### 🤖 AI Features")

ai_cols = st.columns(2)

with ai_cols[0]:
    st.markdown("#### 📷 Scope Recognition")
    uploaded_file = st.file_uploader("Upload scope photo", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        scope_info = identify_scope(image_bytes=uploaded_file.getvalue())
        if scope_info:
            st.success(f"Identified: **{scope_info.manufacturer} {scope_info.model}**")
            st.write(f"- Click Value: {scope_info.click_value_mrad} MRAD")
            st.write(f"- Max Elevation: {scope_info.max_elevation_mrad} MRAD")
            st.write(f"- Reticles: {', '.join(scope_info.reticle_options)}")

with ai_cols[1]:
    st.markdown("#### 🔭 Supported Scopes")
    scopes = list_supported_scopes()
    for scope in scopes[:5]:
        st.write(f"✓ {scope}")
    if len(scopes) > 5:
        st.caption(f"...and {len(scopes) - 5} more")

# Footer
st.divider()
st.caption(f"{APP_NAME} v{VERSION} | Made with ❤️ for precision shooters")
