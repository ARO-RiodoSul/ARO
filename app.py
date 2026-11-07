import streamlit as st
import pandas as pd

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão Associação", page_icon="📊", layout="wide")

st.title("🦅 Sistema de Gestão - Associação")
st.markdown("---")

# CONEXÃO DIRETA E NATIVA COM O GOOGLE SHEETS (Via link CSV público)
try:
    # Link da planilha vindo dos Secrets
    url_base = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # Transforma o link normal da planilha em um link de download de dados nativo
    if "edit#" in url_base:
        url_socios = url_base.split("edit#")[0] + "gviz/tq?tqx=out:csv&sheet=Socios"
        url_financeiro = url_base.split("edit#")[0] + "gviz/tq?tqx=out:csv&sheet=Financeiro"
    else:
        url_socios = url_base
        url_financeiro = url_base

    # Lê os dados de forma nativa (Sem precisar de nenhuma biblioteca extra!)
    df_socios = pd.read_csv(url_socios)
    df_financeiro = pd.read_csv(url_financeiro)
except Exception as e:
    st.error("Por favor, verifique as Configurações Avançadas (Secrets) no Streamlit.")
    st.stop()

# CÁLCULO DE SALDO EM TEMPO REAL
if not df_financeiro.empty and "Tipo" in df_financeiro.columns and "Valor" in df_financeiro.columns:
    entradas = pd.to_numeric(df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'], errors='coerce').sum()
    saidas = pd.to_numeric(df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'], errors='coerce').sum()
    saldo_atual = entradas - saidas
else:
    entradas, saidas, saldo_atual = 0.0, 0.0, 0.0

# Painel de Indicadores Visuais
col1, col2, col3 = st.columns(3)
col1.metric(label="🟢 Total de Entradas", value=f"R$ {entradas:,.2f}")
col2.metric(label="🔴 Total de Saídas", value=f"R$ {saidas:,.2f}")
col3.metric(label="💰 Saldo Atual em Caixa", value=f"R$ {saldo_atual:,.2f}")

st.markdown("---")

# ABAS DE NAVEGAÇÃO
aba_socios, aba_financeiro = st.tabs(["👥 Controle de Sócios", "💸 Fluxo de Caixa"])

with aba_socios:
    st.subheader("Lista de Sócios Cadastrados")
    st.dataframe(df_socios, use_container_width=True)

with aba_financeiro:
    st.subheader("Histórico do Extrato Financeiro")
    st.dataframe(df_financeiro, use_container_width=True)

