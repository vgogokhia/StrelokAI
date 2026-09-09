"""
StrelokAI - AI-Powered Ballistic Calculator
Main Streamlit Application
Version: 1.4.0
"""
import streamlit as st

# Page configuration MUST be the first Streamlit command
from config import APP_NAME, VERSION
st.set_page_config(
    page_title=f"{APP_NAME} - Ballistic Calculator",
    page_icon="🎯",
    layout="wide",
    # "auto": open on desktop, collapsed on phones so the solution is visible
    # immediately instead of a full-screen sidebar.
    initial_sidebar_state="auto",
)

from core.state import init_session_state
from core.theme import apply_theme
from core.url_handler import process_query_params
from core.units import CLICK_OPTIONS

from components.sidebar_auth import render_sidebar_auth
from components.sidebar_profiles import render_sidebar_profiles
from components.target_wind import render_target_section, render_wind_section
from components.atmosphere import render_atmosphere_section
from components.solution import render_solution_section
from components.dope_card import render_dope_card
from components.reticle import render_reticle
from components.turret import render_turret
from components.range_estimator import render_range_estimator


init_session_state()

# Restore logged-in user from persistent cookie (survives idle websocket
# disconnects that would otherwise log the user out).
from core.session_persist import restore_session_from_cookie
restore_session_from_cookie()

process_query_params()
from core.google_auth import handle_google_oauth
google_auth_success, google_err = handle_google_oauth()
if google_err:
    st.sidebar.error(google_err)

st.session_state.theme = "dark"
apply_theme(st.session_state.theme)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    c_units, c_ang = st.columns(2)
    with c_units:
        units_index = 1 if st.session_state.get("units", "metric") == "imperial" else 0
        units_choice = st.radio(
            "Units", ["Metric", "Imperial"], index=units_index, horizontal=True, key="units_radio",
        )
        st.session_state.units = "imperial" if units_choice == "Imperial" else "metric"
    with c_ang:
        ang_index = 1 if st.session_state.get("angular_unit", "MRAD") == "MOA" else 0
        st.session_state.angular_unit = st.radio(
            "Angular", ["MRAD", "MOA"], index=ang_index, horizontal=True, key="angular_radio",
        )

    click_labels = list(CLICK_OPTIONS.keys())
    # Keep the click list in the same family as the angular unit by default.
    cur_click = st.session_state.get("click_value", "0.1 MRAD")
    if st.session_state.angular_unit not in cur_click:
        cur_click = "0.1 MRAD" if st.session_state.angular_unit == "MRAD" else "1/4 MOA"
    st.session_state.click_value = st.selectbox(
        "Scope click value", click_labels, index=click_labels.index(cur_click), key="click_value_select",
    )

    st.divider()
    render_sidebar_auth()
    st.divider()
    render_sidebar_profiles()

# ---------------------------------------------------------------------------
# Main tabbed interface
# ---------------------------------------------------------------------------
tab_calc, tab_dope, tab_reticle, tab_turret, tab_range = st.tabs(
    ["Calculator", "Dope Card", "Reticle", "Turret", "Range Est."]
)

with tab_calc:
    col_target, col_wind = st.columns([2, 1])
    render_target_section(col_target)
    render_wind_section(col_wind)
    render_atmosphere_section()
    st.divider()
    render_solution_section()

with tab_dope:
    render_dope_card()

with tab_reticle:
    render_reticle()

with tab_turret:
    render_turret()

with tab_range:
    render_range_estimator()

st.divider()
st.caption(f"{APP_NAME} v{VERSION} | Made with ❤️ for precision shooters")
