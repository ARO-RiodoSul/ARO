import streamlit as st
import pandas as pd
import os

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Sócios - Painel ARO", page_icon="👥", layout="wide")

# --- TRAVA DE SEGURANÇA POR CATEGORIA DE USUÁRIO ---
if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

# Título do Módulo
st.title("👥 Cadastro de Sócios - ARO Rio do Sul")

is_master = st.session_state.get("user_role") == "master"

# CARREGAMENTO INTEGRADO E SEGURO CORRIGIDO CONTRA TABELAS VAZIAS
if "dados_socios_internos" not in st.session_state:
    if os.path.exists("./backup_socios.csv"):
        try:
            df_carregado = pd.read_csv("./backup_socios.csv")
            # Se o arquivo existir mas estiver vazio (só cabeçalho), monta as 20 linhas padrão
            if df_carregado.empty:
                df_carregado = pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])
        except:
            df_carregado = pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])
    else:
        df_carregado = pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])
    
    st.session_state["dados_socios_internos"] = df_carregado

df_socios = st.session_state["dados_socios_internos"]

# Garantir conversão numérica limpa do sequencial
if not df_socios.empty:
    df_socios["Número"] = pd.to_numeric(df_socios["Número"], errors='coerce').fillna(0).astype(int)

st.markdown("### 📊 Listagem de Sócios Cadastrados")

if is_master:
    # AJUSTADO: Mensagem antiga em st.caption removida daqui de forma definitiva
    
    df_editado = st.data_editor(
        df_socios,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Número": st.column_config.NumberColumn("Nº", disabled=True, format="%d"),
            "ID": st.column_config.TextColumn("ID ARO"),
            "Nome": st.column_config.TextColumn("Nome Completo"),
            "Telefone": st.column_config.TextColumn("Telefone/Contato"),
            "CPF": st.column_config.TextColumn("CPF"),
            "CTF": st.column_config.TextColumn("CTF IBAMA"),
            "Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo", "Pendente"], default="Ativo")
        },
        disabled=False,
        use_container_width=True,
        key="editor_socios_master"
    )
    
    if not df_editado.equals(df_socios):
        # Recalcula e preenche o número sequencial caso novas linhas sejam inseridas via celular ou PC
        ultimo_num = 0
        for idx, row in df_editado.iterrows():
            try:
                val_num = int(float(row["Número"]))
            except:
                val_num = 0
                
            if val_num == 0:
                ultimo_num += 1
                df_editado.at[idx, "Número"] = int(ultimo_num)
            else:
                ultimo_num = val_num
        
        df_editado["Número"] = df_editado["Número"].astype(int)
        st.session_state["dados_socios_internos"] = df_editado
        try:
            df_editado.to_csv("./backup_socios.csv", index=False)
        except:
            pass
        st.rerun()

else:
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
