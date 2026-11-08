import streamlit as st
import pandas as pd
import datetime

# 1. Configuração Inicial da Página Principal
st.set_page_config(page_title="Painel ARO - Rio do Sul", page_icon="🦅", layout="wide")

# Inicialização segura do Estado do Usuário
if "username" not in st.session_state:
    st.session_state["username"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# --- FUNÇÃO DO RELATÓRIO FINANCEIRO (Totalmente blindada contra erros) ---
def gerar_relatorio_texto():
    txt = "=== RELATÓRIO FINANCEIRO GERAL - ARO ===\n\n"
    if "financas_data" in st.session_state and "meses" in st.session_state["financas_data"]:
        for mes, df_at in st.session_state["financas_data"]["meses"].items():
            if df_at is not None and isinstance(df_at, pd.DataFrame) and not df_at.empty:
                txt += f"\n--- Mês: {mes} ---\n"
                for _, r in df_at.iterrows():
                    try:
                        dia_val = r.get('Dia')
                        motivo_val = r.get('Motivo')
                        if pd.isna(dia_val) or str(dia_val).strip() == "" or pd.isna(motivo_val) or str(motivo_val).strip() == "":
                            continue
                        dia_int = int(float(dia_val))
                        ent = float(r.get('Entradas', 0.0)) if pd.notna(r.get('Entradas')) else 0.0
                        sai = float(r.get('Saídas', 0.0)) if pd.notna(r.get('Saídas')) else 0.0
                        txt += f"Dia {dia_int:02d} | Entrada: R$ {ent:.2f} | Saída: R$ {sai:.2f} | Motivo: {motivo_val}\n"
                    except:
                        continue
    return txt

# --- 2. SISTEMA DE LOGIN E CONTROLE DE ACESSO ---
st.title("🦅 Sistema de Gestão - ARO Rio do Sul")

if st.session_state["username"] is None:
    st.subheader("🔑 Área de Acesso")
    
    # Campo de login simples para identificação
    usuario_input = st.text_input("Digite seu Nome de Usuário / Identificação:")
    
    if st.button("Entrar no Painel", use_container_width=True):
        if usuario_input.strip() == "Junior Rebelo":
            st.session_state["username"] = "Junior Rebelo"
            st.session_state["user_role"] = "master"
            st.success("Bem-vindo de volta, Junior! Acesso Master concedido.")
            st.rerun()
        elif usuario_input.strip() != "":
            st.session_state["username"] = usuario_input.strip()
            st.session_state["user_role"] = "leitura"
            st.info(f"Acesso concedido como {usuario_input.strip()} (Modo Leitura).")
            st.rerun()
        else:
            st.warning("Por favor, digite um nome de usuário válido.")

else:
    # --- 3. PAINEL PRINCIPAL APÓS LOGIN ---
    st.sidebar.markdown(f"👤 **Usuário:** {st.session_state['username']}")
    st.sidebar.markdown(f"🛡️ **Nível:** {st.session_state['user_role'].upper()}")
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state["username"] = None
        st.session_state["user_role"] = None
        st.rerun()

    st.markdown(f"### 👋 Olá, {st.session_state['username']}!")
    st.write("Utilize o menu lateral do Streamlit para navegar entre as páginas de **Sócios** e **Finanças**.")
    
    # Recursos exclusivos da Página Inicial para o perfil Master
    if st.session_state["user_role"] == "master":
        st.write("---")
        st.markdown("### 🛠️ Painel Administrativo Geral")
        
        # Botão de download do relatório financeiro consolidado
        dados_txt = gerar_relatorio_texto()
        st.download_button(
            label="📥 Baixar Relatório Financeiro Geral",
            data=dados_txt,
            file_name="relatorio_financeiro_aro.txt",
            mime="text/plain",
            use_container_width=True
        )

