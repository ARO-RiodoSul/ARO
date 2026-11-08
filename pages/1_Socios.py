import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Sócios - Painel ARO", page_icon="👥", layout="wide")

role_atual = str(st.session_state.get("user_role", "")).strip().lower()
usuario_logado = str(st.session_state.get("username", "")).strip().lower()

# Libera o acesso à página para master, diretoria e admin
if role_atual not in ["master", "diretoria", "admin"] and usuario_logado not in ["master", "admin"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para Master ou Diretoria.")
    st.stop()

st.title("👥 Cadastro de Sócios - ARO Rio do Sul")
is_master = role_atual in ["master", "admin"] or usuario_logado in ["master", "admin"]

# --- BANCO DE DADOS OFICIAL EMBUTIDO EM CÓDIGO (BLINDADO CONTRA REBOOT) ---
@st.cache_data(ttl=3600)
def obter_planilha_fixa_socios():
    dados_oficiais = [
        {"Número": 1, "ID": "25151", "Nome": "Carolina Leandro", "Telefone": "47-996331899", "CPF": "7033276907", "CTF": "5455", "Status": "Ativo"},
        {"Número": 2, "ID": "51515", "Nome": "Pedro Paulo", "Telefone": "47-1252", "CPF": "25255", "CTF": "25255", "Status": "Ativo"},
    ]
    return pd.DataFrame(dados_oficiais)

# CORREÇÃO CHAVE: Inicialização global liberada para qualquer nível de acesso permitido (Master ou Diretoria)
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = obter_planilha_fixa_socios()

df_socios = st.session_state["dados_socios_internos"]

if not df_socios.empty:
    df_socios["Número"] = pd.to_numeric(df_socios["Número"], errors='coerce').fillna(1).astype(int)

if is_master:
    st.markdown("### 📝 Registrar Novo Membro (Sessão Atual)")
    with st.form("form_novo_socio", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f4, col_f5, col_f6 = st.columns(3)
        
        id_aro = col_f1.text_input("ID ARO:")
        nome_socio = col_f2.text_input("Nome Completo:")
        tel_socio = col_f3.text_input("Telefone / Contato:")
        cpf_socio = col_f4.text_input("CPF:")
        ctf_socio = col_f5.text_input("CTF IBAMA:")
        status_socio = col_f6.selectbox("Status Inicial:", ["Ativo", "Inativo", "Pendente"])
        
        if st.form_submit_button("➕ Cadastrar Novo Sócio", use_container_width=True):
            if nome_socio.strip():
                proximo_no = int(df_socios["Número"].max() + 1) if not df_socios.empty else 1
                novo_registro = pd.DataFrame([{
                    "Número": int(proximo_no), "ID": id_aro.strip(), "Nome": nome_socio.strip(),
                    "Telefone": tel_socio.strip(), "CPF": cpf_socio.strip(), "CTF": ctf_socio.strip(), "Status": status_socio
                }])
                st.session_state["dados_socios_internos"] = pd.concat([df_socios, novo_registro], ignore_index=True)
                st.success(f"Sócio '{nome_socio.strip()}' adicionado temporariamente!")
                st.rerun()
            else:
                st.error("Preencha o campo 'Nome Completo'!")

st.write("---")
st.markdown("### 📊 Listagem de Sócios Cadastrados")

# FIX: Removida qualquer trava de nível de acesso para a exibição da tabela principal
if df_socios.empty:
    st.info("Nenhum sócio registrado no sistema até o momento.")
else:
    st.dataframe(
        df_socios.sort_values(by="Número"),
        hide_index=True,
        column_config={
            "Número": st.column_config.NumberColumn("Nº", format="%d"),
            "ID": "ID ARO", 
            "Nome": "Nome Completo", 
            "Telefone": "Telefone/Contato",
            "CPF": "CPF", 
            "CTF": "CTF IBAMA", 
            "Status": "Status"
        },
        use_container_width=True
    )

st.write("---")
st.markdown("### 💾 Central de Backups")
col_back_1, col_back_2 = st.columns(2)

with col_back_1:
    st.markdown("**Exportar Dados Atuais**")
    buffer_csv = io.StringIO()
    df_socios.to_csv(buffer_csv, index=False)
    st.download_button(
        label="📥 Baixar Lista em Planilha (.CSV)",
        data=buffer_csv.getvalue(),
        file_name="backup_socios_aro.csv",
        mime="text/csv",
        use_container_width=True
    )
    
with col_back_2:
    if is_master:
        st.markdown("**Sobrescrever por Cópia Externa**")
        arquivo_enviado = st.file_uploader("Selecione um arquivo CSV para carregar na sessão atual:", type=["csv"], key="uploader_socios")
        if arquivo_enviado is not None:
            try:
                df_importado = pd.read_csv(arquivo_enviado)
                colunas_obrigatorias = ["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"]
                if all(col in df_importado.columns for col in colunas_obrigatorias):
                    if st.button("🔄 Confirmar Carregamento", use_container_width=True, type="primary"):
                        st.session_state["dados_socios_internos"] = df_importado
                        st.success("Dados carregados com sucesso para esta sessão!")
                        st.rerun()
                else:
                    st.error("⚠️ Colunas inválidas.")
            except:
                st.error("Erro ao ler CSV.")

if is_master and not df_socios.empty:
    st.write("---")
    st.markdown("### 🗑️ Remover Membro do Sistema (Sessão Atual)")
    lista_opcoes_del = [f"Nº {r['Número']} - {r['Nome']} (ID: {r['ID']})" for _, r in df_socios.iterrows()]
    socio_para_deletar = st.selectbox("Selecione o sócio que deseja apagar:", lista_opcoes_del)
    confirmar_del_socio = st.checkbox("Confirmo que desejo excluir da visualização")
    
    if st.button("❌ Deletar Sócio Selecionado", use_container_width=True):
        if confirmar_del_socio:
            posicao = lista_opcoes_del.index(socio_para_deletar)
            df_remanescente = df_socios.drop(df_socios.index[posicao]).reset_index(drop=True)
            if not df_remanescente.empty:
                df_remanescente["Número"] = list(range(1, len(df_remanescente) + 1))
            st.session_state["dados_socios_internos"] = df_remanescente
            st.success("Removido com sucesso!")
            st.rerun()
        else:
            st.error("Marque a caixa de confirmação!")
