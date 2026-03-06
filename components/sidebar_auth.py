"""
StrelokAI - Sidebar Authentication Component
Renders Email login/signup forms and Google sign-in button in the sidebar.
Version: 1.2.0
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
        
        # DEBUG VIEW for 403 error
        if st.checkbox("Show Google Auth Debug Info"):
            google_config = st.secrets.get("google", {})
            client_id = google_config.get("client_id", "NOT SET")
            redirect_uri = google_config.get("redirect_uri", "NOT SET")
            st.code(f"Client ID: {client_id}\nRedirect: {redirect_uri}", language="text")
            
            from core.google_auth import get_google_auth_url
            if client_id != "NOT SET" and redirect_uri != "NOT SET":
                st.code(get_google_auth_url(client_id, redirect_uri), language="text")
                st.info("Copy the URL above and paste it directly into an Incognito window. If it gives 403 right away, the Google Console config is definitely wrong. If it works there but not when clicking the button, Streamlit Cloud is blocking the referrer.")
            
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
    """Render a styled Google sign-in button that redirects to the standard OAuth flow."""
    google_config = st.secrets.get("google", {})
    client_id = google_config.get("client_id", "")
    redirect_uri = google_config.get("redirect_uri", "https://strelokai.streamlit.app")
    
    if client_id and redirect_uri:
        from core.google_auth import get_google_auth_url
        auth_url = get_google_auth_url(client_id, redirect_uri)
        
        # Use st.components.v1.html to execute JS and break out of Streamlit's iframe
        import streamlit.components.v1 as components
        
        btn_html = f"""
        <html>
        <head>
        <style>
            .g-btn {{
                display: block;
                width: 100%;
                padding: 10px;
                background-color: #4285F4;
                color: white;
                text-align: center;
                border-radius: 8px;
                text-decoration: none;
                font-family: "Source Sans Pro", sans-serif;
                font-weight: 600;
                cursor: pointer;
                border: 1px solid #357ae8;
                box-sizing: border-box;
                font-size: 16px;
                transition: background-color 0.2s;
            }}
            .g-btn:hover {{
                background-color: #357ae8;
            }}
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
        </head>
        <body>
            <button class="g-btn" onclick="window.parent.location.href='{auth_url}'">
                🔵 Sign in with Google
            </button>
        </body>
        </html>
        """
        components.html(btn_html, height=45)
    else:
        st.button("🔵 Sign in with Google", disabled=True, use_container_width=True)
        st.caption("Google credentials not configured")
