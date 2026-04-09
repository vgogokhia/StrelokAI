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

        auth_tab = st.radio(
            "auth_mode",
            ["Login", "Sign Up"],
            horizontal=True,
            label_visibility="collapsed",
            key="auth_tab_radio",
        )

        # Use an st.form so the username + password + submit are processed
        # together in a single rerun (fixes the race where the submit button
        # fired before the text inputs committed their values to session_state).
        is_signup = (auth_tab == "Sign Up")
        form_key = "signup_form" if is_signup else "login_form"
        submit_label = "Create Account" if is_signup else "Login"

        with st.form(form_key, clear_on_submit=False):
            username_val = st.text_input("Username", key=f"{form_key}_username")
            password_val = st.text_input("Password", type="password", key=f"{form_key}_password")
            submitted = st.form_submit_button(
                submit_label, type="primary", use_container_width=True
            )

        if submitted:
            username_val = (username_val or "").strip()
            password_val = password_val or ""
            if not username_val or not password_val:
                st.error("Please enter username and password")
            else:
                if is_signup:
                    success, message = create_user(username_val, password_val)
                    welcome = f"Account created! Welcome, {username_val}!"
                else:
                    success, message = authenticate_user(username_val, password_val)
                    welcome = f"Welcome, {username_val}!"

                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username_val
                    st.session_state.auth_message = welcome
                    try:
                        save_session_cookie(username_val)
                    except Exception:
                        pass
                    st.rerun()
                else:
                    st.error(message)
        
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
