"""
StrelokAI - Sidebar Authentication Component
Renders Email login/signup forms and Google sign-in button in the sidebar.
Version: 1.2.0
"""
import streamlit as st
from auth import create_user, authenticate_user
from core.session_persist import save_session_cookie, clear_session_cookie

def render_sidebar_auth():
    if not st.session_state.logged_in:
        st.markdown("### 🔐 Login")
        
        # Email login/signup form
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
                        try:
                            save_session_cookie(username_val)
                        except Exception:
                            pass
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
                        try:
                            save_session_cookie(username_val)
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter username and password")
        
        # Divider between email and Google
        st.markdown("---")
        
        # Google Sign-In button
        _render_google_login()

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
            try:
                clear_session_cookie()
            except Exception:
                pass
            st.rerun()


def _render_google_login():
    """Render a styled Google sign-in button that redirects to the standard OAuth flow."""
    google_config = st.secrets.get("google", {})
    client_id = google_config.get("client_id", "")
    redirect_uri = google_config.get("redirect_uri", "https://strelokai.streamlit.app")
    
    if client_id and redirect_uri:
        from core.google_auth import get_google_auth_url
        auth_url = get_google_auth_url(client_id, redirect_uri)

        # Streamlit Cloud's iframe sandbox blocks both window.top
        # navigation (so components.html redirects do nothing) and
        # window.close() on user-opened tabs. The only reliable option is
        # st.link_button, which opens Google in a new tab. The original
        # tab still picks up the login via the persistent cookie on its
        # next reconnect, so both tabs end up logged in and either one
        # can be closed.
        st.link_button(
            "🔵 Sign in with Google",
            url=auth_url,
            use_container_width=True,
        )
        st.caption("Opens in a new tab. You can close either tab after logging in.")
    else:
        st.button("🔵 Sign in with Google", disabled=True, use_container_width=True)
        st.caption("Google credentials not configured")
