import streamlit as st
from supabase import create_client, Client
import pandas as pd

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def carregar_tabela(nome_tabela: str, ordem: str = "id") -> pd.DataFrame:
    try:
        sb = get_supabase()
        res = sb.table(nome_tabela).select("*").order(ordem).execute()
        if res.data:
            return pd.DataFrame(res.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados de '{nome_tabela}': {e}")
        return pd.DataFrame()

def inserir_registro(nome_tabela: str, dados: dict) -> bool:
    try:
        sb = get_supabase()
        sb.table(nome_tabela).insert(dados).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar em '{nome_tabela}': {e}")
        return False

def atualizar_registro(nome_tabela: str, registro_id: int, dados: dict) -> bool:
    try:
        sb = get_supabase()
        sb.table(nome_tabela).update(dados).eq("id", registro_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar '{nome_tabela}': {e}")
        return False

def excluir_registro(nome_tabela: str, registro_id: int) -> bool:
    try:
        sb = get_supabase()
        sb.table(nome_tabela).delete().eq("id", registro_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir de '{nome_tabela}': {e}")
        return False
