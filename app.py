import streamlit as st
import pandas as pd
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="📊", layout="wide")

# --- SISTEMA DE LOGIN DE SEGURANÇA E NÍVEL DE ACESSO ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "user"

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        col_logo_esq, col_logo_meio, col_logo_dir = st.columns(3)
        col_logo_meio.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #6B7280; font-family: sans-serif;'>ARO - Rio do Sul</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9CA3AF;'>Insira suas credenciais abaixo para acessar o sistema.</p>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("tela_login"):
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário...")
        senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...")
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        if botao_entrar:
            if usuario == "Junior Rebelo" and senha == "270688":
                st.session_state["autenticado"] = True
                st.session_state["user_role"] = "master"
                st.success("Acesso Master autorizado! Carregando...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")
    st.stop()

# ==============================================================================
# PAINEL INTERNO ARO RIO DO SUL
# ==============================================================================
if "tela_atual" not in st.session_state:
    st.session_state["tela_atual"] = "menu"

# 1. INICIALIZAÇÃO DA MEMÓRIA DOS SÓCIOS
if "dados_socios_internos" not in st.session_state:
    linhas_socios = [{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 101)]
    st.session_state["dados_socios_internos"] = pd.DataFrame(linhas_socios)

# 2. LISTA DE MESES (DEZ 2026 - DEZ 2028)
anos = [2026, 2027, 2028]
meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
lista_meses_completa = []
for ano in anos:
    for m_idx, nome_m in enumerate(meses_nomes):
        if ano == 2026 and m_idx != 11:  # Começa estritamente em Dezembro de 2026
            continue
        lista_meses_completa.append(f"{nome_m} {ano}")

# 3. INICIALIZAÇÃO DO BANCO DE DADOS DE MESES FINANCEIROS
if "saldo_anterior_master" not in st.session_state:
    st.session_state["saldo_anterior_master"] = 0.0

if "dados_meses_financeiros" not in st.session_state:
    st.session_state["dados_meses_financeiros"] = {}
    for mes_ref in lista_meses_completa:
        linhas_mes = [{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]
        st.session_state["dados_meses_financeiros"][mes_ref] = pd.DataFrame(linhas_mes)

# --- MATEMÁTICA FINANCEIRA GLOBAL EM TEMPO REAL ---
total_entradas_global = 0.0
total_saidas_global = 0.0

for m_ref in lista_meses_completa:
    df_m = st.session_state["dados_meses_financeiros"][m_ref]
    total_entradas_global += pd.to_numeric(df_m["Entradas"], errors='coerce').sum()
    total_saidas_global += pd.to_numeric(df_m["Saídas"], errors='coerce').sum()

saldo_gestao_atual = total_entradas_global - total_saidas_global
saldo_total_global = total_entradas_global + st.session_state["saldo_anterior_master"] - total_saidas_global

# --- TELA 1: MENU PRINCIPAL ---
if st.session_state["tela_atual"] == "menu":
    col_logo, col_titulo, col_logout = st.columns(3)
    if os.path.exists("logo.png"):
        col_logo.image("logo.png", width=80)
    col_titulo.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    if col_logout.button("🔒 Sair do App"):
        st.session_state["autenticado"] = False
        st.session_state["user_role"] = "user"
        st.rerun()
        
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Selecione o módulo de gerenciamento:</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
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
        df_modificado = st.data_editor(st.session_state["dados_socios_internos"], use_container_width=True, disabled=["Número"], column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo"], required=True)}, hide_index=True, key="editor_socios_aro")
        st.session_state["dados_socios_internos"] = df_modificado
    else:
        st.dataframe(st.session_state["dados_socios_internos"], use_container_width=True, hide_index=True)

# --- TELA 3: FINANÇAS ---
elif st.session_state["tela_atual"] == "caixa":
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("🪙 Controle Financeiro - Finanças")
    st.markdown("---")
    
    # INDICADORES SUPERIORES
    met_1, met_2, met_3, met_4, met_5 = st.columns(5)
    
    with met_1:
        st.markdown("### 🏦 Saldo Anterior")
        if st.session_state["user_role"] == "master":
            st.session_state["saldo_anterior_master"] = st.number_input("Editar Valor (R$)", value=st.session_state["saldo_anterior_master"], step=50.0, format="%.2f", label_visibility="collapsed")
        else:
            st.markdown(f"**R$ {st.session_state['saldo_anterior_master']:,.2f}**")
            
    met_2.metric(label="🟢 Total de Entradas", value=f"R$ {total_entradas_global:,.2f}")
    met_3.metric(label="🔴 Total de Saídas", value=f"R$ {total_saidas_global:,.2f}")
    met_4.metric(label="📊 Saldo (Gestão Atual)", value=f"R$ {saldo_gestao_atual:,.2f}")
    met_5.metric(label="💰 Saldo (Total)", value=f"R$ {saldo_total_global:,.2f}")
    
    st.markdown("---")
    
    # NAVEGAÇÃO DOS MESES
    st.subheader("📅 Selecione o Mês de Trabalho")
    mes_selecionado = st.selectbox("Escolha o período:", lista_meses_completa, index=0)
    
    st.markdown(f"### 🗓️ Lançamentos Diários: {mes_selecionado}")
    
    df_mes_ativo = st.session_state["dados_meses_financeiros"][mes_selecionado]
    
    if st.session_state["user_role"] == "master":
        st.success("📝 Modo Master Ativo: Edite os valores diretamente na tabela. Para criar linhas extras no mesmo dia, use o botão azul embaixo.")
        
        df_mes_editado = st.data_editor(
            df_mes_ativo,
            use_container_width=True,
            column_config={
                "Dia": st.column_config.NumberColumn("Dia", disabled=False),
                "Entradas": st.column_config.NumberColumn("Entradas (R$)", min_value=0.0, format="%.2f"),
                "Saídas": st.column_config.NumberColumn("Saídas (R$)", min_value=0.0, format="%.2f"),
                "Motivo": st.column_config.TextColumn("Motivo / Descrição")
            },
            num_rows="dynamic",
            hide_index=True,
            key=f"editor_financeiro_{mes_selecionado}"
        )
        st.session_state["dados_meses_financeiros"][mes_selecionado] = df_mes_editado
        
        # Inserir múltiplos lançamentos por dia
        with st.expander("➕ Inserir Múltiplos Lançamentos por Dia"):
            with st.form(f"form_extra_{mes_selecionado}", clear_on_submit=True):
                c_dia, c_ent, c_sai, c_mot = st.columns(4)
                d_ex = c_dia.number_input("Dia", min_value=1, max_value=31, step=1, value=1)
                e_ex = c_ent.number_input("Entrada (R$)", min_value=0.0, step=10.0, format="%.2f")
                s_ex = c_sai.number_input("Saída (R$)", min_value=0.0, step=10.0, format="%.2f")
                m_ex = c_mot.text_input("Motivo")
                bt_inserir_extra = st.form_submit_button("Adicionar Registro ao Mês")
                
                if bt_inserir_extra and (e_ex > 0 or s_ex > 0):
                    nova_linha_diaria = pd.DataFrame([{"Dia": d_ex, "Entradas": e_ex, "Saídas": s_ex, "Motivo": m_ex}])
                    st.session_state["dados_meses_financeiros"][mes_selecionado] = pd.concat([st.session_state["dados_meses_financeiros"][mes_selecionado], nova_linha_diaria], ignore_index=True)
                    st.success("Registro adicionado com sucesso!")
                    st.rerun()
    else:
        st.dataframe(df_mes_ativo, use_container_width=True, hide_index=True)

    # --- FECHAMENTO E TOTAIS DE SOMA DO MÊS SELECIONADO ---
    st.markdown("---")
    m_entradas = pd.to_numeric(df_mes_ativo["Entradas"], errors='coerce').sum()
    m_saidas = pd.to_numeric(df_mes_ativo["Saídas"], errors='coerce').sum()
    m_saldo = m_entradas - m_saidas

    col_t1, col_t2, col_t3 = st.columns(3)
