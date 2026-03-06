"""
StrelokAI - AI-Powered Ballistic Calculator
Main Streamlit Application
Version: 1.1.0
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

# Main content area
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
    bc_g7=st.session_state.profile["bc_g7"],
    mass_grains=st.session_state.profile["mass_grains"],
    diameter=st.session_state.profile["diameter"],
    zero_range=st.session_state.profile["zero_range"],
    target_range=st.session_state.target_range,
    temp_c=temp_c,
    pressure=pressure,
    humidity=humidity,
    altitude=altitude,
    wind_speed=st.session_state.wind_speed,
    wind_deg=wind_deg
)

# AI Features Section
st.divider()
render_ai_features()

# Footer
st.divider()
st.caption(f"{APP_NAME} v{VERSION} | Made with ❤️ for precision shooters")
