import streamlit as st
import pandas as pd
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Acesso - Criatório 047", page_icon="🔒", layout="centered")

# --- SISTEMA DE LOGIN DE SEGURANÇA ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# SE O USUÁRIO NÃO ESTIVER LOGADO, MOSTRA A TELA DE LOGIN (CAPA)
if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # EXIBIÇÃO DA LOGO NO TOPO DA TELA
    if os.path.exists("logo.png"):
        col_logo_esq, col_logo_meio, col_logo_dir = st.columns([1, 2, 1])
        col_logo_meio.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🦅 CRIATÓRIO 047</h1>", unsafe_allow_html=True)
        
    st.markdown("<h3 style='text-align: center; color: #6B7280; font-family: sans-serif;'>ARO - Rio do Sul</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9CA3AF;'>Insira suas credenciais abaixo para acessar o sistema.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # FORMULÁRIO DE ACESSO (ABAIXO DA LOGO)
    with st.form("tela_login"):
        usuario = st.text_input("Usuário Admin", placeholder="Digite seu usuário...")
        senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...")
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        
        if botao_entrar:
            # NOVAS CREDENCIAIS CONFIGURADAS
            if usuario == "Junior Rebelo" and senha == "270688":
                st.session_state["autenticado"] = True
                st.success("Acesso autorizado! Carregando...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")
                
    st.stop()

# ==============================================================================
# SE PASSAR DO LOGIN, O APLICATIVO PRINCIPAL ABRE AQUI EMBAIXO
# ==============================================================================

# CONEXÃO DIRETA COM O GOOGLE SHEETS
try:
    url_base = st.secrets["connections"]["gsheets"]["spreadsheet"]
    if "edit?" in url_base:
        link_limpo = url_base.split("/edit")[0]
        url_socios = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Socios"
        url_financeiro = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Financeiro"
    else:
        url_socios = url_base
        url_financeiro = url_base

    df_socios = pd.read_csv(url_socios)
    df_financeiro = pd.read_csv(url_financeiro)
except Exception as e:
    st.error("Erro ao conectar à planilha. Verifique as configurações avançadas.")
    st.stop()

# BARRA SUPERIOR DO PAINEL INTERNO
col_titulo, col_logout = st.columns([3, 1])
col_titulo.title("🦅 Painel Criatório 047")
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

# Painel de Indicadores Visuais
col1, col2, col3 = st.columns(3)
col1.metric(label="🟢 Total de Entradas", value=f"R$ {entradas:,.2f}")
col2.metric(label="🔴 Total de Saídas", value=f"R$ {saidas:,.2f}")
col3.metric(label="💰 Saldo Atual em Caixa", value=f"R$ {saldo_atual:,.2f}")

st.markdown("---")

# ABAS INTERNAS
aba_socios, aba_financeiro = st.tabs(["👥 Controle de Sócios", "💸 Fluxo de Caixa"])

with aba_socios:
    st.subheader("Lista de Sócios Cadastrados")
    st.dataframe(df_socios, use_container_width=True)

with aba_financeiro:
    st.subheader("Histórico do Extrato Financeiro")
    st.dataframe(df_financeiro, use_container_width=True)
