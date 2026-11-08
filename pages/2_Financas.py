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

# CORREÇÃO AQUI: Inicializar com tabela dinâmica vazia (sem travar 31 linhas fixas)
for m in lista_meses:
    if m not in st.session_state["financas_data"]["meses"]:
        st.session_state["financas_data"]["meses"][m] = pd.DataFrame(
            columns=["Dia", "Entradas", "Saídas", "Motivo"]
        )

# --- CÁLCULO E AGREGAÇÃO DOS TOTAIS ---
total_entradas_geral = 0.0
total_saidas_geral = 0.0

for m in lista_meses:
    df_mes = st.session_state["financas_data"]["meses"][m]
    if not df_mes.empty:
        total_entradas_geral += pd.to_numeric(df_mes["Entradas"]).sum()
        total_saidas_geral += pd.to_numeric(df_mes["Saídas"]).sum()

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

# Garantir tipos numéricos para os totais do mês
total_entradas_mes = pd.to_numeric(df_atual["Entradas"]).sum() if not df_atual.empty else 0.0
total_saidas_mes = pd.to_numeric(df_atual["Saídas"]).sum() if not df_atual.empty else 0.0
saldo_mes = total_entradas_mes - total_saidas_mes

col_mes_totais = st.columns(3)
col_mes_totais[0].metric("Entradas do Mês", f"R$ {total_entradas_mes:,.2f}")
col_mes_totais[1].metric("Saídas do Mês", f"R$ {total_saidas_mes:,.2f}")
col_mes_totais[2].metric("Balanço do Mês", f"R$ {saldo_mes:,.2f}")

st.write("")
st.markdown(f"**Tabela de Movimentações - {mes_selecionado}**")

if is_master:
    # O num_rows="dynamic" agora vai funcionar porque o DataFrame original está livre
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
        key=f"editor_{mes_selecionado}"
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

# --- 3. RECURSO DE RELATÓRIO IMPRESSO ---
if is_master:
    st.write("---")
    st.markdown("### 🖨️ Relatórios do Sistema")
    if st.button("Gerar Relatório de Impressão"):
        st.success("Relatório preparado com sucesso! Utilize a função de impressão do seu navegador (Ctrl+P).")
        
        st.markdown("## RELATÓRIO CONSOLIDADO DE CAIXA - ARO")
        st.markdown(f"**Data de Emissão:** {datetime.date.today().strftime('%d/%m/%Y')}")
        st.write(f"**Saldo Anterior:** R$ {saldo_anterior:,.2f}")
        st.write(f"**Total de Entradas (Período):** R$ {total_entradas_geral:,.2f}")
        st.write(f"**Total de Saídas (Período):** R$ {total_saidas_geral:,.2f}")
        st.write(f"**Saldo Total Acumulado:** R$ {saldo_total:,.2f}")
        st.write("---")
        
        for m in lista_meses:
            df_m = st.session_state["financas_data"]["meses"][m]
            if not df_m.empty:
                st.markdown(f"### Mês: {m}")
                st.table(df_m)
                st.markdown("<div style='page-break-after: always;'></div>", unsafe_allow_html=True)
