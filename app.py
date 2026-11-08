import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="logo.png" if os.path.exists("logo.png") else "📊", layout="wide")
st.markdown("""<head><title>ARO</title><link rel="apple-touch-icon" href="app/static/logo.png"><link rel="icon" type="image/png" href="app/static/logo.png"></head>""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
PATH_SOCIOS = os.path.join(BASE_DIR, "backup_socios.csv")

if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "visitante", "username": ""})

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists(LOGO_PATH):
        _, col_img, _ = st.columns(3)
        col_img.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #6B7280;'>ARO - Rio do Sul</h3>", unsafe_allow_html=True)
    
    with st.form("t_login"):
        u_input = st.text_input("Usuário").strip()
        s_input = st.text_input("Senha", type="password").strip()
        
        if st.form_submit_button("Entrar"):
            u_f = u_input.lower()
            
            # 1. PERMISSÃO MASTER (JUNIOR REBELO)
            if u_input == "Junior Rebelo" and s_input == "270688":
                st.session_state.update({"autenticado": True, "user_role": "master", "username": "Junior Rebelo"})
                st.rerun()
                
            # 2. USUÁRIOS FIXOS DA DIRETORIA
            elif u_f in ["kleven", "valter", "peterson", "mauro"] and s_input == {"kleven": "12345678", "valter": "021277", "peterson": "100693", "mauro": "120660"}[u_f]:
                st.session_state.update({"autenticado": True, "user_role": "diretoria", "username": u_f.capitalize()})
                st.rerun()
            elif u_f == "vanderlei" and s_input == "251073":
                st.session_state.update({"autenticado": True, "user_role": "diretoria", "username": "Vanderlei"})
                st.rerun()
                
            # 3. NOVOS USUÁRIOS FIXOS DE SÓCIOS (Gravados direto no código)
            elif u_f == "carolina" and s_input == "230197":
                st.session_state.update({"autenticado": True, "user_role": "socio", "username": "Carolina"})
                st.rerun()
            elif u_f == "pedro" and s_input == "1988":
                st.session_state.update({"autenticado": True, "user_role": "socio", "username": "Pedro"})
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                
    st.write("<p style='text-align: center; color: gray; margin: 5px 0;'>Ou se você é apenas um visitante do evento:</p>", unsafe_allow_html=True)
    if st.button("🌐 Entrar como Convidado / Visitante", use_container_width=True):
        st.session_state.update({"autenticado": True, "user_role": "visitante", "username": "Visitante Convidado"})
        st.rerun()
    st.stop()

# --- SE ESTIVER AUTENTICADO ---
if "dados_socios_internos" not in st.session_state:
    if os.path.exists(PATH_SOCIOS):
        try: st.session_state["dados_socios_internos"] = pd.read_csv(PATH_SOCIOS)
        except: st.session_state["dados_socios_internos"] = pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])
    else:
        st.session_state["dados_socios_internos"] = pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])

c_l, c_t, c_o = st.columns(3)
try:
    if os.path.exists(LOGO_PATH): c_l.image(LOGO_PATH, width=80)
except: pass

c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
if c_o.button("🔒 Sair do Painel", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

st.markdown("---")
role = st.session_state["user_role"]
st.markdown(f"<h2 style='text-align: center; color: #1E3A8A;'>🦅 Bem-vindo, {st.session_state['username']}!</h2>", unsafe_allow_html=True)

if role in ["master", "diretoria"]:
    st.markdown("<p style='text-align: center; color: #6B7280;'>Utilize o menu lateral à esquerda para navegar entre as planilhas de Sócios, Finanças e Torneios.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align: center; color: #6B7280;'>Utilize o menu lateral à esquerda para gerenciar seu plantel de aves e solicitar inscrições em torneios oficiais.</p>", unsafe_allow_html=True)
