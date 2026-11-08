import streamlit as st
import pandas as pd
import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando)
st.set_page_config(
    page_title="Painel de Controle - ARO Rio do Sul",
    page_icon="🦅",
    layout="wide"
)

# 2. INICIALIZAÇÃO SEGURA DO ESTADO GLOBAL (session_state)
if "username" not in st.session_state:
    st.session_state["username"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)

# --- 3. CONTROLE DE NAVEGAÇÃO SEGURO (BLOCAGE DE PÁGINAS) ---
# Definir a página inicial de login
login_page = st.Page("app.py", title="🔑 Área de Acesso", icon="🔒")

# Definir as páginas protegidas que ficam na pasta /pages
pag_socios = st.Page("pages/1_Socios.py", title="👥 Cadastro de Sócios", icon="👥")
pag_financas = st.Page("pages/2_Financas.py", title="💰 Fluxo de Caixa", icon="💰")
pag_torneios = st.Page("pages/3_Torneios.py", title="🦅 Torneios Oficiais", icon="🦅")

# REGRA DE OURO: Se NÃO estiver logado, a única página existente no app é a tela de login
if st.session_state["username"] is None:
    pg = st.navigation([login_page], position="hidden") # Esconde a barra lateral completamente
    pg.run()
    
    # --- TELA DE LOGIN CENTRALIZADA ---
    st.markdown("<h2 style='text-align: center;'>🦅 Associação Regional dos Ornitofílios</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Sistema de Gestão Interna - ARO Rio do Sul</h4>", unsafe_allow_html=True)
    st.write("\n")
    
    _, col_login_box, _ = st.columns([1, 2, 1])
    
    with col_login_box:
        st.markdown("### 🔑 Identificação do Usuário")
        usuario_input = st.text_input("Nome de Usuário / Credencial:", placeholder="Ex: Junior Rebelo")
        
        if st.button("Entrar no Painel", use_container_width=True):
            if usuario_input.strip() == "Junior Rebelo":
                st.session_state["username"] = "Junior Rebelo"
                st.session_state["user_role"] = "master"
                st.success("Acesso Master concedido!")
                st.rerun()
            elif usuario_input.strip() != "":
                st.session_state["username"] = usuario_input.strip()
                st.session_state["user_role"] = "leitura"
                st.info(f"Acesso concedido como {usuario_input.strip()} (Modo Leitura).")
                st.rerun()
            else:
                st.error("Por favor, preencha o campo de usuário para entrar.")

# Se o usuário JÁ estiver logado, libera o menu lateral com todas as páginas reais
else:
    # Gerencia a barra de navegação ativa com as abas protegidas
    pg = st.navigation({
        "Menu Principal": [login_page],
        "Módulos Administrativos": [pag_socios, pag_financas, pag_torneios]
    })
    pg.run()
    
    # Conteúdo que aparece na tela inicial ('app.py') após o login efetuado
    st.sidebar.write("---")
    if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state["username"] = None
        st.session_state["user_role"] = None
        st.rerun()
        
    st.markdown(f"## 👋 Olá, {st.session_state['username']}!")
    st.write("Você está conectado ao sistema da ARO. Utilize a barra lateral que acabou de aparecer para navegar entre os módulos.")
    st.write("---")
    
    # Dashboard Informativo Simples de Boas-Vindas
    st.markdown("### 📅 Próximo Evento Cadastrado")
    st.metric(label="Data do Torneio Oficial ARO", value=st.session_state["data_torneio_aro"].strftime('%d/%m/%Y'))
    st.caption("Para alterar dados financeiros ou realizar inscrições de aves, selecione a página correspondente no menu lateral esquerdo.")
