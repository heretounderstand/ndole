import streamlit as st
from supabase import create_client, Client

def initialize_supabase() -> Client:
    # Créer un client Supabase avec l'URL et la clé API stockées dans les secrets Streamlit
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["api_key"]

    # Création du client Supabase
    supabase_client = create_client(url, key)
    
    # Retourner le client Supabase
    # Note: Supabase intègre à la fois la base de données et le stockage,
    # nous n'avons donc pas besoin de retourner des objets séparés
    return supabase_client