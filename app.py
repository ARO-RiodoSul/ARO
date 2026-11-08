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

# SE O USUÁRIO NÃO ESTIVER LOGADO, MOSTRA A TELA DE LOGIN (CAPA)
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
                st.session_state["user_role"] = "master"  # Define como usuário Master
                st.success("Acesso Master autorizado! Carregando...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")
                
    st.stop()

# ==============================================================================
# PAINEL INTERNO ARO RIO DO SUL (APÓS LOGIN)
# ==============================================================================

if "tela_atual" not in st.session_state:
    st.session_state["tela_atual"] = "menu"

# CONEXÃO DIRETA COM O GOOGLE SHEETS
try:
    url_base = st.secrets["connections"]["gsheets"]["spreadsheet"]
    if "/edit" in url_base:
        link_limpo = url_base.split("/edit")[0]
    else:
        link_limpo = url_base
        
    url_socios = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Socios"
    url_financeiro = f"{link_limpo}/gviz/tq?tqx=out:csv&sheet=Financeiro"

    df_socios_web = pd.read_csv(url_socios)
    df_financeiro = pd.read_csv(url_financeiro)
except Exception as e:
    st.error("Erro ao conectar à planilha. Verifique se o link está público e correto nos Secrets.")
    st.stop()

# --- TELA 1: MENU PRINCIPAL ---
if st.session_state["tela_atual"] == "menu":
    
    col_logo, col_titulo, col_logout = st.columns([1, 4, 1])
    
    if os.path.exists("logo.png"):
        col_logo.image("logo.png", width=80)
    
    col_titulo.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    
    if col_logout.button("🔒 Sair do App"):
        st.session_state["autenticado"] = False
        st.session_state["user_role"] = "user"
        st.rerun()
        
    st.markdown("---")
    
    if st.session_state["user_role"] == "master":
        st.info("⭐ Modo Administrador: Acesso Master Ativado")
    
    st.markdown("<br>", unsafe_allow_html=True)
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

# --- TELA 2: SÓCIOS (REESTRUTURADO CONFORME AS ESPECIFICAÇÕES) ---
elif st.session_state["tela_atual"] == "socios":
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("👥 Controle de Sócios (ARO)")
    st.markdown("---")
    
    # Montagem da estrutura de 1 a 100 linhas fixas
    linhas_fixas = []
    for i in range(1, 101):
        # Tenta buscar os dados existentes vindos da planilha
        if i - 1 < len(df_socios_web):
            dados_linha = df_socios_web.iloc[i - 1]
            linhas_fixas.append({
                "Número": i,
                "ID": dados_linha.get("ID", ""),
                "Nome": dados_linha.get("Nome", ""),
                "Telefone": dados_linha.get("Telefone", ""),
                "CPF": dados_linha.get("CPF", ""),
                "CTF": dados_linha.get("CTF", ""),
                "Status": dados_linha.get("Status", "Ativo")
            })
        else:
            # Preenche linhas vazias caso a planilha ainda não tenha 100 registros
            linhas_fixas.append({
                "Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"
            })
            
    df_estrutura_socios = pd.DataFrame(linhas_fixas)
    
    # TRAVA DE SEGURANÇA: Se não for o usuário master, a tabela fica bloqueada para alterações
    if st.session_state["user_role"] == "master":
        st.success("📝 Você está logado como Master. Edição de colunas liberada abaixo:")
        
        # Torna a tabela totalmente editável na tela pelo usuário Master
        df_editado = st.data_editor(
            df_estrutura_socios,
            use_container_width=True,
            disabled=["Número"], # Primeira coluna 'Número' é protegida e auto-incremental
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Ativo", "Inativo"],
                    required=True
                )
            },
            hide_index=True
        )
        
        # Botão auxiliar para sincronizar ou gerenciar dados com o Drive
        with st.expander("📂 Sincronização e Ajustes manuais com a Planilha"):
            st.markdown(f"Abra a sua planilha do Google Drive para consolidar alterações em massa ou copiar dados:")
            st.markdown(f"[➡️ Abrir Planilha Google Sheets]({url_base})")
    else:
        st.warning("🔒 Visualização restrita. Somente o usuário Master pode editar estas colunas.")
        st.dataframe(df_estrutura_socios, use_container_width=True, hide_index=True)

# --- TELA 3: FINANÇAS ---
elif st.session_state["tela_atual"] == "caixa":
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("🪙 Finanças")
    st.markdown("---")
    
    entradas, saidas, saldo_atual = 0.0, 0.0, 0.0
    if not df_financeiro.empty:
        df_financeiro.columns = [c.strip().title() for c in df_financeiro.columns]
        if "Tipo" in df_financeiro.columns and "Valor" in df_financeiro.columns:
            df_financeiro["Valor"] = pd.to_numeric(df_financeiro["Valor"], errors='coerce').fillna(0)
            entradas = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
            saidas = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
            saldo_atual = entradas - saidas

    col1, col2, col3 = st.columns(3)
    col1.metric(label="🟢 Total de Entradas", value=f"R$ {entradas:,.2f}")
    col2.metric(label="🔴 Total de Saídas", value=f"R$ {saidas:,.2f}")
    col3.metric(label="💰 Saldo Atual em Caixa", value=f"R$ {saldo_atual:,.2f}")
    st.markdown("---")
    
    st.dataframe(df_financeiro, use_container_width=True)

