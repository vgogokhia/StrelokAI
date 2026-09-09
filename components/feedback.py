"""
ballistics.ge - Feedback form
Stores messages in Firestore (collection "feedback"); admins listed in
secrets [admin] users = [...] see the inbox in the same tab.
Version: 1.0.0
"""
import time
from datetime import datetime

import streamlit as st

from config import VERSION
from core.firestore_client import is_firestore_configured, get_firestore_client
from core.secrets import secret_section

_MIN_INTERVAL_S = 60
_MAX_LEN = 2000


def _admins() -> set[str]:
    users = secret_section("admin").get("users", [])
    if isinstance(users, str):
        users = [users]
    return {str(u).lower() for u in users}


def _save(kind: str, message: str, contact: str) -> None:
    ss = st.session_state
    get_firestore_client().collection("feedback").add({
        "kind": kind,
        "message": message.strip()[:_MAX_LEN],
        "contact": contact.strip()[:200],
        "username": ss.get("username") if ss.get("logged_in") else None,
        "profile": {k: ss.get("profile", {}).get(k) for k in ("chambering", "cartridge", "muzzle_velocity")},
        "units": ss.get("units"),
        "version": VERSION,
        "created_at": datetime.utcnow().isoformat(),
        "read": False,
    })


def render_feedback():
    st.markdown("### 💬 Feedback / უკუკავშირი")
    st.caption(
        "იპოვე ხარვეზი, გინდა ახალი ფუნქცია, ან უბრალოდ აზრი გაქვს? დაწერე აქ. "
        "Found a bug or want a feature? Write here."
    )

    if not is_firestore_configured():
        st.info("Feedback is not configured on this server. Write to the author directly.")
        return

    with st.form("feedback_form", clear_on_submit=True):
        kind = st.radio(
            "Type", ["🐞 ხარვეზი / Bug", "💡 იდეა / Feature", "💬 სხვა / Other"],
            horizontal=True, label_visibility="collapsed",
        )
        message = st.text_area(
            "შეტყობინება / Message", height=140, max_chars=_MAX_LEN,
            placeholder="რა მოხდა, რა მოელოდი, რომელი ვაზნა/მანძილი… / What happened, what you expected, which load/range…",
        )
        contact = st.text_input(
            "კონტაქტი (არასავალდებულო) / Contact (optional)",
            placeholder="email, Facebook, phone — თუ გინდა პასუხი მოგწერო",
        )
        sent = st.form_submit_button("📨 გაგზავნა / Send", type="primary", width="stretch")

    if sent:
        now = time.time()
        if len(message.strip()) < 5:
            st.warning("შეტყობინება ძალიან მოკლეა. / Message is too short.")
        elif now - st.session_state.get("_feedback_sent_at", 0) < _MIN_INTERVAL_S:
            st.warning("ერთი წუთი დაიცადე შემდეგ შეტყობინებამდე. / Please wait a minute before sending again.")
        else:
            try:
                _save(kind, message, contact)
                st.session_state._feedback_sent_at = now
                st.success("მადლობა! მივიღე. / Thanks, received.")
            except Exception as exc:
                st.error(f"ვერ გაიგზავნა: {exc}")

    # ---- admin inbox ------------------------------------------------------
    user = (st.session_state.get("username") or "").lower()
    if st.session_state.get("logged_in") and user in _admins():
        st.divider()
        st.markdown("#### 📥 Inbox (admin)")
        try:
            docs = list(
                get_firestore_client().collection("feedback")
                .order_by("created_at", direction="DESCENDING").limit(100).stream()
            )
        except Exception as exc:
            st.error(f"Could not load feedback: {exc}")
            return
        if not docs:
            st.caption("No feedback yet.")
            return
        show_read = st.checkbox("Show read", value=False)
        for d in docs:
            f = d.to_dict()
            if f.get("read") and not show_read:
                continue
            with st.container(border=True):
                st.markdown(
                    f"**{f.get('kind','')}** · {f.get('created_at','')[:16].replace('T',' ')} · "
                    f"{f.get('username') or 'anonymous'} · {f.get('contact') or ''}"
                )
                st.write(f.get("message", ""))
                p = f.get("profile") or {}
                st.caption(f"v{f.get('version')} · {f.get('units')} · {p.get('chambering')} / {p.get('cartridge')}")
                if not f.get("read") and st.button("Mark read", key=f"fb_read_{d.id}"):
                    d.reference.update({"read": True})
                    st.rerun()
