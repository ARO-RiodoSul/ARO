import streamlit as st
import pandas as pd
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="📊", layout="wide")

# --- SISTEMA DE LOGIN DE SEGURANÇA ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "user"

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        _, col_logo_meio, _ = st.columns(3)
        col_logo_meio.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #6B7280; font-family: sans-serif;'>ARO - Rio do Sul</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9CA3AF;'>Insira suas credenciais abaixo para acessar o sistema.</p>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("tela_login"):
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário...")
        senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...")
        if st.form_submit_button("Entrar no Sistema"):
            if usuario == "Junior Rebelo" and senha == "270688":
                st.session_state["autenticado"], st.session_state["user_role"] = True, "master"
                st.rerun()
            elif usuario == "Kleven" and senha == "12345678":
                st.session_state["autenticado"], st.session_state["user_role"] = True, "leitor"
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# ==============================================================================
# PAINEL INTERNO (APÓS LOGIN)
# ==============================================================================
if "tela_atual" not in st.session_state:
    st.session_state["tela_atual"] = "menu"

# 1. MEMÓRIA DOS SÓCIOS (1 A 100)
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.DataFrame([
        {"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 101)
    ])

# 2. LISTA DE MESES (DEZ 2026 - DEZ 2028)
lista_meses_completa = ["Dezembro 2026"] + [f"{m} {a}" for a in [2027, 2028] for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]]

# 3. BANCO DE DADOS FINANCEIRO INTERNO
if "saldo_anterior_master" not in st.session_state:
    st.session_state["saldo_anterior_master"] = 0.0

if "dados_meses_financeiros" not in st.session_state:
    st.session_state["dados_meses_financeiros"] = {
        m_ref: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m_ref in lista_meses_completa
    }

# MATEMÁTICA FINANCEIRA GLOBAL
total_entradas_global = sum(pd.to_numeric(st.session_state["dados_meses_financeiros"][m]["Entradas"], errors='coerce').sum() for m in lista_meses_completa)
total_saidas_global = sum(pd.to_numeric(st.session_state["dados_meses_financeiros"][m]["Saídas"], errors='coerce').sum() for m in lista_meses_completa)
saldo_gestao_atual = total_entradas_global - total_saidas_global
saldo_total_global = total_entradas_global + st.session_state["saldo_anterior_master"] - total_saidas_global

# --- TELA 1: MENU PRINCIPAL ---
if st.session_state["tela_atual"] == "menu":
    col_logo, col_titulo, col_logout = st.columns([1, 4, 1])
    if os.path.exists("logo.png"): col_logo.image("logo.png", width=80)
    col_titulo.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    if col_logout.button("🔒 Sair"):
        st.session_state["autenticado"] = False
        st.rerun()
        
    st.markdown("---")
    st.info("⭐ Acesso Master" if st.session_state["user_role"] == "master" else "ℹ️ Acesso de Consulta (Apenas Leitura)")
    
    col_btn_socios, col_btn_caixa = st.columns(2)
    with col_btn_socios:
        st.markdown("<h1 style='text-align: center; margin: 0; color: #FBBF24;'>👥</h1>", unsafe_allow_html=True)
        if st.button("Sócios", use_container_width=True, type="primary"):
            st.session_state["tela_atual"] = "socios"
            st.rerun()
    with col_btn_caixa:
        st.markdown("<h1 style='text-align: center; margin: 0; color: #FBBF24;'>🪙</h1>", unsafe_allow_html=True)
        if st.button("Finanças", use_container_width=True, type="primary"):
            st.session_state["tela_atual"] = "caixa"
            st.rerun()

# --- TELA 2: SÓCIOS ---
elif st.session_state["tela_atual"] == "socios":
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
    st.title("👥 Controle de Sócios")
    st.markdown("---")
    if st.session_state["user_role"] == "master":
        st.session_state["dados_socios_internos"] = st.data_editor(st.session_state["dados_socios_internos"], use_container_width=True, disabled=["Número"], column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo"], required=True)}, hide_index=True)
    else:
        st.dataframe(st.session_state["dados_socios_internos"], use_container_width=True, hide_index=True)

# --- TELA 3: FINANÇAS ---
elif st.session_state["tela_atual"] == "caixa":
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("🪙 Controle Financeiro - Finanças")
    st.markdown("---")
    
    # 1. Topo: Saldo Anterior
    _, col_anterior_meio, _ = st.columns([1, 2, 1])
    with col_anterior_meio:
        st.markdown("<h3 style='text-align: center;'>🏦 Saldo Anterior</h3>", unsafe_allow_html=True)
        if st.session_state["user_role"] == "master":
            st.session_state["saldo_anterior_master"] = st.number_input("Editar Valor", value=st.session_state["saldo_anterior_master"], step=50.0, format="%.2f", label_visibility="collapsed")
        else:
            st.markdown(f"<h4 style='text-align: center; color: #1E3A8A;'>R$ {st.session_state['saldo_anterior_master']:,.2f}</h4>", unsafe_allow_html=True)
            
    # 2. Meio e Base: Métricas Financeiras
    st.markdown("<br>", unsafe_allow_html=True)
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("🟢 Total de Entradas", f"R$ {total_entradas_global:,.2f}")
    c_m2.metric("🔴 Total de Saídas", f"R$ {total_saidas_global:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c_b1, c_b2 = st.columns(2)
    c_b1.metric("📊 Saldo (Gestão Atual)", f"R$ {saldo_gestao_atual:,.2f}")
    c_b2.metric("💰 Saldo (Total)", f"R$ {saldo_total_global:,.2f}")
    st.markdown("---")
    
    # Seleção de Meses e Lançamentos
    mes_selecionado = st.selectbox("📅 Selecione o Mês de Trabalho:", lista_meses_completa)
    st.markdown(f"### 🗓️ Lançamentos Diários: {mes_selecionado}")
    
    df_mes_ativo = st.session_state["dados_meses_financeiros"][mes_selecionado]
    
    if st.session_state["user_role"] == "master":
        df_mes_editado = st.data_editor(
            df_mes_ativo, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "Dia": st.column_config.NumberColumn("Dia"),
                "Entradas": st.column_config.NumberColumn("Entradas (R$)", min_value=0.0, format="%.2f"),
                "Saídas": st.column_config.NumberColumn("Saídas (R$)", min_value=0.0, format="%.2f"),
                "Motivo": st.column_config.TextColumn("Motivo / Descrição")
            }
        )
        st.session_state["dados_meses_financeiros"][mes_selecionado] = df_mes_editado
        
        with st.expander("➕ Criar Linha Dupla / Extra para o mesmo Dia"):
            with st.form(f"f_ex_{mes_selecionado}", clear_on_submit=True):
                c_d, c_e, c_s, c_m = st.columns(4)
                d_ex = c_d.number_input("Dia", min_value=1, max_value=31, value=1)
                e_ex = c_e.number_input("Entrada (R$)", min_value=0.0, format="%.2f")
                s_ex = c_s.number_input("Saída (R$)", min_value=0.0, format="%.2f")
                m_ex = c_m.text_input("Motivo")
                if st.form_submit_button("Inserir Linha Extra") and (e_ex > 0 or s_ex > 0):
                    st.session_state["dados_meses_financeiros"][mes_selecionado] = pd.concat([df_mes_editado, pd.DataFrame([{"Dia": d_ex, "Entradas": e_ex, "Saídas": s_ex, "Motivo": m_ex}])], ignore_index=True)
                    st.slots = st.success("Linha adicionada!")
                    st.rerun()
    else:
        st.dataframe(df_mes_ativo, use_container_width=True, hide_index=True)

    # Fechamento e Somas do Mês Selecionado
    st.markdown("---")
    m_ent = pd.to_numeric(df_mes_ativo["Entradas"], errors='coerce').sum()
    m_sai = pd.to_numeric(df_mes_ativo["Saídas"], errors='coerce').sum()
    
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.markdown(f"📊 **Total Entradas do Mês:** R$ {m_ent:,.2f}")
    col_t2.markdown(f"📊 **Total Saídas do Mês:** R$ {m_sai:,.2f}")
    col_t3.markdown(f"📉 **Saldo Líquido do Mês:** R$ {(m_ent - m_sai):,.2f}")
