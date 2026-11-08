import streamlit as st
import pandas as pd
import os, pickle

# CONFIGURAÇÃO DO APP E ÍCONE DO NAVEGADOR
st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="logo.png" if os.path.exists("logo.png") else "📊", layout="wide")

# TRAVA PARA FORÇAR A LOGO E NOME NO CELULAR
st.markdown("""<head><title>ARO</title><link rel="apple-touch-icon" href="app/static/logo.png"><link rel="icon" type="image/png" href="app/static/logo.png"></head>""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN SEGURO COM NOVOS NÍVEIS DE USUÁRIO ---
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "visitante", "tela_atual": "menu"})

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        _, col_img, _ = st.columns(3)
        col_img.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #6B7280;'>ARO - Rio do Sul</h3>", unsafe_allow_html=True)
    
    with st.form("t_login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == "Junior Rebelo" and s == "270688":
                st.session_state.update({"autenticado": True, "user_role": "master"})
                st.rerun()
            elif u == "Diretoria" and s == "aro2026":
                st.session_state.update({"autenticado": True, "user_role": "diretoria"})
                st.rerun()
            elif u == "Socio" and s == "aro123":
                st.session_state.update({"autenticado": True, "user_role": "socio"})
                st.rerun()
            elif u == "Visitante" and s == "aro999":
                st.session_state.update({"autenticado": True, "user_role": "visitante"})
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# --- SE ESTIVER AUTENTICADO ---
lista_meses = ["Dezembro 2026"] + [f"{m} {a}" for a in ["2027", "2028"] for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]]

# CARREGAMENTO CENTRALIZADO DE BANCOS DE DADOS
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv("backup_socios.csv") if os.path.exists("backup_socios.csv") else pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])

if "saldo_anterior_master" not in st.session_state:
    if os.path.exists("backup_saldo_ant.txt"):
        with open("backup_saldo_ant.txt", "r") as f: st.session_state["saldo_anterior_master"] = float(f.read())
    else: st.session_state["saldo_anterior_master"] = 0.0

if "dados_meses_financeiros" not in st.session_state:
    st.session_state["dados_meses_financeiros"] = pickle.load(open("backup_financas.pkl", "rb")) if os.path.exists("backup_financas.pkl") else {m: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m in lista_meses}

if "dados_torneios_internos" not in st.session_state:
    st.session_state["dados_torneios_internos"] = pickle.load(open("backup_torneios_v2.pkl", "rb")) if os.path.exists("backup_torneios_v2.pkl") else pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])

if "data_torneio_aro" not in st.session_state:
    try: st.session_state["data_torneio_aro"] = open("backup_data_torneio.txt", "r").read() if os.path.exists("backup_data_torneio.txt") else "08/11/2026"
    except: st.session_state["data_torneio_aro"] = "08/11/2026"

# --- TELA: MENU PRINCIPAL ---
c_l, c_t, c_o = st.columns(3)
try:
    if os.path.exists("logo.png"): c_l.image("logo.png", width=80)
except: pass

c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
if c_o.button("🔒 Sair do Painel"):
    st.session_state["autenticado"] = False
    st.rerun()

st.markdown("---")

role = st.session_state["user_role"]
if role == "master": st.info("⭐ Modo Administrador: Acesso Master Ativado")
elif role == "diretoria": st.info("🛡️ Modo Diretoria: Acesso Administrativo Parcial Ativado")
elif role == "socio": st.info("👥 Modo Sócio: Acesso de Consulta a Torneios Ativado")
else: st.info("ℹ️ Modo Visitante: Acesso Limitado Ativado")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🦅 Bem-vindo ao Sistema Oficial ARO</h2>", unsafe_allow_html=True)

if role in ["master", "diretoria"]:
    st.markdown("<p style='text-align: center; color: #6B7280;'>Utilize o menu lateral à esquerda do seu navegador ou celular para navegar entre as planilhas de Sócios, Finanças e Torneios de forma independente.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align: center; color: #6B7280;'>Utilize o menu lateral à esquerda para visualizar a página de **Torneios**. As abas de Sócios e Finanças são restritas à administração.</p>", unsafe_allow_html=True)
