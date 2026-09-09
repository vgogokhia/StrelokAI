"""
ballistics.ge - Remember the working state across page refreshes.

``st.session_state`` dies with the browser tab, so every refresh used to
reset the rifle, ammo, distance, wind and atmosphere to defaults. This
module snapshots the fields a shooter actually types in and restores them:

* for everyone: a base64-encoded JSON cookie in the same browser
  (via extra_streamlit_components, like the login cookie);
* for logged-in users additionally: a Firestore document
  ``users/{username}/state/last`` so the state follows them across devices.

Saving happens at the end of every script run, only when the snapshot
actually changed. Restoring happens once per session, before any widget
is drawn; the cookie component needs one round-trip before it can report
cookies, so restore is retried for the first few runs.
Version: 1.0.0
"""
from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timedelta

import streamlit as st

from core.session_persist import _cookie_manager, read_cookies
from core.firestore_client import is_firestore_configured

_COOKIE = "strelokai_state"
_COOKIE_TTL_DAYS = 90
_MAX_RESTORE_RUNS = 3

# Plain session-state values to persist.
_STATE_KEYS = (
    "profile", "target_range", "recent_ranges",
    "wind_speed", "wind_dir_deg", "compass_heading",
    "temp_c", "pressure", "humidity", "altitude_m",
    "location_lat", "location_lon",
    "shot_angle_deg", "cant_angle_deg",
    "units", "angular_unit", "click_value",
    "reticle_name", "turret_per_rev",
    "_last_loaded_rifle", "_last_loaded_ammo",
)

# Widgets that own their value through a key: (widget key, state key, to-widget)
_WIDGET_MIRRORS = (
    ("units_radio", "units", lambda v: "Imperial" if v == "imperial" else "Metric"),
    ("angular_radio", "angular_unit", lambda v: v),
    ("click_value_select", "click_value", lambda v: v),
    ("reticle_selector", "reticle_name", lambda v: v),
    ("save_rifle_name", "_last_loaded_rifle", lambda v: v or ""),
    ("save_ammo_name", "_last_loaded_ammo", lambda v: v or ""),
)


# ---------------------------------------------------------------------------
# Snapshot / apply
# ---------------------------------------------------------------------------

def snapshot() -> dict:
    out = {}
    for k in _STATE_KEYS:
        if k in st.session_state:
            v = st.session_state[k]
            if isinstance(v, dict):
                v = dict(v)
            out[k] = v
    return out


def apply(data: dict) -> None:
    """Write a snapshot into session_state (before widgets are created)."""
    if not isinstance(data, dict):
        return
    for k in _STATE_KEYS:
        if k in data and data[k] is not None:
            if k == "profile":
                prof = dict(st.session_state.get("profile", {}))
                prof.update(data[k])
                st.session_state.profile = prof
            else:
                st.session_state[k] = data[k]
    for widget_key, state_key, conv in _WIDGET_MIRRORS:
        if state_key in data and data[state_key] is not None:
            st.session_state[widget_key] = conv(data[state_key])
    # Force the range widgets to re-seed from the restored target_range.
    for k in ("target_range_num", "target_range_slider"):
        st.session_state.pop(k, None)


def _encode(data: dict) -> str:
    raw = json.dumps(data, separators=(",", ":"), default=float).encode()
    return base64.urlsafe_b64encode(raw).decode()


def _decode(token: str) -> dict | None:
    try:
        return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
    except Exception:
        return None


def _fingerprint(data: dict) -> str:
    return json.dumps(data, sort_keys=True, default=float)


# ---------------------------------------------------------------------------
# Firestore (logged-in users)
# ---------------------------------------------------------------------------

def _fs_doc(username: str):
    from core.firestore_client import get_firestore_client
    return (get_firestore_client().collection("users").document(username.lower())
            .collection("state").document("last"))


def _fs_load(username: str) -> dict | None:
    try:
        doc = _fs_doc(username).get()
        return doc.to_dict().get("data") if doc.exists else None
    except Exception:
        return None


def _fs_save(username: str, data: dict) -> None:
    try:
        _fs_doc(username).set({"data": data, "updated_at": datetime.utcnow().isoformat()})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public hooks (call at the top and bottom of app.py)
# ---------------------------------------------------------------------------

def restore_app_state() -> None:
    ss = st.session_state
    ss.setdefault("_state_restore_runs", 0)

    # 1. Logged-in user: load their cloud state once per login.
    username = ss.get("username") if ss.get("logged_in") else None
    if username and ss.get("_state_fs_user") != username and is_firestore_configured():
        ss._state_fs_user = username
        data = _fs_load(username)
        if data:
            apply(data)
            ss._state_restored = True
            ss._state_last_saved = _fingerprint(snapshot())
            return

    # 2. Browser cookie (everyone). The cookie component reports nothing on
    #    the very first run, so retry a few times, but never after we saved.
    if ss.get("_state_restored") or ss.get("_state_last_saved"):
        return
    if ss._state_restore_runs >= _MAX_RESTORE_RUNS:
        ss._state_restored = True
        return
    ss._state_restore_runs += 1
    if _cookie_manager() is None:
        ss._state_restored = True
        return
    token = read_cookies().get(_COOKIE)
    if token:
        data = _decode(token)
        if data:
            apply(data)
        ss._state_restored = True
        ss._state_last_saved = _fingerprint(snapshot())


def save_app_state() -> None:
    ss = st.session_state
    if not ss.get("_state_restored"):
        return  # don't overwrite a cookie we haven't read yet
    data = snapshot()
    fp = _fingerprint(data)
    if fp == ss.get("_state_last_saved"):
        return
    ss._state_last_saved = fp

    cm = _cookie_manager()
    if cm is not None:
        try:
            cm.set(
                _COOKIE, _encode(data), key="strelokai_state_set",
                expires_at=datetime.utcnow() + timedelta(days=_COOKIE_TTL_DAYS),
            )
        except Exception:
            pass

    username = ss.get("username") if ss.get("logged_in") else None
    if username and is_firestore_configured():
        # Light debounce so slider drags don't hammer Firestore.
        now = time.time()
        if now - ss.get("_state_fs_saved_at", 0.0) > 2.0:
            ss._state_fs_saved_at = now
            _fs_save(username, data)


def forget_app_state() -> None:
    """Reset to defaults and remember that (used by the 'Reset' button).

    Everything except the cookie-manager component instance is dropped so
    ``init_session_state`` repopulates defaults on the next run; the
    end-of-run save then overwrites the cookie with those defaults. (A
    cookie *delete* followed by ``st.rerun`` is unreliable: the rerun can
    pre-empt the delete before the browser applies it.)
    """
    keep = st.session_state.get("_cookie_manager_instance")
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    if keep is not None:
        st.session_state._cookie_manager_instance = keep
    st.session_state._state_restored = True   # don't re-apply the old cookie
    st.session_state._state_fs_user = None
