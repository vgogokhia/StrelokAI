"""
StrelokAI - Session State Initialization
Initializes all Streamlit session state variables used across the app.
Version: 1.0.0
"""
import streamlit as st

def init_session_state():
    """Initialize all Streamlit session state variables."""
    if "profile" not in st.session_state:
        st.session_state.profile = {
            "name": "Default Profile",
            "muzzle_velocity": 850.0,
            "mv_temp_c": 15.0,
            "temp_sensitivity": 0.1,
            "drag_model": "G7",
            "bc_g7": 0.243,
            "mass_grains": 175.0,
            "diameter": 0.308,
            "bullet_length_in": 1.240,
            "zero_range": 100.0,
            "sight_height": 40.0,
            "twist_rate": 11.25,
            "twist_direction": "right",
        }
    # Forward-compatible top-ups for older session profiles
    for k, default in (
        ("bullet_length_in", 1.240),
        ("twist_direction", "right"),
    ):
        if k not in st.session_state.profile:
            st.session_state.profile[k] = default

    if "weather" not in st.session_state:
        st.session_state.weather = None

    if "theme" not in st.session_state:
        st.session_state.theme = "dark"

    if "target_range" not in st.session_state:
        st.session_state.target_range = 500
    if "recent_ranges" not in st.session_state:
        st.session_state.recent_ranges = []
    if "cant_angle_deg" not in st.session_state:
        st.session_state.cant_angle_deg = 0.0
    if "shot_angle_deg" not in st.session_state:
        st.session_state.shot_angle_deg = 0.0
    if "reticle_name" not in st.session_state:
        st.session_state.reticle_name = "MIL-Dot"

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
