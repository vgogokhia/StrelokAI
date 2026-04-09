"""
StrelokAI - AI-Powered Ballistic Calculator
Main Streamlit Application
Version: 1.3.0
"""
import streamlit as st

# Page configuration MUST be the first Streamlit command
from config import APP_NAME, VERSION
st.set_page_config(
    page_title=f"{APP_NAME} - Ballistic Calculator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import core modules
from core.state import init_session_state
from core.theme import apply_theme
from core.url_handler import process_query_params

# Import UI components
from components.sidebar_auth import render_sidebar_auth
from components.sidebar_profiles import render_sidebar_profiles
from components.target_wind import render_target_section, render_wind_section
from components.atmosphere import render_atmosphere_section
from components.solution import render_solution_section
from components.ai_features import render_ai_features
from components.dope_card import render_dope_card
from components.reticle import render_reticle
from components.turret import render_turret
from components.range_estimator import render_range_estimator


# Initialize Session State
init_session_state()

# Process URL Params & OAuth Return
process_query_params()
from core.google_auth import handle_google_oauth
google_auth_success, google_err = handle_google_oauth()
if google_err:
    st.sidebar.error(google_err)

# Apply Theme
apply_theme(st.session_state.theme)

# Header - compact for mobile
st.markdown(f"**🎯 {APP_NAME}** | Ballistic Calculator |")

# Sidebar - Settings
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Theme selector
    theme_index = 1 if st.session_state.theme == "red" else 0
    theme = st.radio("Theme", ["Dark", "Red (NVG)"], index=theme_index, horizontal=True,
                     key="theme_radio", on_change=lambda: setattr(st.session_state, 'theme', 'red' if 'Red' in st.session_state.theme_radio else 'dark'))
    
    if "Red" in theme:
        st.session_state.theme = "red"
    else:
        st.session_state.theme = "dark"
    
    st.divider()
    
    # Rendering Sidebar Components
    render_sidebar_auth()
    st.divider()
    render_sidebar_profiles()

# Main tabbed interface
tab_calc, tab_dope, tab_reticle, tab_turret, tab_range = st.tabs(
    ["🎯 Calculator", "📋 Dope Card", "🔭 Reticle", "🎛️ Turret", "📏 Range Est."]
)

with tab_calc:
    col_target, col_wind = st.columns([2, 1])

    # Target & Wind
    render_target_section(col_target)
    wind_deg = render_wind_section(col_wind)

    # Atmosphere
    temp_c, pressure, humidity, altitude = render_atmosphere_section()

    # Calculate Solution
    st.divider()
    render_solution_section(
        muzzle_velocity=st.session_state.profile["muzzle_velocity"],
        mv_temp_c=st.session_state.profile.get("mv_temp_c", 15.0),
        temp_sensitivity=st.session_state.profile.get("temp_sensitivity", 0.1),
        drag_model=st.session_state.profile.get("drag_model", "G7"),
        bc_val=st.session_state.profile["bc_g7"],
        mass_grains=st.session_state.profile["mass_grains"],
        diameter=st.session_state.profile["diameter"],
        zero_range=st.session_state.profile["zero_range"],
        target_range=st.session_state.target_range,
        temp_c=temp_c,
        pressure=pressure,
        humidity=humidity,
        altitude=altitude,
        wind_speed=st.session_state.wind_speed,
        wind_deg=wind_deg,
        bullet_length_in=st.session_state.profile.get("bullet_length_in", 1.0),
        twist_rate_inches=st.session_state.profile.get("twist_rate", 10.0),
        twist_direction=st.session_state.profile.get("twist_direction", "right"),
        sight_height_mm=st.session_state.profile.get("sight_height", 40.0),
        elevation_angle_deg=float(st.session_state.get("shot_angle_deg", 0.0)),
        cant_angle_deg=float(st.session_state.get("cant_angle_deg", 0.0)),
    )

    # AI Features Section
    st.divider()
    render_ai_features()

with tab_dope:
    render_dope_card()

with tab_reticle:
    render_reticle()

with tab_turret:
    render_turret()

with tab_range:
    render_range_estimator()

# Footer
st.divider()
st.caption(f"{APP_NAME} v{VERSION} | Made with ❤️ for precision shooters")
