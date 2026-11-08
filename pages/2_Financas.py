import streamlit as st
import pandas as pd
import datetime

# Configuração da página
st.set_page_config(page_title="Finanças - Painel ARO", page_icon="💰", layout="wide")

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

# Inicializar com tabela vazia estruturada se não existir
for m in lista_meses:
    if m not in st.session_state["financas_data"]["meses"]:
        st.session_state["financas_data"]["meses"][m] = pd.DataFrame(
            columns=["Dia", "Entradas", "Saídas", "Motivo"]
        )

# --- SELEÇÃO DE VISUALIZAÇÃO MENSAL ---
st.markdown("### 📅 Lançamentos Mensais")
mes_selecionado = st.selectbox("Selecione o mês para visualizar/editar:", lista_meses)

df_atual = st.session_state["financas_data"]["meses"][mes_selecionado]

st.write("")
st.markdown(f"**Tabela de Movimentações - {mes_selecionado}**")

if is_master:
    # O próprio Streamlit salva no session_state usando a chave key sem precisar de st.rerun
    df_editado = st.data_editor(
        df_atual,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Dia": st.column_config.NumberColumn("Dia", min_value=1, max_value=31, step=1, format="%d", required=True),
            "Entradas": st.column_config.NumberColumn("Entradas (R$)", min_value=0.0, format="%.2f", default=0.0),
            "Saídas": st.column_config.NumberColumn("Saídas (R$)", min_value=0.0, format="%.2f", default=0.0),
            "Motivo": st.column_config.TextColumn("Motivo/Descrição", required=True)
        },
        disabled=False,
        key=f"editor_dados_{mes_selecionado}"
    )
    # Atualiza o estado global com os dados editados da tabela
    st.session_state["financas_data"]["meses"][mes_selecionado] = df_editado
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

# --- CÁLCULO E AGREGAÇÃO DOS TOTAIS RECALCULADOS EM TEMPO REAL ---
total_entradas_geral = 0.0
total_saidas_geral = 0.0

for m in lista_meses:
    df_m = st.session_state["financas_data"]["meses"][m]
    if df_m is not None and not df_m.empty:
        total_entradas_geral += pd.to_numeric(df_m["Entradas"], errors='coerce').fillna(0).sum()
        total_saidas_geral += pd.to_numeric(df_m["Saídas"], errors='coerce').fillna(0).sum()

saldo_anterior = st.session_state["financas_data"]["saldo_anterior"]
saldo_gestao = total_entradas_geral - total_saidas_geral
saldo_total = saldo_anterior + saldo_gestao

# Totais específicos do mês selecionado
total_entradas_mes = pd.to_numeric(df_editado["Entradas"], errors='coerce').fillna(0).sum() if is_master else pd.to_numeric(df_atual["Entradas"], errors='coerce').fillna(0).sum()
total_saidas_mes = pd.to_numeric(df_editado["Saídas"], errors='coerce').fillna(0).sum() if is_master else pd.to_numeric(df_atual["Saídas"], errors='coerce').fillna(0).sum()
saldo_mes = total_entradas_mes - total_saidas_mes

# --- EXIBIÇÃO DE MÉTRICAS ABAIXO DA TABELA PARA EVITAR CONFLITO DE RECARREGAMENTO ---
st.write("---")
st.markdown(f"### 📊 Resumo do Mês Selecionado ({mes_selecionado})")
col_mes = st.columns(3)
col_mes.metric("Entradas do Mês", f"R$ {total_entradas_mes:,.2f}")
col_mes.metric("Saídas do Mês", f"R$ {total_saidas_mes:,.2f}")
col_mes.metric("Balanço do Mês", f"R$ {saldo_mes:,.2f}")

st.write("---")
st.markdown("### 📊 Resumo Consolidado Geral")
if is_master:
    novo_saldo_anterior = st.number_input("Saldo Anterior (R$)", value=float(saldo_anterior), step=100.0, key="edit_saldo_ant")
    if novo_saldo_anterior != saldo_anterior:
        st.session_state["financas_data"]["saldo_anterior"] = novo_saldo_anterior
else:
    st.metric(label="Saldo Anterior", value=f"R$ {saldo_anterior:,.2f}")

col_finais = st.columns(4)
col_finais.metric("Total de Entradas", f"R$ {total_entradas_geral:,.2f}")
col_finais.metric("Total de Saídas", f"R$ {total_saidas_geral:,.2f}")
col_finais.metric("Saldo (Gestão)", f"R$ {saldo_gestao:,.2f}")
col_finais.metric("Saldo Total", f"R$ {saldo_total:,.2f}")
