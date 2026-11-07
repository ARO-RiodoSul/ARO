import streamlit as st
import pandas as pd

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão Associação", page_icon="📊", layout="wide")

st.title("🦅 Sistema de Gestão - Associação")
st.markdown("---")

# CONEXÃO DIRETA COM O GOOGLE SHEETS
try:
    url_base = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # Divide o link antes do '/edit' para garantir o endereço limpo da planilha
    link_limpo = url_base.split("/edit")[0]
    
    # Cria os links nativos específicos e separados para cada aba
    url_socios = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Socios"
    url_financeiro = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Financeiro"

    # Leitura isolada de cada tabela
    df_socios = pd.read_csv(url_socios)
    df_financeiro = pd.read_csv(url_financeiro)
except Exception as e:
    st.error("Por favor, verifique se o link da planilha está correto nas configurações avançadas.")
    st.stop()

# CÁLCULO DE SALDO EM TEMPO REAL
entradas, saidas, saldo_atual = 0.0, 0.0, 0.0

if not df_financeiro.empty:
    # Padroniza os nomes das colunas para evitar erros de maiúsculas/minúsculas
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

# ABAS DE NAVEGAÇÃO ORGANIZADAS
aba_socios, aba_financeiro = st.tabs(["👥 Controle de Sócios", "💸 Fluxo de Caixa"])

with aba_socios:
    st.subheader("Lista de Sócios Cadastrados")
    if not df_socios.empty:
        st.dataframe(df_socios, use_container_width=True)
    else:
        st.info("Nenhum sócio encontrado na aba 'Socios' da planilha.")

with aba_financeiro:
    st.subheader("Histórico do Extrato Financeiro")
    if not df_financeiro.empty:
        st.dataframe(df_financeiro, use_container_width=True)
    else:
        st.info("Nenhuma movimentação encontrada na aba 'Financeiro' da planilha.")
