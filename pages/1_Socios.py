import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Sócios - ARO Rio do Sul", page_icon="👥", layout="wide")

if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
    st.warning("🔒 Por favor, faça o login na tela inicial (app.py) para acessar este módulo.")
    st.stop()

if st.button("⬅️ Voltar para a Capa Central"):
    st.switch_page("app.py")

st.title("👥 Controle de Sócios")
st.markdown("---")

if "dados_socios_internos" not in st.session_state:
    if os.path.exists("backup_socios.csv"):
        st.session_state["dados_socios_internos"] = pd.read_csv("backup_socios.csv")
    else:
        st.session_state["dados_socios_internos"] = pd.DataFrame([
            {"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)
        ])

if st.session_state["user_role"] == "master":
    st.success("📝 Modo Master Ativo: Edite os dados diretamente na tabela abaixo.")
    
    df_m = st.data_editor(
        st.session_state["dados_socios_internos"], 
        use_container_width=True, 
        disabled=["Número"], 
        column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo"])}, 
        hide_index=True
    )
    
    if not df_m.equals(st.session_state["dados_socios_internos"]): 
        st.session_state["dados_socios_internos"] = df_m
        df_m.to_csv("backup_socios.csv", index=False)
        st.toast("💾 Alterações nos Sócios salvas automaticamente!")
        st.rerun()
        
    if st.button("➕ Adicionar Linha para Novo Sócio"):
        p_n = len(st.session_state["dados_socios_internos"]) + 1
        n_l = pd.DataFrame([{"Número": p_n, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"}])
        st.session_state["dados_socios_internos"] = pd.concat([st.session_state["dados_socios_internos"], n_l], ignore_index=True)
        st.session_state["dados_socios_internos"].to_csv("backup_socios.csv", index=False)
        st.rerun()
else:
    st.info("ℹ️ Modo de Leitura: Você pode visualizar a listagem oficial abaixo.")
    st.dataframe(st.session_state["dados_socios_internos"], use_container_width=True, hide_index=True)
