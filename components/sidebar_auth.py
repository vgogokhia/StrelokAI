"""
StrelokAI - Sidebar Authentication Component
Renders Email login/signup forms and Google sign-in button in the sidebar.
Version: 1.1.0
"""
import streamlit as st
from auth import create_user, authenticate_user

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
            st.rerun()


def _render_google_login():
    """Render a styled Google sign-in button."""
    try:
        from streamlit_google_auth import Authenticate
        import json
        
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
            
            if st.session_state.get("connected"):
                st.session_state.logged_in = True
                st.session_state.username = st.session_state.get("user_info", {}).get("email", "Google User")
                st.session_state.auth_message = f"Welcome, {st.session_state.username}!"
                st.rerun()
            else:
                authenticator.login()
        else:
            # No Google credentials configured — show disabled-style button
            st.button("🔵 Sign in with Google", disabled=True, use_container_width=True)
            st.caption("Google auth not configured")
    except ImportError:
        st.button("🔵 Sign in with Google", disabled=True, use_container_width=True)
        st.caption("Requires: streamlit-google-auth")
    except Exception as e:
        st.button("🔵 Sign in with Google", disabled=True, use_container_width=True)
        st.caption(f"Google auth error: {str(e)}")
