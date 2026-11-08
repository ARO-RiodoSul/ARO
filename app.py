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
# PAINEL INTERNO ARO RIO DO SUL (INDEPENDENTE DE PLANILHA)
# ==============================================================================

if "tela_atual" not in st.session_state:
    st.session_state["tela_atual"] = "menu"

# INICIALIZAÇÃO DA ESTRUTURA FIXA INTERNA DE 100 SÓCIOS (MEMÓRIA DO APP)
if "dados_socios_internos" not in st.session_state:
    linhas_fixas = []
    for i in range(1, 101):
        linhas_fixas.append({
            "Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"
        })
    st.session_state["dados_socios_internos"] = pd.DataFrame(linhas_fixas)

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

# --- TELA 2: SÓCIOS (100% AUTÔNOMO E EDITÁVEL) ---
elif st.session_state["tela_atual"] == "socios":
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("👥 Controle de Sócios")
    st.markdown("---")
    
    # Exibe orientações dinâmicas para o usuário master
    if st.session_state["user_role"] == "master":
        st.success("📝 Modo Master Ativo: Clique diretamente nas células abaixo para preencher os dados dos 100 sócios.")
        
        # Editor interativo direto na tela atualizado na memória interna
        df_modificado = st.data_editor(
            st.session_state["dados_socios_internos"],
            use_container_width=True,
            disabled=["Número"],  # Protege o contador automático de 1 a 100
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Ativo", "Inativo"],
                    required=True
                )
            },
            hide_index=True,
            key="editor_socios_aro"
        )
        
        # Salva as alterações na memória interna do aplicativo de forma contínua
        st.session_state["dados_socios_internos"] = df_modificado
        
        # Ferramentas locais de ajuste da tabela interna
        with st.expander("⚙️ Opções de Ajuste do Módulo"):
            if st.button("♻️ Resetar Tabela (Apagar as 100 Linhas)"):
                del st.session_state["dados_socios_internos"]
                st.rerun()
    else:
        st.warning("🔒 Modo de Visualização Restrito. Somente o usuário Master pode realizar alterações.")
        st.dataframe(st.session_state["dados_socios_internos"], use_container_width=True, hide_index=True)

# --- TELA 3: FINANÇAS ---
elif st.session_state["tela_atual"] == "caixa":
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state["tela_atual"] = "menu"
        st.rerun()
        
    st.title("🪙 Finanças")
    st.markdown("---")
    st.info("Módulo financeiro pronto para desenvolvimento interno personalizado. Nenhuma planilha externa conectada.")

