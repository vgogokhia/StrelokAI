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
from auth import create_user, authenticate_user, user_exists
from profiles import (
    RifleProfile, CartridgeProfile, FullProfile,
    save_full_profile, load_full_profile, list_full_profiles
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

# Auth session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "auth_message" not in st.session_state:
    st.session_state.auth_message = None

# Check for compass heading from URL query param
query_params = st.query_params
if "heading" in query_params:
    try:
        new_heading = int(query_params["heading"])
        st.session_state.compass_heading = new_heading
        st.query_params.clear()  # Clear the param after reading
    except:
        pass

# Apply theme
apply_theme(st.session_state.theme)

# Header - compact for mobile
st.markdown(f"**🎯 {APP_NAME}** | Ballistic Calculator |")


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
    
    # ============ Authentication Section ============
    if not st.session_state.logged_in:
        st.markdown("### 🔐 Login / Sign Up")
        
        auth_method = st.radio("", ["Email", "Google"], horizontal=True, label_visibility="collapsed")
        
        if auth_method == "Email":
            auth_tab = st.radio("", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed", key="auth_tab_radio")
            
            st.text_input("Username", key="auth_username_input")
            st.text_input("Password", type="password", key="auth_password_input")
            
            # Read from session state (fix for button click timing)
            username_val = st.session_state.get("auth_username_input", "")
            password_val = st.session_state.get("auth_password_input", "")
            
            if auth_tab == "Login":
                if st.button("Login", type="primary", use_container_width=True):
                    if username_val and password_val:
                        success, message = authenticate_user(username_val, password_val)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username_val
                            st.session_state.auth_message = f"Welcome, {username_val}!"
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter username and password")
            else:
                if st.button("Create Account", type="primary", use_container_width=True):
                    if username_val and password_val:
                        success, message = create_user(username_val, password_val)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username_val
                            st.session_state.auth_message = f"Account created! Welcome, {username_val}!"
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter username and password")
        
        else:
            # Google OAuth
            st.markdown("##### Sign in with Google")
            try:
                from streamlit_google_auth import Authenticate
                import json
                import tempfile
                import os
                
                # Get credentials from secrets
                google_config = st.secrets.get("google", {})
                client_id = google_config.get("client_id", "")
                client_secret = google_config.get("client_secret", "")
                redirect_uri = google_config.get("redirect_uri", "https://strelokai.streamlit.app")
                
                if client_id and client_secret:
                    # Create temporary credentials file (required by library)
                    creds = {
                        "web": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "redirect_uris": [redirect_uri],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token"
                        }
                    }
                    
                    # Write to temp file
                    creds_path = "/tmp/google_creds.json"
                    with open(creds_path, "w") as f:
                        json.dump(creds, f)
                    
                    authenticator = Authenticate(
                        secret_credentials_path=creds_path,
                        cookie_name="strelokai_auth",
                        cookie_key="strelokai_secret_cookie_key_12345",
                        redirect_uri=redirect_uri,
                    )
                    
                    authenticator.check_authentification()
                    authenticator.login()
                    
                    if st.session_state.get("connected"):
                        st.session_state.logged_in = True
                        st.session_state.username = st.session_state.get("user_info", {}).get("email", "Google User")
                        st.session_state.auth_message = f"Welcome, {st.session_state.username}!"
                        st.rerun()
                else:
                    st.info("Google auth not configured.")
                    st.caption("Add credentials to Streamlit secrets, or use Email login")
            except ImportError:
                st.warning("Google auth requires: `pip install streamlit-google-auth`")
                st.caption("Use Email login for now")
            except Exception as e:
                st.error(f"Google auth error: {str(e)}")
                st.caption("Use Email login instead")
        
        st.caption("Login to save/load profiles")
    else:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.session_state.auth_message:
            st.success(st.session_state.auth_message)
            st.session_state.auth_message = None
        
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            # Also clear Google auth if used
            if "connected" in st.session_state:
                st.session_state.connected = False
            st.rerun()
    
    st.divider()
    
    # ============ Profile Section ============
    st.markdown("### 📋 Active Profile")
    
    # Profile save/load (only when logged in)
    if st.session_state.logged_in:
        saved_profiles = list_full_profiles(st.session_state.username)
        
        with st.expander("💾 Save / Load Profile", expanded=False):
            # Load existing profile
            if saved_profiles:
                selected_profile = st.selectbox(
                    "Load profile:",
                    ["-- Select --"] + saved_profiles,
                    key="profile_selector"
                )
                
                if selected_profile != "-- Select --":
                    if st.button("📂 Load", use_container_width=True):
                        loaded = load_full_profile(st.session_state.username, selected_profile)
                        if loaded:
                            # Update session state with loaded profile
                            st.session_state.profile = {
                                "name": loaded.name,
                                "muzzle_velocity": loaded.rifle.muzzle_velocity,
                                "bc_g7": loaded.cartridge.bc_g7,
                                "mass_grains": loaded.cartridge.mass_grains,
                                "diameter": loaded.cartridge.diameter,
                                "zero_range": loaded.rifle.zero_range,
                                "sight_height": loaded.rifle.sight_height,
                                "twist_rate": loaded.rifle.twist_rate,
                            }
                            st.success(f"✅ Loaded '{selected_profile}'")
                            st.rerun()
            else:
                st.caption("No saved profiles yet")
            
            st.divider()
            
            # Save current profile
            save_name = st.text_input("Save as:", st.session_state.profile["name"], key="save_profile_name")
            if st.button("💾 Save Current Profile", use_container_width=True):
                # Create profile objects
                rifle = RifleProfile(
                    name=save_name,
                    muzzle_velocity=st.session_state.profile["muzzle_velocity"],
                    zero_range=st.session_state.profile["zero_range"],
                    sight_height=st.session_state.profile["sight_height"],
                    twist_rate=st.session_state.profile["twist_rate"]
                )
                cartridge = CartridgeProfile(
                    name=save_name,
                    bc_g7=st.session_state.profile["bc_g7"],
                    mass_grains=st.session_state.profile["mass_grains"],
                    diameter=st.session_state.profile["diameter"]
                )
                full_profile = FullProfile(
                    name=save_name,
                    rifle=rifle,
                    cartridge=cartridge
                )
                
                success, message = save_full_profile(st.session_state.username, full_profile)
                if success:
                    st.success(f"✅ Profile '{save_name}' saved!")
                    st.rerun()
                else:
                    st.error(message)
    
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
    
    # Phone compass - auto updates on click
    import streamlit.components.v1 as components
    
    # Show current heading if set
    if st.session_state.compass_heading > 0:
        st.success(f"🧭 Heading: **{int(st.session_state.compass_heading)}°**")
    
    components.html("""
    <div style="font-family: sans-serif; text-align: center;">
        <button onclick="getCompass()" style="
            background: linear-gradient(135deg, #1a1a2e 0%, #0f5132 100%);
            color: #4CAF50; 
            border: 2px solid #4CAF50; 
            padding: 15px; 
            border-radius: 10px; 
            cursor: pointer;
            font-size: 18px;
            width: 100%;
        ">🧭 GET COMPASS</button>
        <div id="status" style="margin-top: 10px; color: #888;">Tap to get heading</div>
    </div>
    <script>
    let done = false;
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
    function update(h) {
        if (!done) {
            done = true;
            h = Math.round(h);
            document.getElementById('status').innerHTML = '✓ ' + h + '° (' + getDir(h) + ') - Updating page...';
            // Full absolute URL redirect
            window.top.location.replace('https://strelokai.streamlit.app/?heading=' + h);
        }
    }
    function getCompass() {
        done = false;
        document.getElementById('status').innerHTML = 'Reading compass...';
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            DeviceOrientationEvent.requestPermission().then(r => {
                if (r === 'granted') {
                    window.addEventListener('deviceorientation', e => { if(e.alpha) update(e.alpha); }, {once: true});
                } else { document.getElementById('status').innerHTML = 'Denied'; }
            });
        } else if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', e => { if(e.alpha) update(e.alpha); }, {once: true});
        } else {
            document.getElementById('status').innerHTML = 'Not available';
        }
    }
    </script>
    """, height=100)
    
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
