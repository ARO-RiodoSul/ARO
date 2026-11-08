import streamlit st
import pandas as pd
import os

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Sócios - Painel ARO", page_icon="👥", layout="wide")

# --- TRAVA DE SEGURANÇA POR CATEGORIA DE USUÁRIO ---
if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

# Título do Módulo
st.title("👥 Cadastro de Sócios - ARO Rio do Sul")

is_master = st.session_state.get("user_role") == "master"

# CARREGAMENTO INTELIGENTE: Começa com apenas 1 linha se o arquivo estiver em branco
if "dados_socios_internos" not in st.session_state:
    df_carregado = pd.DataFrame()
    if os.path.exists("./backup_socios.csv"):
        try:
            df_carregado = pd.read_csv("./backup_socios.csv")
        except:
            pass
            
    # Se o arquivo não existir, estiver vazio ou tiver apenas cabeçalhos, cria exatamente 1 linha inicial
    if df_carregado.empty or len(df_carregado) == 0:
        df_carregado = pd.DataFrame([{"Número": 1, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"}])
    
    st.session_state["dados_socios_internos"] = df_carregado

df_socios = st.session_state["dados_socios_internos"]

# Garante o tipo numérico limpo para a sequência
if not df_socios.empty:
    df_socios["Número"] = pd.to_numeric(df_socios["Número"], errors='coerce').fillna(1).astype(int)

st.markdown("### 📊 Listagem de Sócios Cadastrados")

if is_master:
    # Renderização da tabela dinâmica controlada por linhas crescentes
    df_editado = st.data_editor(
        df_socios,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Número": st.column_config.NumberColumn("Nº", disabled=True, format="%d"),
            "ID": st.column_config.TextColumn("ID ARO"),
            "Nome": st.column_config.TextColumn("Nome Completo"),
            "Telefone": st.column_config.TextColumn("Telefone/Contato"),
            "CPF": st.column_config.TextColumn("CPF"),
            "CTF": st.column_config.TextColumn("CTF IBAMA"),
            "Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo", "Pendente"], default="Ativo")
        },
        disabled=False,
        use_container_width=True,
        key="editor_socios_master"
    )
    
    if not df_editado.equals(df_socios):
        # Recalcula estritamente a sequência correta 1, 2, 3, 4... baseado no número total de linhas
        df_editado["Número"] = list(range(1, len(df_editado) + 1))
        
        st.session_state["dados_socios_internos"] = df_editado
        try:
            df_editado.to_csv("./backup_socios.csv", index=False)
        except:
            pass
        st.rerun()

else:
    # Modo de visualização limpa para a diretoria, removendo registros de teste vazios
    df_leitura = df_socios[df_socios["Nome"].get(0, "") != ""] if "Nome" in df_socios.columns else df_socios
    if df_leitura.empty:
        st.info("Nenhum sócio registrado no momento.")
    else:
        st.dataframe(
            df_leitura,
            hide_index=True,
            column_config={
                "Número": "Nº",
                "ID": "ID ARO",
                "Nome": "Nome Completo",
                "Telefone": "Telefone/Contato",
                "CPF": "CPF",
                "CTF": "CTF IBAMA",
                "Status": "Status"
            },
            use_container_width=True
        )
