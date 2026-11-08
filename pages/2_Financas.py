import streamlit as st
import pandas as pd
import datetime

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Finanças - Painel ARO", page_icon="💰", layout="wide")

# --- TRAVA DE SEGURANÇA POR CATEGORIA DE USUÁRIO ---
# Só permite o acesso para Master e Diretoria. Bloqueia Sócios e Visitantes.
if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop() # Interrompe o carregamento do restante do arquivo na tela

# Título do Módulo
st.title("💰 Fluxo de Caixa - ARO Rio do Sul")

# Validar se o usuário possui nível Master para liberar a edição de campos administrativos
is_master = st.session_state.get("user_role") == "master"

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

# Inicializa como uma tabela dinâmica vazia para permitir o botão "+" e dobrar dias
for m in lista_meses:
    if m not in st.session_state["financas_data"]["meses"]:
        st.session_state["financas_data"]["meses"][m] = pd.DataFrame(
            columns=["Dia", "Entradas", "Saídas", "Motivo"]
        )

# --- CÁLCULO E AGREGAÇÃO DOS TOTAIS RECALCULADOS ACUMULADOS ---
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

# --- 1. MENU PRINCIPAL ---
st.markdown("### 📊 Resumo Consolidado Geral")

# Saldo Anterior no topo - Editável APENAS pelo perfil 'master'
with st.container():
    if is_master:
        novo_saldo_anterior = st.number_input("Saldo Anterior (R$)", value=float(saldo_anterior), step=100.0, key="edit_saldo_ant")
        if novo_saldo_anterior != saldo_anterior:
            st.session_state["financas_data"]["saldo_anterior"] = novo_saldo_anterior
            st.rerun()
    else:
        st.metric(label="Saldo Anterior", value=f"R$ {saldo_anterior:,.2f}")

st.write("---")

# Total de Entradas e Saídas abaixo
col_meio_1, col_meio_2 = st.columns(2)
with col_meio_1:
    st.metric(label="Total de Entradas", value=f"R$ {total_entradas_geral:,.2f}")
with col_meio_2:
    st.metric(label="Total de Saídas", value=f"R$ {total_saidas_geral:,.2f}")

st.write("---")

# Saldos da Gestão e Total embaixo
col_baixo_1, col_baixo_2 = st.columns(2)
with col_baixo_1:
    st.metric(label="Saldo (Gestão Atual)", value=f"R$ {saldo_gestao:,.2f}")
with col_baixo_2:
    st.metric(label="Saldo (Total)", value=f"R$ {saldo_total:,.2f}")

st.write("---")

# --- 2. SELEÇÃO DE VISUALIZAÇÃO MENSAL ---
st.markdown("### 📅 Lançamentos Mensais")
mes_selecionado = st.selectbox("Selecione o mês para visualizar/editar:", lista_meses)

df_atual = st.session_state["financas_data"]["meses"][mes_selecionado]

# Totais rápidos do mês na tela
total_entradas_mes = pd.to_numeric(df_atual["Entradas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
total_saidas_mes = pd.to_numeric(df_atual["Saídas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
saldo_mes = total_entradas_mes - total_saidas_mes

# Desempacotando as colunas de totais mensais corretamente
col_mes_1, col_mes_2, col_mes_3 = st.columns(3)
with col_mes_1:
    st.metric("Entradas do Mês", f"R$ {total_entradas_mes:,.2f}")
with col_mes_2:
    st.metric("Saídas do Mês", f"R$ {total_saidas_mes:,.2f}")
with col_mes_3:
    st.metric("Balanço do Mês", f"R$ {saldo_mes:,.2f}")

st.write("")
st.markdown(f"**Tabela de Movimentações - {mes_selecionado}**")

# Regra de edição: Apenas o Master edita e usa a duplicação dinâmica de dias. Diretoria apenas visualiza.
if is_master:
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
        key=f"editor_financeiro_{mes_selecionado}"
    )
    
    # Se houver mudanças, aplica a ordenação automática pelo Dia antes de salvar
    if not df_editado.equals(df_atual):
        df_editado["Dia"] = pd.to_numeric(df_editado["Dia"], errors='coerce')
        df_editado = df_editado.dropna(subset=["Dia"]).sort_values(by="Dia").reset_index(drop=True)
        st.session_state["financas_data"]["meses"][mes_selecionado] = df_editado
        st.rerun()
else:
    # A diretoria entra aqui: consegue ver todos os dados do caixa mas sem permissão de alterar nada
    st.dataframe(
        df_atual,
        hide_index=True,
        column_config={
            "Dia": "Dia",
            "Entradas": st.column_config.NumberColumn("Entradas (R$)", format="%.2f"),
            "Saídas": st.column_config.NumberColumn("Saídas (R$)", format="%.2f"),
            "Motivo": "Motivo/Descrição"
        },
        use_container_width=True
    )
