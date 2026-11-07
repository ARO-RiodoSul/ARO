import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão Associação", page_icon="📊", layout="wide")

st.title("🦅 Sistema de Gestão - Associação")
st.markdown("---")

# CONEXÃO COM O GOOGLE SHEETS
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # LER DADOS DAS ABAS DA PLANILHA
    df_socios = conn.read(worksheet="Socios", ttl=0)
    df_financeiro = conn.read(worksheet="Financeiro", ttl=0)
except Exception:
    st.error("Configure os dados de acesso ao Google Sheets nos Secrets do Streamlit.")
    st.stop()

# CÁLCULO DE SALDO EM TEMPO REAL
if not df_financeiro.empty and "Tipo" in df_financeiro.columns and "Valor" in df_financeiro.columns:
    entradas = pd.to_numeric(df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor']).sum()
    saidas = pd.to_numeric(df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor']).sum()
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
aba_socios, aba_financeiro, aba_relatorios = st.tabs(["👥 Controle de Sócios", "💸 Fluxo de Caixa", "📋 Relatórios Gerais"])

# --- ABA: CONTROLE DE SÓCIOS ---
with aba_socios:
    st.subheader("Cadastrar Novo Sócio")
    with st.form("form_socio", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf = st.text_input("CPF / Identificação")
        status = st.selectbox("Status Inicial", ["Ativo", "Inativo", "Inadimplente"])
        bt_salvar_socio = st.form_submit_button("Gravar Sócio")
        
        if bt_salvar_socio and nome:
            novo_socio = pd.DataFrame([{"Nome": nome, "CPF": cpf, "Status": status}])
            df_atualizado = pd.concat([df_socios, novo_socio], ignore_index=True)
            conn.update(worksheet="Socios", data=df_atualizado)
            st.success(f"Sócio {nome} cadastrado com sucesso!")
            st.rerun()

    st.subheader("Lista de Sócios Cadastrados")
    st.dataframe(df_socios, use_container_width=True)

# --- ABA: FLUXO DE CAIXA ---
with aba_financeiro:
    st.subheader("Lançar Movimentação Financeira")
    with st.form("form_financeiro", clear_on_submit=True):
        col_data, col_desc = st.columns(2)
        data_lanc = col_data.date_input("Data")
        desc_lanc = col_desc.text_input("Descrição")
        
        col_tipo, col_val = st.columns(2)
        tipo_lanc = col_tipo.selectbox("Tipo", ["Entrada", "Saída"])
        valor_lanc = col_val.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f")
        
        bt_salvar_fin = st.form_submit_button("Lançar no Caixa")
        
        if bt_salvar_fin and desc_lanc and valor_lanc > 0:
            nova_mov = pd.DataFrame([{"Data": str(data_lanc), "Descrição": desc_lanc, "Tipo": tipo_lanc, "Valor": valor_lanc}])
            df_fin_atualizado = pd.concat([df_financeiro, nova_mov], ignore_index=True)
            conn.update(worksheet="Financeiro", data=df_fin_atualizado)
            st.success("Movimentação registrada!")
            st.rerun()

# --- ABA: RELATÓRIOS ---
with aba_relatorios:
    st.subheader("Histórico do Extrato Financeiro")
    st.dataframe(df_financeiro, use_container_width=True)
