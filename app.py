import streamlit as st
import pandas as pd

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão Associação", page_icon="📊", layout="wide")

st.title("🦅 Sistema de Gestão - Associação")
st.markdown("---")

# CONEXÃO DIRETA COM O GOOGLE SHEETS (Substituindo o split problemático)
try:
    url_base = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # Limpa o link de forma segura para o formato de exportação de dados
    link_base = url_base.split("/edit")[0]
    url_socios = f"{link_base}/gviz/tq?tqx=out:csv&sheet=Socios"
    url_financeiro = f"{link_base}/gviz/tq?tqx=out:csv&sheet=Financeiro"

    # Leitura rápida dos dados da planilha
    df_socios = pd.read_csv(url_socios)
    df_financeiro = pd.read_csv(url_financeiro)
except Exception as e:
    st.error("Por favor, verifique se o link da planilha está correto nas configurações avançadas.")
    st.stop()

# CÁLCULO DE SALDO EM TEMPO REAL
entradas, saidas, saldo_atual = 0.0, 0.0, 0.0

if not df_financeiro.empty:
    # Garante que as colunas existem antes de somar
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

# ABAS DE NAVEGAÇÃO
aba_socios, aba_financeiro = st.tabs(["👥 Controle de Sócios", "💸 Fluxo de Caixa"])

with aba_socios:
    st.subheader("Lista de Sócios Cadastrados")
    st.dataframe(df_socios, use_container_width=True)

with aba_financeiro:
    st.subheader("Histórico do Extrato Financeiro")
    st.dataframe(df_financeiro, use_container_width=True)
