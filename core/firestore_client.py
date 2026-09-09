"""
StrelokAI - Firestore Client Singleton
Initialises a google-cloud-firestore client from Streamlit secrets.
Version: 1.1.0 - graceful "not configured" detection
"""
import streamlit as st

from core.secrets import secret_section


class FirestoreNotConfigured(RuntimeError):
    """Raised when no ``[gcp_service_account]`` section exists in secrets."""


def is_firestore_configured() -> bool:
    cfg = secret_section("gcp_service_account")
    return bool(cfg.get("project_id") and cfg.get("private_key"))


@st.cache_resource
def get_firestore_client():
    """Return a cached Firestore client built from st.secrets."""
    key_dict = secret_section("gcp_service_account")
    if not key_dict:
        raise FirestoreNotConfigured(
            "Firestore is not configured (missing [gcp_service_account] in secrets)."
        )
    from google.cloud import firestore
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(key_dict)
    # Database ID defaults to "strelokai"; override with `database_id` in secrets.
    db_id = key_dict.get("database_id", "strelokai")
    return firestore.Client(credentials=creds, project=key_dict["project_id"], database=db_id)
