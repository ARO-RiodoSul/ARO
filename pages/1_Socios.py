import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Sócios - Painel ARO", page_icon="👥", layout="wide")

if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

st.title("👥 Cadastro de Sócios - ARO Rio do Sul")
is_master = st.session_state.get("user_role") == "master"

# ROTA TEMPORÁRIA LIBERADA DE ESCRITA
PATH_SOCIOS = "/tmp/backup_socios.csv"

if "dados_socios_internos" not in st.session_state:
    if os.path.exists(PATH_SOCIOS):
        df_carregado = pd.read_csv(PATH_SOCIOS)
    elif os.path.exists("backup_socios.csv"):
        df_carregado = pd.read_csv("backup_socios.csv")
    else:
        df_carregado = pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])
    st.session_state["dados_socios_internos"] = df_carregado

df_socios = st.session_state["dados_socios_internos"]

if not df_socios.empty:
    df_socios["Número"] = pd.to_numeric(df_socios["Número"], errors='coerce').fillna(1).astype(int)

if is_master:
    st.markdown("### 📝 Registrar Novo Membro")
    with st.form("form_novo_socio", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f4, col_f5, col_f6 = st.columns(3)
        with col_f1: id_aro = st.text_input("ID ARO:")
        with col_f2: nome_socio = st.text_input("Nome Completo:")
        with col_f3: tel_socio = st.text_input("Telefone / Contato:")
        with col_f4: cpf_socio = st.text_input("CPF:")
        with col_f5: ctf_socio = st.text_input("CTF IBAMA:")
        with col_f6: status_socio = st.selectbox("Status Inicial:", ["Ativo", "Inativo", "Pendente"])
        
        if st.form_submit_button("➕ Cadastrar Novo Sócio", use_container_width=True):
            if nome_socio.strip():
                proximo_no = int(df_socios["Número"].max() + 1) if not df_socios.empty else 1
                novo_registro = pd.DataFrame([{
                    "Número": int(proximo_no), "ID": id_aro.strip(), "Nome": nome_socio.strip(),
                    "Telefone": tel_socio.strip(), "CPF": cpf_socio.strip(), "CTF": ctf_socio.strip(), "Status": status_socio
                }])
                st.session_state["dados_socios_internos"] = pd.concat([df_socios, novo_registro], ignore_index=True)
                try:
                    st.session_state["dados_socios_internos"].to_csv(PATH_SOCIOS, index=False)
                    st.success(f"Sócio cadastrado com o Nº {proximo_no}!")
                    st.rerun()
                except: st.error("Erro ao gravar arquivo físico de backup.")
            else: st.error("Preencha o campo 'Nome Completo'!")

st.write("---")
st.markdown("### 📊 Listagem de Sócios Cadastrados")

if df_socios.empty:
    st.info("Nenhum sócio registrado no sistema.")
else:
    st.dataframe(
        df_socios.sort_values(by="Número"),
        hide_index=True,
        column_config={
            "Número": st.column_config.NumberColumn("Nº", format="%d"),
            "ID": "ID ARO", "Nome": "Nome Completo", "Telefone": "Telefone/Contato",
            "CPF": "CPF", "CTF": "CTF IBAMA", "Status": "Status"
        },
        use_container_width=True
    )

if is_master and not df_socios.empty:
    st.write("---")
    st.markdown("### 🗑️ Remover Membro do Sistema")
    lista_opcoes_del = [f"Nº {r['Número']} - {r['Nome']}" for _, r in df_socios.iterrows()]
    socio_para_deletar = st.selectbox("Selecione o sócio para apagar:", lista_opcoes_del)
    confirmar_del_socio = st.checkbox("💥 Confirmo a exclusão permanente")
    
    if st.button("❌ Deletar Sócio Selecionado", use_container_width=True):
        if confirmar_del_socio:
            posicao = lista_opcoes_del.index(socio_para_deletar)
            st.session_state["dados_socios_internos"] = df_socios.drop(df_socios.index[posicao]).reset_index(drop=True)
            if not st.session_state["dados_socios_internos"].empty:
                st.session_state["dados_socios_internos"]["Número"] = list(range(1, len(st.session_state["dados_socios_internos"]) + 1))
            try:
                st.session_state["dados_socios_internos"].to_csv(PATH_SOCIOS, index=False)
                st.success("Membro excluído!")
                st.rerun()
            except: st.error("Erro ao atualizar arquivo físico.")
        else: st.error("Marque a confirmação antes de deletar!")
