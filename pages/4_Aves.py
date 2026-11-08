import streamlit as st
import pandas as pd
import os, pickle

st.set_page_config(page_title="Minhas Aves - Painel ARO", page_icon="🦅", layout="wide")

if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

st.title("🦅 Plantel de Aves Compartilhado - ARO")
role_atual = str(st.session_state.get("user_role", "")).strip().lower()
usuario_logado = str(st.session_state.get("username", "")).strip().lower()

PATH_AVES = "backup_aves.pkl"
usuarios_dinamicos = st.session_state.get("banco_usuarios_dinamicos", {})

is_master_strict = role_atual == "master" or usuario_logado == "master"
is_diretoria = role_atual in ["diretoria", "admin"] or usuario_logado in ["admin"]

socio_vinculado = usuarios_dinamicos.get(st.session_state.get("username"), {}).get("socio_vinculado", st.session_state.get("username"))

# FIX: Força a leitura direta do arquivo físico do disco a cada atualização de tela
df_inicial = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha"])
if os.path.exists(PATH_AVES):
    try:
        with open(PATH_AVES, "rb") as f: 
            df_inicial = pickle.load(f)
    except: 
        pass
st.session_state["dados_aves_sistema"] = df_inicial
df_aves = st.session_state["dados_aves_sistema"]

with st.form("form_cadastro_ave", clear_on_submit=True):
    st.markdown("### 📝 Cadastrar Nova Ave")
    col1, col2, col3 = st.columns(3)
    nome_passaro = col1.text_input("Nome do Pássaro:")
    especie_selecionada = col2.selectbox("Espécie:", ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"])
    anilha_passaro = col3.text_input("Número da Anilha:")
    
    proprietario_final = socio_vinculado
    if is_master_strict or is_diretoria:
        df_socios = st.session_state.get("dados_socios_internos", pd.DataFrame())
        lista_proprietarios = [st.session_state.get("username")]
        if not df_socios.empty and "Nome" in df_socios.columns: 
            lista_proprietarios.extend(df_socios["Nome"].dropna().tolist())
        proprietario_final = st.selectbox("Proprietário da Ave:", [x for x in lista_proprietarios if x != ""], index=0)

    if st.form_submit_button("Salvar Ave no Plantel", use_container_width=True):
        if nome_passaro.strip() and anilha_passaro.strip():
            nova_ave = pd.DataFrame([{"Proprietário": proprietario_final, "Nome da Ave": nome_passaro.strip(), "Espécie": especie_selecionada, "Anilha": anilha_passaro.strip()}])
            st.session_state["dados_aves_sistema"] = pd.concat([df_aves, nova_ave], ignore_index=True)
            with open(PATH_AVES, "wb") as f:
                pickle.dump(st.session_state["dados_aves_sistema"], f)
            st.success("Ave cadastrada com sucesso!"); st.rerun()

st.write("---")
st.markdown("### 🏆 Aves Registradas no Sistema")

if is_master_strict:
    st.dataframe(df_aves, hide_index=True, use_container_width=True)
else:
    df_f = df_aves[df_aves["Proprietário"] == socio_vinculado] if not df_aves.empty else pd.DataFrame()
    st.dataframe(df_f, hide_index=True, use_container_width=True)

if is_master_strict:
    st.write("---")
    st.markdown("### 💾 Central de Segurança do Plantel (Exclusivo Master)")
    cb_exp, cb_imp = st.columns(2)
    
    with cb_exp:
        st.markdown("**Exportar Aves**")
        st.download_button(
            label="📥 Exportar Todas as Aves (.PKL)", 
            data=pickle.dumps(df_aves), 
            file_name="backup_geral_aves_aro.pkl", 
            mime="application/octet-stream", 
            use_container_width=True
        )
        
    with cb_imp:
        st.markdown("**Importar Aves**")
        arq_sub_aves = st.file_uploader("Subir arquivo de backup de aves:", type=["pkl"], key="up_aves_master")
        if arq_sub_aves:
            try:
                aves_carregadas = pickle.load(arq_sub_aves)
                if st.button("🔄 Confirmar Restauração do Plantel Geral", use_container_width=True, type="primary"):
                    st.session_state["dados_aves_sistema"] = aves_carregadas
                    with open(PATH_AVES, "wb") as f:
                        pickle.dump(aves_carregadas, f)
                    st.success("Plantel geral restaurado com sucesso!"); st.rerun()
            except: 
                st.error("Arquivo inválido ou corrompido.")

