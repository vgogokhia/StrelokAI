"""
Persist the logged-in user across Streamlit websocket reconnects.

Streamlit's ``st.session_state`` is bound to the websocket, so when the
browser goes idle and the socket disconnects, the next reconnect gets
a fresh session — the user appears logged out even though the Google
OAuth on the Google side is still valid. We store a signed, opaque
cookie with the username and read it back at every app start.

The cookie is HMAC-signed with a server secret (``st.secrets["auth"]
["cookie_secret"]`` if present, otherwise a constant fallback so the
feature still works in local development).
"""
from __future__ import annotations

import hmac
import hashlib
import time
from typing import Optional

import streamlit as st

try:
    import extra_streamlit_components as stx  # type: ignore
    _COOKIE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _COOKIE_AVAILABLE = False


_COOKIE_NAME = "strelokai_session"
_COOKIE_TTL_DAYS = 30
_DEFAULT_SECRET = "strelokai-dev-secret-change-in-secrets-toml"


def _secret() -> str:
    auth_cfg = st.secrets.get("auth", {}) if hasattr(st, "secrets") else {}
    return auth_cfg.get("cookie_secret", _DEFAULT_SECRET)


def _sign(payload: str) -> str:
    return hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()


def _encode(username: str) -> str:
    ts = str(int(time.time()))
    body = f"{username}|{ts}"
    return f"{body}|{_sign(body)}"


def _decode(token: str) -> Optional[str]:
    if not token or token.count("|") != 2:
        return None
    body, sig = token.rsplit("|", 1)
    if not hmac.compare_digest(sig, _sign(body)):
        return None
    username, ts = body.rsplit("|", 1)
    try:
        issued = int(ts)
    except ValueError:
        return None
    max_age = _COOKIE_TTL_DAYS * 86400
    if time.time() - issued > max_age:
        return None
    return username


@st.cache_resource(show_spinner=False)
def _cookie_manager():
    if not _COOKIE_AVAILABLE:
        return None
    return stx.CookieManager(key="strelokai_cookie_mgr")


def restore_session_from_cookie() -> None:
    """If the user has a valid persistent cookie, mark them logged in."""
    if st.session_state.get("logged_in"):
        return
    cm = _cookie_manager()
    if cm is None:
        return
    token = cm.get(_COOKIE_NAME)
    if not token:
        return
    username = _decode(token)
    if username:
        st.session_state.logged_in = True
        st.session_state.username = username


def save_session_cookie(username: str) -> None:
    cm = _cookie_manager()
    if cm is None:
        return
    from datetime import datetime, timedelta
    expires = datetime.utcnow() + timedelta(days=_COOKIE_TTL_DAYS)
    cm.set(_COOKIE_NAME, _encode(username), expires_at=expires, key="strelokai_cookie_set")


def clear_session_cookie() -> None:
    cm = _cookie_manager()
    if cm is None:
        return
    cm.delete(_COOKIE_NAME, key="strelokai_cookie_del")
