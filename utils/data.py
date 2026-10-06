import streamlit as st
from supabase import create_client, Client


def _create_client() -> Client:
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["api_key"])


@st.cache_resource
def get_db() -> Client:
    """Process-wide client for table and storage access.

    It is shared by every Streamlit session, so it must never be used to sign a
    user in: the resulting session would be attached to all other users' requests.
    """
    return _create_client()


def get_auth_client() -> Client:
    """Fresh, throwaway client for sign-up / sign-in / password changes."""
    return _create_client()


# Backwards-compatible name.
initialize_supabase = get_db
