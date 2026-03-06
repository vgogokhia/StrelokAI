"""
StrelokAI - URL Query Parameter Handler
Processes URL query params (e.g. compass heading from mobile device).
Version: 1.0.0
"""
import streamlit as st

def process_query_params():
    """Check for compass heading from URL query parameters and update state."""
    query_params = st.query_params
    if "heading" in query_params:
        try:
            new_heading = int(query_params["heading"])
            st.session_state.compass_heading = new_heading
            st.query_params.clear()  # Clear the param after reading
        except:
            pass
