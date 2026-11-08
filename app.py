import streamlit as st
import pandas as pd
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="📊", layout="wide")

# --- SISTEMA DE LOGIN DE SEGURANÇA ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# SE O USUÁRIO NÃO ESTIVER LOGADO, MOSTRA A TELA DE LOGIN (CAPA)
if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # EXIBIÇÃO DA LOGO NO TOPO DE LOGIN (CORRIGIDO PARA REQUERER 3 COLUNAS)
    if os.path.exists("logo.png"):
        col_logo_esq, col_logo_meio, col_logo_dir = st.columns(3)
        col_logo_meio.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
        
    st.markdown("<h3 style='text-align: center; color: #6B7280; font-family: sans-serif;'>ARO - Rio do Sul</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9CA3AF;'>Insira suas credenciais abaixo para acessar o sistema.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.form("tela_login"):
        usuario = st.text_input("Usuário Admin", placeholder="Digite seu usuário...")
        senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...")
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        
        if botao_entrar:
            if usuario == "Junior Rebelo" and senha == "270688":
                st.session_state["autenticado"] = True
                st.success("Acesso autorizado! Carregando...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")
                
    st.stop()

# ==============================================================================
# SE PASSAR DO LOGIN - PAINEL INTERNO ARO RIO DO SUL
# ==============================================================================

# Gerenciamento de navegação interna por botões
if "tela_atual" not in st.session_state:
    st.session_state["tela_atual"] = "menu"

# CONEXÃO DIRETA COM O GOOGLE SHEETS
try:
    url_base = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # CORREÇÃO: Captura estritamente o primeiro item do texto cortado [0]
    if "/edit" in url_base:
        link_limpo = url_base.split("/edit")[0]
    else:
        link_limpo = url_base
        
    url_socios = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Socios"
    url_financeiro = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Financeiro"

    df_socios = pd.read_csv(url_socios)
    df_financeiro = pd.read_csv(url_financeiro)
except Exception as e:
    st.error(f"Erro ao conectar à planilha. Verifique se o link está público e correto nos Secrets. Detalhe: {e}")
    st.stop()

# --- TELA 1: MENU PRINCIPAL ---
if st.session_state["tela_atual"] == "menu":
    
    # Barra superior com o novo título e logo alinhados (CORRIGIDO PARA REQUERER 3 COLUNAS)
    col_logo, col_titulo, col_logout = st.columns(3)
    
    if os.path.exists("logo.png"):
        col_logo.image("logo.png", width=80)
    
    col_titulo.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    
    if col_logout.button("🔒 Sair do App"):
        st.session_state["autenticado"] = False
        st.rerun()
        
    st.markdown("---")
    
    # CÁLCULO DE SALDO EM TEMPO REAL
    entradas, saidas, saldo_atual = 0.0, 0.0, 0.0
    if not df_financeiro.empty:
        df_financeiro.columns = [c.strip().title() for c in df_financeiro.columns]
        if "Tipo" in df_financeiro.columns and "Valor" in df_financeiro.columns:
            df_financeiro["Valor"] = pd.to_numeric(df_financeiro["Valor"], errors='coerce').fillna(0)
            entradas = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
            saidas = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
            saldo_atual = entradas - saidas

    # Painel de Indicadores Rápidos no Menu
    col1, col2, col3 = st.columns(3)
    col1.metric(label="🟢 Total de Entradas", value=f"R$ {entradas:,.2f}")
    col2.metric(label="🔴 Total de Saídas", value=f"R$ {saidas:,.2f}")
    col3.metric(label="💰 Saldo Atual em Caixa", value=f"R$ {saldo_atual:,.2f}")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Selecione o módulo de gerenciamento:</h3>", unsafe_allow_html=True)
    
    # BOTÕES LADO A LADO COM ÍCONES (CORRIGIDO PARA REQUERER 2 COLUNAS)
    col_btn_socios, col_btn_caixa = st.columns(2)
    
    with col_btn_socios:
        st.markdown("<h1 style='text-align: center; margin: 0;'>👥</h1>", unsafe_allow_html=True)
        if st.button("Controle de Sócios", use_container_width=True, type="primary"):
            st.session_state["tela_atual"] = "socios"
            st.rerun()
            
    with col_btn_caixa:
        st.markdown("<h1 style='text-align: center; margin: 0;'>💸</h1>", unsafe_allow_html=True)
        if st.button("Fluxo de Caixa", use_container_width=True, type="primary"):
            st.session_state["tela_atual"] = "caixa"
            st.rerun()

# --- TELA 2: CONTROLE DE SÓCIOS ---
elif st.session_state["tela_atual"] == "socios":
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("👥 Controle de Sócios")
    st.markdown("---")
    st.dataframe(df_socios, use_container_width=True)

# --- TELA 3: FLUXO DE CAIXA ---
elif st.session_state["tela_atual"] == "caixa":
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("💸 Fluxo de Caixa")
    st.markdown("---")
    st.dataframe(df_financeiro, use_container_width=True)
