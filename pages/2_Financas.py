import streamlit as st
import pandas as pd
import datetime

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Finanças - Painel ARO", page_icon="💰", layout="wide")

# --- TRAVA DE SEGURANÇA POR CATEGORIA DE USUÁRIO ---
# Só permite o acesso para Master e Diretoria. Bloqueia Sócios e Visitantes.
if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

# Título do Módulo
st.title("💰 Fluxo de Caixa - ARO Rio do Sul")

# Validar se o usuário possui nível Master para liberar a edição
is_master = st.session_state.get("user_role") == "master"

# Reativar a cronologia padrão idêntica ao seu app.py para não dar conflito
lista_meses = ["Dezembro 2026"] + [f"{m} {a}" for a in ["2027", "2028"] for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]]

# --- GARANTIR O CARREGAMENTO INTEGRADO COM O SEU APP.PY ---
if "dados_meses_financeiros" not in st.session_state:
    st.session_state["dados_meses_financeiros"] = {m: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m in lista_meses}

if "saldo_anterior_master" not in st.session_state:
    st.session_state["saldo_anterior_master"] = 0.0

# --- CÁLCULO E AGREGAÇÃO DOS TOTAIS RECALCULADOS ACUMULADOS ---
total_entradas_geral = 0.0
total_saidas_geral = 0.0

for m in lista_meses:
    df_m = st.session_state["dados_meses_financeiros"][m]
    if df_m is not None and not df_m.empty:
        total_entradas_geral += pd.to_numeric(df_m["Entradas"], errors='coerce').fillna(0).sum()
        total_saidas_geral += pd.to_numeric(df_m["Saídas"], errors='coerce').fillna(0).sum()

saldo_anterior = st.session_state["saldo_anterior_master"]
saldo_gestao = total_entradas_geral - total_saidas_geral
saldo_total = saldo_anterior + saldo_gestao

# --- 1. MENU PRINCIPAL (O Seu Layout Favorito) ---
st.markdown("### 📊 Resumo Consolidado Geral")

# Saldo Anterior no topo - Editável APENAS pelo Junior Rebelo (Master)
with st.container():
    if is_master:
        novo_saldo_anterior = st.number_input("Saldo Anterior (R$)", value=float(saldo_anterior), step=100.0, key="edit_saldo_ant")
        if novo_saldo_anterior != saldo_anterior:
            st.session_state["saldo_anterior_master"] = novo_saldo_anterior
            try:
                with open("backup_saldo_ant.txt", "w") as f:
                    f.write(str(novo_saldo_anterior))
            except: pass
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

df_atual = st.session_state["dados_meses_financeiros"][mes_selecionado]

# Totais rápidos do mês na tela
total_entradas_mes = pd.to_numeric(df_atual["Entradas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
total_saidas_mes = pd.to_numeric(df_atual["Saídas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
saldo_mes = total_entradas_mes - total_saidas_mes

col_mes_1, col_mes_2, col_mes_3 = st.columns(3)
with col_mes_1:
    st.metric("Entradas do Mês", f"R$ {total_entradas_mes:,.2f}")
with col_mes_2:
    st.metric("Saídas do Mês", f"R$ {total_saidas_mes:,.2f}")
with col_mes_3:
    st.metric("Balanço do Mês", f"R$ {saldo_mes:,.2f}")

st.write("")
st.markdown(f"**Tabela Fixo de Movimentações (Dias 1 a 31) - {mes_selecionado}**")

# Retorna a tabela estática com 31 linhas fixas, sem botão de "+" para não quebrar a ordem visual
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
        key=f"editor_estatico_{mes_selecionado}",
        use_container_width=True
    )
    
    if not df_editado.equals(df_atual):
        st.session_state["dados_meses_financeiros"][mes_selecionado] = df_editado
        try:
            import pickle
            pickle.dump(st.session_state["dados_meses_financeiros"], open("backup_financas.pkl", "wb"))
        except: pass
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
        },
        use_container_width=True
    )
