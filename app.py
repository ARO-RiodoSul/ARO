import streamlit as st
import pandas as pd
import os, pickle

st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="logo.png" if os.path.exists("logo.png") else "📊", layout="wide")
st.markdown("""<head><title>ARO</title><link rel="apple-touch-icon" href="app/static/logo.png"><link rel="icon" type="image/png" href="app/static/logo.png"></head>""", unsafe_allow_html=True)

# CAMINHOS ABSOLUTOS SEGUROS CONTRA ERROS DE ESCRITA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_USUARIOS = os.path.join(BASE_DIR, "backup_usuarios.pkl")
PATH_SOCIOS = os.path.join(BASE_DIR, "backup_socios.csv")

if "banco_usuarios_dinamicos" not in st.session_state:
    if os.path.exists(PATH_USUARIOS):
        try:
            with open(PATH_USUARIOS, "rb") as f: st.session_state["banco_usuarios_dinamicos"] = pickle.load(f)
        except: st.session_state["banco_usuarios_dinamicos"] = {}
    else:
        st.session_state["banco_usuarios_dinamicos"] = {
            "Socio": {"senha": "aro123", "role": "socio", "socio_vinculado": "Nenhum"},
            "Visitante": {"senha": "aro999", "role": "visitante", "socio_vinculado": "Nenhum"}
        }

usuarios_cadastrados = st.session_state["banco_usuarios_dinamicos"]

if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "visitante"})

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        _, col_img, _ = st.columns(3)
        col_img.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    
    with st.form("t_login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == "Junior Rebelo" and s == "270688":
                st.session_state.update({"autenticado": True, "user_role": "master"})
                st.rerun()
            elif u in ["Kleven", "Valter", "Peterson", "Mauro"] and s == {"Kleven": "12345678", "Valter": "021277", "Peterson": "100693", "Mauro": "120660"}[u]:
                st.session_state.update({"autenticado": True, "user_role": "diretoria"})
                st.rerun()
            elif u == "Vanderlei" and s == "251073":
                st.session_state.update({"autenticado": True, "user_role": "diretoria"})
                st.rerun()
            elif u in usuarios_cadastrados and usuarios_cadastrados[u]["senha"] == s:
                st.session_state.update({"autenticado": True, "user_role": usuarios_cadastrados[u]["role"]})
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                
    st.write("<p style='text-align: center; color: gray; margin: 5px 0;'>Ou se você é apenas um visitante do evento:</p>", unsafe_allow_html=True)
    if st.button("🌐 Entrar como Convidado / Visitante", use_container_width=True):
        st.session_state.update({"autenticado": True, "user_role": "visitante"})
        st.rerun()
    st.stop()

# --- SE ESTIVER AUTENTICADO ---
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv(PATH_SOCIOS) if os.path.exists(PATH_SOCIOS) else pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])

df_socios_global = st.session_state["dados_socios_internos"]

c_l, c_t, c_o = st.columns(3)
try:
    if os.path.exists("logo.png"): c_l.image("logo.png", width=80)
except: pass

c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
if c_o.button("🔒 Sair do Painel", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

st.markdown("---")
role = st.session_state["user_role"]
if role == "master": st.info("⭐ Modo Administrador: Acesso Master Ativado")
elif role == "diretoria": st.info("🛡️ Modo Diretoria: Acesso Administrativo Parcial Ativado")
elif role == "socio": st.info("👥 Modo Sócio: Acesso de Consulta a Torneios Ativado")
else: st.info("ℹ️ Modo Visitante: Acesso Limitado Ativado")

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🦅 Bem-vindo ao Sistema Oficial ARO</h2>", unsafe_allow_html=True)

# --- CENTRAL DE CADASTRO E EXCLUSÃO DINÂMICA DE LOGINS (EXCLUSIVO MASTER) ---
if role == "master":
    st.write("---")
    st.markdown("### 🔑 Central de Gerenciamento de Acessos")
    col_cad_1, col_cad_2 = st.columns(2)
    
    with col_cad_1:
        with st.form("form_cadastrar_usuario", clear_on_submit=True):
            st.markdown("**Cadastrar / Atualizar Usuário**")
            novo_u = st.text_input("Nome de Usuário (Login):")
            novo_s = st.text_input("Senha de Acesso:", type="password")
            tipo_role = st.selectbox("Categoria/Nível:", ["Sócio", "Visitante"])
            
            socio_vinc = "Nenhum"
            if tipo_role == "Sócio":
                lista_nomes = ["Selecione o Sócio..."]
                if not df_socios_global.empty and "Nome" in df_socios_global.columns:
                    lista_nomes.extend(df_socios_global["Nome"].dropna().str.strip().tolist())
                socio_vinc = st.selectbox("Vincular Sócio Oficial:", [x for x in lista_nomes if x != ""])
                
            if st.form_submit_button("Salvar Usuário", use_container_width=True):
                if novo_u.strip() and novo_s.strip():
                    if novo_u.strip() in ["Junior Rebelo", "Kleven", "Valter", "Peterson", "Mauro", "Vanderlei"]:
                        st.error("Nome de usuário reservado para a administração fixa!")
                    elif tipo_role == "Sócio" and socio_vinc == "Selecione o Sócio...":
                        st.error("Selecione qual sócio oficial será vinculado a este login!")
                    else:
                        st.session_state["banco_usuarios_dinamicos"][novo_u.strip()] = {"senha": novo_s.strip(), "role": "socio" if tipo_role == "Sócio" else "visitante", "socio_vinculado": socio_vinc}
                        try:
                            with open(PATH_USUARIOS, "wb") as f: pickle.dump(st.session_state["banco_usuarios_dinamicos"], f)
                            st.success("Usuário salvo com sucesso!")
                            st.rerun()
                        except: st.error("Erro ao gravar arquivo físico de backup.")
                else: st.error("Preencha todos os campos do formulário!")
                    
    with col_cad_2:
        st.markdown("**Usuários Cadastrados Ativos**")
        if usuarios_cadastrados:
            lista_exibicao = [{"Usuário": k, "Senha": v["senha"], "Nível": str(v["role"]).upper(), "Vínculo": v.get("socio_vinculado", "Nenhum")} for k, v in usuarios_cadastrados.items()]
            st.dataframe(pd.DataFrame(lista_exibicao), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("🗑️ **Excluir Usuário**")
            u_para_deletar = st.selectbox("Conta para apagar:", list(usuarios_cadastrados.keys()))
            confirmar_del = st.checkbox("💥 Confirmo a exclusão permanente")
            
            if st.button("❌ Deletar Usuário Selecionado", use_container_width=True):
                if confirmar_del:
                    del st.session_state["banco_usuarios_dinamicos"][u_para_deletar]
                    try:
                        with open(PATH_USUARIOS, "wb") as f: pickle.dump(st.session_state["banco_usuarios_dinamicos"], f)
                        st.success("Usuário excluído!")
                        st.rerun()
                    except: st.error("Erro ao atualizar o backup.")
                else: st.error("Marque o quadrado de confirmação antes de deletar!")
        else:
            st.caption("Nenhum usuário dinâmico ativo no momento.")
