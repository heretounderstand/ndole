import streamlit as st
from streamlit_cookies_controller import CookieController
from supabase import create_client, Client

controller = CookieController()

@st.cache_resource
def initialize_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["api_key"]
    supabase_client = create_client(url, key)
    return supabase_client