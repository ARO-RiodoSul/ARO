import streamlit as st
import pandas as pd
import datetime

# Configuração da página
st.set_page_config(page_title="Finanças - Painel ARO", page_icon="💰", layout="wide")

# Título do Módulo
st.title("💰 Fluxo de Caixa - ARO Rio do Sul")

# Validar se o usuário é Master para liberar a edição
is_master = st.session_state.get("username") == "Junior Rebelo"

# Inicializar dados financeiros no session_state se não existirem
if "financas_data" not in st.session_state:
    st.session_state["financas_data"] = {
        "saldo_anterior": 0.0,
        "meses": {}
    }

# Gerar lista de meses de Dezembro 2026 até Dezembro 2028
start_date = datetime.date(2026, 12, 1)
end_date = datetime.date(2028, 12, 31)

lista_meses = []
current = start_date
while current <= end_date:
    mes_ano = current.strftime("%B %Y").capitalize()
    lista_meses.append(mes_ano)
    if current.month == 12:
        current = datetime.date(current.year + 1, 1, 1)
    else:
        current = datetime.date(current.year, current.month + 1, 1)

# GARANTE A ESTRUTURA FIXA SEVURA (Dias de 1 a 31 sempre visíveis)
for m in lista_meses:
    if m not in st.session_state["financas_data"]["meses"]:
        st.session_state["financas_data"]["meses"][m] = pd.DataFrame(
            {"Dia": [i for i in range(1, 32)], "Entradas": [0.0]*31, "Saídas": [0.0]*31, "Motivo": [""]*31}
        )

# --- CÁLCULO E AGREGAÇÃO DOS TOTAIS ---
total_entradas_geral = 0.0
total_saidas_geral = 0.0

for m in lista_meses:
    df_mes = st.session_state["financas_data"]["meses"][m]
    total_entradas_geral += pd.to_numeric(df_mes["Entradas"], errors='coerce').fillna(0).sum()
    total_saidas_geral += pd.to_numeric(df_mes["Saídas"], errors='coerce').fillna(0).sum()

saldo_anterior = st.session_state["financas_data"]["saldo_anterior"]
saldo_gestao = total_entradas_geral - total_saidas_geral
saldo_total = saldo_anterior + saldo_gestao

# --- 1. MENU PRINCIPAL (Métricas) ---
st.markdown("### 📊 Resumo Consolidado Geral")

col_topo = st.columns(1)
with col_topo:
    if is_master:
        novo_saldo_anterior = st.number_input("Saldo Anterior (R$)", value=float(saldo_anterior), step=100.0, key="edit_saldo_ant")
        if novo_saldo_anterior != saldo_anterior:
            st.session_state["financas_data"]["saldo_anterior"] = novo_saldo_anterior
            st.rerun()
    else:
        st.metric(label="Saldo Anterior", value=f"R$ {saldo_anterior:,.2f}")

st.write("---")

col_meio = st.columns(2)
with col_meio:
    st.metric(label="Total de Entradas", value=f"R$ {total_entradas_geral:,.2f}")
with col_meio:
    st.metric(label="Total de Saídas", value=f"R$ {total_saidas_geral:,.2f}")

st.write("---")

col_baixo = st.columns(2)
with col_baixo:
    st.metric(label="Saldo (Gestão Atual)", value=f"R$ {saldo_gestao:,.2f}")
with col_baixo:
    st.metric(label="Saldo (Total)", value=f"R$ {saldo_total:,.2f}")

st.write("---")

# --- 2. SELEÇÃO DE VISUALIZAÇÃO MENSAL ---
st.markdown("### 📅 Lançamentos Mensais")
mes_selecionado = st.selectbox("Selecione o mês para visualizar/editar:", lista_meses)

df_atual = st.session_state["financas_data"]["meses"][mes_selecionado]

total_entradas_mes = pd.to_numeric(df_atual["Entradas"], errors='coerce').fillna(0).sum()
total_saidas_mes = pd.to_numeric(df_atual["Saídas"], errors='coerce').fillna(0).sum()
saldo_mes = total_entradas_mes - total_saidas_mes

col_mes_totais = st.columns(3)
col_mes_totais.metric("Entradas do Mês", f"R$ {total_entradas_mes:,.2f}")
col_mes_totais.metric("Saídas do Mês", f"R$ {total_saidas_mes:,.2f}")
col_mes_totais.metric("Balanço do Mês", f"R$ {saldo_mes:,.2f}")

st.write("")
st.markdown(f"**Tabela de Movimentações - {mes_selecionado}**")

# SOLUÇÃO PARA O MESMO DIA: Deixamos a tabela fixa e adicionamos um campo extra abaixo para lançamentos adicionais se faltar espaço
if is_master:
    df_editado = st.data_editor(
        df_atual,
        hide_index=True,
        column_config={
            "Dia": st.column_config.NumberColumn("Dia", disabled=True),
            "Entradas": st.column_config.NumberColumn("Entradas (R$)", min_value=0.0, format="%.2f"),
            "Saídas": st.column_config.NumberColumn("Saídas (R$)", min_value=0.0, format="%.2f"),
            "Motivo": st.column_config.TextColumn("Motivo/Descrição")
        },
        disabled=False,
        key=f"editor_estatico_{mes_selecionado}"
    )
    
    if not df_editado.equals(df_atual):
        st.session_state["financas_data"]["meses"][mes_selecionado] = df_editado
        st.rerun()
else:
    st.dataframe(
        df_atual,
        hide_index=True,
        column_config={
            "Dia": "Dia",
            "Entradas": st.column_config.NumberColumn("Entradas (R$)", format="%.2f"),
            "Saídas": st.column_config.NumberColumn("Saídas (R$)", format="%.2f"),
            "Motivo": "Motivo/Descrição"
        }
    )

