"""
ballistics.ge - Ballistic Calculator
Main application
Version: 1.5.0
"""
import streamlit as st

# Page configuration MUST be the first Streamlit command
from config import APP_NAME, VERSION, TAGLINE
st.set_page_config(
    page_title=f"{APP_NAME} — Ballistic Calculator | MRAD, MOA, .308, .22 LR",
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
from core.seo import inject_head_tags, render_header, render_about

from components.sidebar_auth import render_sidebar_auth
from components.sidebar_profiles import render_sidebar_profiles
from components.target_wind import render_target_section, render_wind_section
from components.atmosphere import render_atmosphere_section
from components.solution import render_solution_section
from components.dope_card import render_dope_card
from components.reticle import render_reticle
from components.turret import render_turret
from components.range_estimator import render_range_estimator
from components.feedback import render_feedback


init_session_state()

# Restore logged-in user from persistent cookie (survives idle websocket
# disconnects that would otherwise log the user out).
from core.session_persist import restore_session_from_cookie, begin_script_run
begin_script_run()
restore_session_from_cookie()

# Bring back the last used rifle/ammo/range/wind/atmosphere after a refresh.
from core.app_state import restore_app_state, save_app_state, forget_app_state
restore_app_state()

process_query_params()
from core.google_auth import handle_google_oauth
google_auth_success, google_err = handle_google_oauth()
if google_err:
    st.sidebar.error(google_err)

st.session_state.theme = "dark"
apply_theme(st.session_state.theme)
inject_head_tags()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    # Keyed widgets are seeded through session_state (no index=/value=), so
    # restoring a remembered state never triggers Streamlit's
    # "default value AND session state" warning.
    c_units, c_ang = st.columns(2)
    with c_units:
        st.session_state.setdefault(
            "units_radio", "Imperial" if st.session_state.get("units") == "imperial" else "Metric")
        units_choice = st.radio("Units", ["Metric", "Imperial"], horizontal=True, key="units_radio")
        st.session_state.units = "imperial" if units_choice == "Imperial" else "metric"
    with c_ang:
        st.session_state.setdefault("angular_radio", st.session_state.get("angular_unit", "MRAD"))
        st.session_state.angular_unit = st.radio(
            "Angular", ["MRAD", "MOA"], horizontal=True, key="angular_radio")

    click_labels = list(CLICK_OPTIONS.keys())
    cur_click = st.session_state.get("click_value_select") or st.session_state.get("click_value", "0.1 MRAD")
    # Keep the click list in the same family as the angular unit.
    if st.session_state.angular_unit not in cur_click:
        cur_click = "0.1 MRAD" if st.session_state.angular_unit == "MRAD" else "1/4 MOA"
    if st.session_state.get("click_value_select") != cur_click:
        st.session_state.click_value_select = cur_click
    st.session_state.click_value = st.selectbox(
        "Scope click value", click_labels, key="click_value_select")

    st.divider()
    render_sidebar_auth()
    st.divider()
    render_sidebar_profiles()
    st.divider()
    if st.button("↺ Reset everything to defaults", width="stretch",
                 help="Clears the remembered rifle, ammo, range, wind and atmosphere."):
        forget_app_state()
        init_session_state()
        st.rerun()

# ---------------------------------------------------------------------------
# Main tabbed interface
# ---------------------------------------------------------------------------
render_header()
tab_calc, tab_dope, tab_reticle, tab_turret, tab_range, tab_fb = st.tabs(
    ["Calculator", "Dope Card", "Reticle", "Turret", "Range Est.", "💬 Feedback"]
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

with tab_fb:
    render_feedback()

st.divider()
render_about()
st.caption(
    f"© {APP_NAME} · v{VERSION} · free ballistic calculator, made in Georgia 🇬🇪 for precision shooters · "
    "your inputs are remembered on this device"
)

# Persist the working state (cookie + Firestore when logged in).
save_app_state()
