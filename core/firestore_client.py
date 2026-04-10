"""
StrelokAI - Firestore Client Singleton
Initialises a google-cloud-firestore client from Streamlit secrets.
Version: 1.0.0
"""
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account


@st.cache_resource
def get_firestore_client() -> firestore.Client:
    """Return a cached Firestore client built from st.secrets."""
    key_dict = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds, project=key_dict["project_id"])
