"""
ballistics.ge - Safe access to Streamlit secrets.

``st.secrets`` raises ``StreamlitSecretNotFoundError`` when no
``secrets.toml`` exists at all (typical for a fresh local checkout), and
``KeyError`` for missing keys. Every optional integration (Google login,
Firestore, Gemini, cookie signing) must degrade gracefully instead of
crashing the whole app, so all secret lookups go through these helpers.
Version: 1.0.0
"""
from __future__ import annotations

import os
from typing import Any, Mapping

import streamlit as st


def secret_section(name: str) -> dict:
    """Return a secrets section (e.g. ``[google]``) as a plain dict, or ``{}``."""
    try:
        value = st.secrets[name]
    except Exception:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def secret_value(key: str, default: Any = None, *, env: bool = True) -> Any:
    """Return a top-level secret, falling back to the environment variable."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    if env:
        env_val = os.getenv(key)
        if env_val is not None:
            return env_val
    return default


def has_secret_section(name: str) -> bool:
    return bool(secret_section(name))


def secrets_status() -> tuple[str, str]:
    """('ok'|'missing'|'error', detail) — used for a sidebar diagnostic."""
    try:
        keys = list(st.secrets.keys())
        return "ok", f"{len(keys)} top-level entries: {', '.join(sorted(keys))[:120]}"
    except Exception as exc:  # StreamlitSecretNotFoundError, TOML decode errors
        msg = str(exc)
        if "No secrets found" in msg:
            hint = ""
            if os.getenv("STREAMLIT_SECRETS_TOML"):
                hint = " (STREAMLIT_SECRETS_TOML is set but no file was written — check deploy logs)"
            return "missing", "no secrets.toml" + hint
        return "error", msg[:300]
