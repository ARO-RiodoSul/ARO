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

# Garantir o carregamento integrado e centralizado sincronizado com o app.py
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv("backup_socios.csv") if os.path.exists("backup_socios.csv") else pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])

df_socios = st.session_state["dados_socios_internos"]

# Garantir que a coluna 'Número' seja tratada como numérico para evitar erros na ordenação
if not df_socios.empty:
    df_socios["Número"] = pd.to_numeric(df_socios["Número"], errors='coerce').fillna(0).astype(int)

st.markdown("### 📊 Listagem de Sócios Cadastrados")

if is_master:
    st.caption("💡 Para cadastrar novos sócios a partir do 21, basta rolar até o final da tabela e clicar no botão **'➕ Add row'**. O número sequencial será gerado sozinho!")
    
    # AJUSTADO: num_rows="dynamic" ativo para liberar a criação ilimitada de novos membros
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
    
    # Se houver mudanças na tabela (novas linhas ou edições)
    if not df_editado.equals(df_socios):
        # Percorre as linhas para preencher automaticamente o número sequencial das novas linhas adicionadas
        ultimo_num = 0
        for idx, row in df_editado.iterrows():
            if pd.isna(row["Número"]) or row["Número"] == 0:
                ultimo_num += 1
                df_editado.at[idx, "Número"] = int(ultimo_num)
            else:
                ultimo_num = int(row["Número"])
        
        # Garante que os números permaneçam salvos como inteiros limpos
        df_editado["Número"] = df_editado["Número"].astype(int)
        
        # Salva o progresso na memória do app e sobrescreve o arquivo físico de backup
        st.session_state["dados_socios_internos"] = df_editado
        try:
            df_editado.to_csv("backup_socios.csv", index=False)
        except:
            pass
        st.rerun()

else:
    # Visualização estática para o perfil de Diretoria (Leitura sem alteração)
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
