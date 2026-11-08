import streamlit as st
import pandas as pd
import os

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Sócios - Painel ARO", page_icon="👥", layout="wide")

# --- TRAVA DE SEGURANÇA POR CATEGORIA DE USUÁRIO ---
# Só permite o acesso para Master e Diretoria. Bloqueia Sócios e Visitantes.
if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop() # Interrompe o carregamento do restante do arquivo na tela

# Título do Módulo
st.title("👥 Cadastro de Sócios - ARO Rio do Sul")

# Validar se o usuário possui nível Master para liberar a edição administrativa
is_master = st.session_state.get("user_role") == "master"

# Garantir o carregamento centralizado sincronizado com o app.py
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv("backup_socios.csv") if os.path.exists("backup_socios.csv") else pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])

df_socios = st.session_state["dados_socios_internos"]

# --- 1. PAINEL DE CONTROLE E EXIBIÇÃO ---
st.markdown("### 📊 Listagem de Sócios Cadastrados")

if is_master:
    st.caption("💡 Como Master, você pode editar diretamente as células abaixo. As alterações são guardadas na memória do sistema.")
    
    # Editor de dados dinâmico habilitado apenas para o Master
    df_editado = st.data_editor(
        df_socios,
        hide_index=True,
        column_config={
            "Número": st.column_config.NumberColumn("Nº", disabled=True, format="%d"),
            "ID": st.column_config.TextColumn("ID ARO"),
            "Nome": st.column_config.TextColumn("Nome Completo"),
            "Telefone": st.column_config.TextColumn("Telefone/Contato"),
            "CPF": st.column_config.TextColumn("CPF"),
            "CTF": st.column_config.TextColumn("CTF IBAMA"),
            "Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo", "Pendente"])
        },
        disabled=False,
        use_container_width=True,
        key="editor_socios_master"
    )
    
    # Salva as alterações de volta no session_state e grava o arquivo de backup físico
    if not df_editado.equals(df_socios):
        st.session_state["dados_socios_internos"] = df_editado
        try:
            df_editado.to_csv("backup_socios.csv", index=False)
        except:
            pass
        st.rerun()

else:
    # A diretoria entra aqui: Consegue ler todas as informações dos sócios (incluindo CPF e CTF), mas sem poder alterar nada
    st.dataframe(
        df_socios,
        hide_index=True,
        column_config={
            "Número": "Nº",
            "ID": "ID ARO",
            "Nome": "Nome Completo",
            "Telefone": "Telefone/Contato",
            "CPF": "CPF",
            "CTF": "CTF IBAMA",
            "Status": "Status"
        },
        use_container_width=True
    )

