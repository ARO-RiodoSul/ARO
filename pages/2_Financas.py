import streamlit as st
import pandas as pd
import datetime
import io
import pickle

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Finanças - Painel ARO", page_icon="💰", layout="wide")

# --- TRAVA DE SEGURANÇA POR CATEGORIA DE USUÁRIO ---
if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

# Título do Módulo
st.title("💰 Fluxo de Caixa - ARO Rio do Sul")

is_master = st.session_state.get("user_role") == "master"

# Cronologia dos meses idêntica ao app.py
lista_meses = ["Dezembro 2026"] + [f"{m} {a}" for a in ["2027", "2028"] for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]]

# Garantir carregamento centralizado e inicializar com dias fixos de 1 a 31
if "dados_meses_financeiros" not in st.session_state:
    st.session_state["dados_meses_financeiros"] = {m: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m in lista_meses}

if "saldo_anterior_master" not in st.session_state:
    st.session_state["saldo_anterior_master"] = 0.0

df_global_financas = st.session_state["dados_meses_financeiros"]

# --- CÁLCULO DOS TOTAIS ACUMULADOS ---
total_entradas_geral = 0.0
total_saidas_geral = 0.0

for m in lista_meses:
    df_m = df_global_financas[m]
    if df_m is not None and not df_m.empty:
        total_entradas_geral += pd.to_numeric(df_m["Entradas"], errors='coerce').fillna(0).sum()
        total_saidas_geral += pd.to_numeric(df_m["Saídas"], errors='coerce').fillna(0).sum()

saldo_anterior = st.session_state["saldo_anterior_master"]
saldo_gestao = total_entradas_geral - total_saidas_geral
saldo_total = saldo_anterior + saldo_gestao

# --- 1. MENU PRINCIPAL (Layout ARO) ---
st.markdown("### 📊 Resumo Consolidado Geral")

with st.container():
    if is_master:
        novo_saldo_anterior = st.number_input("Saldo Anterior (R$)", value=float(saldo_anterior), step=100.0, key="edit_saldo_ant")
        if novo_saldo_anterior != saldo_anterior:
            st.session_state["saldo_anterior_master"] = novo_saldo_anterior
            try:
                with open("backup_saldo_ant.txt", "w") as f: f.write(str(novo_saldo_anterior))
            except: pass
            st.rerun()
    else:
        st.metric(label="Saldo Anterior", value=f"R$ {saldo_anterior:,.2f}")

st.write("---")

col_meio_1, col_meio_2 = st.columns(2)
with col_meio_1:
    st.metric(label="Total de Entradas", value=f"R$ {total_entradas_geral:,.2f}")
with col_meio_2:
    st.metric(label="Total de Saídas", value=f"R$ {total_saidas_geral:,.2f}")

st.write("---")

col_baixo_1, col_baixo_2 = st.columns(2)
with col_baixo_1:
    st.metric(label="Saldo (Gestão Atual)", value=f"R$ {saldo_gestao:,.2f}")
with col_baixo_2:
    st.metric(label="Saldo (Total)", value=f"R$ {saldo_total:,.2f}")

st.write("---")

# --- 2. SELEÇÃO DE VISUALIZAÇÃO MENSAL ---
st.markdown("### 📅 Lançamentos Mensais")
mes_selecionado = st.selectbox("Selecione o mês para visualizar/editar:", lista_meses)

df_atual = df_global_financas[mes_selecionado]

total_entradas_mes = pd.to_numeric(df_atual["Entradas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
total_saidas_mes = pd.to_numeric(df_atual["Saídas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
saldo_mes = total_entradas_mes - total_saidas_mes

col_mes_1, col_mes_2, col_mes_3 = st.columns(3)
with col_mes_1: st.metric("Entradas do Mês", f"R$ {total_entradas_mes:,.2f}")
with col_mes_2: st.metric("Saídas do Mês", f"R$ {total_saidas_mes:,.2f}")
with col_mes_3: st.metric("Balanço do Mês", f"R$ {saldo_mes:,.2f}")

st.write("")
st.markdown(f"**Tabela de Movimentações - {mes_selecionado}**")

if is_master:
    # num_rows="dynamic" reativado para liberar o "+" no rodapé e poder repetir dias
    df_editado = st.data_editor(
        df_atual,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Dia": st.column_config.NumberColumn("Dia", min_value=1, max_value=31, step=1, format="%d", required=True),
            "Entradas": st.column_config.NumberColumn("Entradas (R$)", min_value=0.0, format="%.2f", default=0.0),
            "Saídas": st.column_config.NumberColumn("Saídas (R$)", min_value=0.0, format="%.2f", default=0.0),
            "Motivo": st.column_config.TextColumn("Motivo/Descrição")
        },
        disabled=False,
        key=f"editor_financeiro_{mes_selecionado}",
        use_container_width=True
    )
    
    if not df_editado.equals(df_atual):
        df_editado["Dia"] = pd.to_numeric(df_editado["Dia"], errors='coerce')
        # Organiza de forma crescente pelo dia automaticamente
        df_editado = df_editado.dropna(subset=["Dia"]).sort_values(by="Dia").reset_index(drop=True)
        st.session_state["dados_meses_financeiros"][mes_selecionado] = df_editado
        try:
            pickle.dump(st.session_state["dados_meses_financeiros"], open("backup_financas.pkl", "wb"))
        except: pass
        st.rerun()
else:
    st.dataframe(df_atual, hide_index=True, column_config={"Dia": "Dia", "Entradas": st.column_config.NumberColumn("Entradas (R$)", format="%.2f"), "Saídas": st.column_config.NumberColumn("Saídas (R$)", format="%.2f"), "Motivo": "Motivo/Descrição"}, use_container_width=True)

# --- 3. RECURSO DE RELATÓRIO IMPRESSO COMPLETO ---
if is_master:
    st.write("---")
    st.markdown("### 🖨️ Relatórios do Sistema")
    
    if st.button("Gerar Relatório de Impressão Completo", use_container_width=True):
        st.success("Relatório gerado com sucesso logo abaixo! Pressione Ctrl+P no seu teclado para imprimir ou salvar em PDF.")
        st.write("---")
        
        st.markdown("<h2 style='text-align: center;'>🦅 RELATÓRIO FINANCEIRO INTEGRADO - ARO RIO DO SUL</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'><b>Data de Emissão:</b> {datetime.date.today().strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
        st.write(f"**Saldo Anterior Geral:** R$ {saldo_anterior:,.2f}")
        st.write(f"**Total Acumulado de Entradas:** R$ {total_entradas_geral:,.2f}")
        st.write(f"**Total Acumulado de Saídas:** R$ {total_saidas_geral:,.2f}")
        st.write(f"**Saldo Total de Caixa:** R$ {saldo_total:,.2f}")
        st.write("---")
        
        for m in lista_meses:
            df_m = st.session_state["dados_meses_financeiros"][m]
            st.markdown(f"### 📅 Período: {m}")
            if df_m is not None and not df_m.empty:
                # Filtrar linhas que possuem movimentações reais para economizar papel na impressão
                df_filtro = df_m[(df_m["Entradas"] > 0) | (df_m["Saídas"] > 0) | (df_m["Motivo"].str.strip() != "")]
                if not df_filtro.empty:
                    df_impressao = df_filtro.copy()
                    df_impressao["Dia"] = df_impressao["Dia"].astype(int)
                    df_impressao["Entradas (R$)"] = df_impressao["Entradas"].map(lambda x: f"R$ {float(x):,.2f}")
                    df_impressao["Saídas (R$)"] = df_impressao["Saídas"].map(lambda x: f"R$ {float(x):,.2f}")
                    st.table(df_impressao[["Dia", "Entradas (R$)", "Saídas (R$)", "Motivo"]].rename(columns={"Motivo": "Motivo/Descrição"}))
                else:
                    st.caption("Sem movimentações registradas neste mês.")
            st.markdown("<div style='page-break-after: always;'></div>", unsafe_allow_html=True)
