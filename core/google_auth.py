"""
StrelokAI - Custom Google Auth Module
Bypasses streamlit-google-auth to handle OAuth2 directly for better stability.
Version: 1.0.0
"""
import streamlit as st
import httpx
import urllib.parse

def get_google_auth_url(client_id: str, redirect_uri: str) -> str:
    """Generate the Google OAuth2 authorization URL."""
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str) -> dict:
    """Exchange the authorization code for access and ID tokens."""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    response = httpx.post(token_url, data=payload)
    response.raise_for_status()
    return response.json()


def get_user_info(access_token: str) -> dict:
    """Get user profile info using the access token."""
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = httpx.get(user_info_url, headers=headers)
    response.raise_for_status()
    return response.json()


def handle_google_oauth():
    """Main OAuth handler to be called in the Streamlit app flow."""
    google_config = st.secrets.get("google", {})
    client_id = google_config.get("client_id")
    client_secret = google_config.get("client_secret")
    redirect_uri = google_config.get("redirect_uri", "https://strelokai.streamlit.app")
    
    if not client_id or not client_secret:
        return False, "Google auth not configured in secrets"
        
    query_params = st.query_params
    
    # Check if we are returning from Google auth
    if "code" in query_params and not st.session_state.get("logged_in"):
        try:
            code = query_params["code"]
            
            # 1. Exchange code
            tokens = exchange_code_for_token(code, client_id, client_secret, redirect_uri)
            
            # 2. Get user info
            user_info = get_user_info(tokens["access_token"])
            
            # 3. Log user in
            st.session_state.logged_in = True
            st.session_state.username = user_info.get("email", "Google User")
            st.session_state.auth_message = f"Welcome, {st.session_state.username}!"

            # Persist across websocket reconnects
            try:
                from core.session_persist import save_session_cookie
                save_session_cookie(st.session_state.username)
            except Exception:
                pass

            # 4. Clean up URL
            st.query_params.clear()
            return True, ""
            
        except Exception as e:
            st.query_params.clear()
            return False, f"Auth Error: {str(e)}"
            
    return False, ""
