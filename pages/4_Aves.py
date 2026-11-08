import streamlit as st
import pandas as pd
import os, pickle

st.set_page_config(page_title="Minhas Aves - Painel ARO", page_icon="🦅", layout="wide")

if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

st.title("🦅 Plantel de Aves Compartilhado - ARO")
role_atual = st.session_state.get("user_role")
usuario_logado = st.session_state.get("username")

PATH_AVES = os.path.abspath("backup_aves.pkl")

usuarios_dinamicos = st.session_state.get("banco_usuarios_dinamicos", {})
socio_vinculado = "Administração" if role_atual in ["master", "diretoria"] else usuarios_dinamicos.get(usuario_logado, {}).get("socio_vinculado", usuario_logado)

if "dados_aves_sistema" not in st.session_state:
    df_inicial = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha"])
    if os.path.exists(PATH_AVES):
        try:
            with open(PATH_AVES, "rb") as f: df_inicial = pickle.load(f)
        except: pass
    st.session_state["dados_aves_sistema"] = df_inicial

df_aves = st.session_state["dados_aves_sistema"]

with st.form("form_cadastro_ave", clear_on_submit=True):
    st.markdown("### 📝 Cadastrar Nova Ave")
    col1, col2, col3 = st.columns(3)
    nome_passaro = col1.text_input("Nome do Pássaro:")
    especie_selecionada = col2.selectbox("Espécie:", ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"])
    anilha_passaro = col3.text_input("Número da Anilha:")
    
    proprietario_final = socio_vinculado
    if role_atual in ["master", "diretoria"]:
        df_socios = st.session_state.get("dados_socios_internos", pd.DataFrame())
        lista_proprietarios = [usuario_logado]
        if not df_socios.empty and "Nome" in df_socios.columns: lista_proprietarios.extend(df_socios["Nome"].dropna().tolist())
        proprietario_final = st.selectbox("Proprietário?", [x for x in lista_proprietarios if x != ""])

    if st.form_submit_button("Salvar Ave no Plantel", use_container_width=True):
        if nome_passaro.strip() and anilha_passaro.strip():
            nova_ave = pd.DataFrame([{"Proprietário": proprietario_final, "Nome da Ave": nome_passaro.strip(), "Espécie": especie_selecionada, "Anilha": anilha_passaro.strip()}])
            st.session_state["dados_aves_sistema"] = pd.concat([df_aves, nova_ave], ignore_index=True)
            with open(PATH_AVES, "wb") as f:
                pickle.dump(st.session_state["dados_aves_sistema"], f)
            st.success("Ave cadastrada com sucesso!"); st.rerun()

st.write("---")
st.markdown("### 🏆 Aves Registradas no Sistema")

if role_atual in ["master", "diretoria"]:
    st.dataframe(df_aves, hide_index=True, use_container_width=True)
else:
    df_f = df_aves[df_aves["Proprietário"] == socio_vinculado] if not df_aves.empty else pd.DataFrame()
    st.dataframe(df_f, hide_index=True, use_container_width=True)
