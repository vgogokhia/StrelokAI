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

        # Streamlit button that triggers a JS redirect in the current tab.
        # st.link_button always opens a new tab; plain HTML anchors with
        # target="_top" are blocked inside Streamlit Cloud's iframe
        # sandbox. Using window.open(url, "_self") from st.components.html
        # navigates the parent document in place.
        if st.button("🔵 Sign in with Google", use_container_width=True, key="google_signin_btn"):
            import streamlit.components.v1 as components
            components.html(
                f"""
                <script>
                    window.parent.location.href = "{auth_url}";
                </script>
                """,
                height=0,
            )
    else:
        st.button("🔵 Sign in with Google", disabled=True, use_container_width=True)
        st.caption("Google credentials not configured")
