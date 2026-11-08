import streamlit as st
import pandas as pd
import io, os

st.set_page_config(page_title="Sócios - Painel ARO", page_icon="👥", layout="wide")

if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

st.title("👥 Cadastro de Sócios - ARO Rio do Sul")
is_master = st.session_state.get("user_role") == "master"

# Nome estável do arquivo físico no servidor
ARQUIVO_SOCIOS_FISICO = "backup_socios.csv"

def carregar_socios_disco():
    if os.path.exists(ARQUIVO_SOCIOS_FISICO):
        try:
            df = pd.read_csv(ARQUIVO_SOCIOS_FISICO)
            st.session_state["dados_socios_internos"] = df
        except:
            st.session_state["dados_socios_internos"] = pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])
    else:
        st.session_state["dados_socios_internos"] = pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])

def salvar_socios_disco():
    df_para_salvar = st.session_state["dados_socios_internos"]
    df_para_salvar.to_csv(ARQUIVO_SOCIOS_FISICO, index=False)

# Garante o carregamento do arquivo físico antes de montar a tela
if "dados_socios_internos" not in st.session_state:
    carregar_socios_disco()

df_socios = st.session_state["dados_socios_internos"]

if not df_socios.empty:
    df_socios["Número"] = pd.to_numeric(df_socios["Número"], errors='coerce').fillna(1).astype(int)

if is_master:
    st.markdown("### 📝 Registrar Novo Membro")
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
                salvar_socios_disco()  # Força gravação física instantânea
                st.success(f"Sucesso! Sócio '{nome_socio.strip()}' cadastrado com o Nº {proximo_no}!")
                st.rerun()
            else:
                st.error("Por favor, preencha ao menos o campo 'Nome Completo'!")
st.write("---")
st.markdown("### 📊 Listagem de Sócios Cadastrados")

if df_socios.empty:
    st.info("Nenhum sócio registrado no sistema até o momento.")
else:
    st.dataframe(
        df_socios.sort_values(by="Número"),
        hide_index=True,
        column_config={
            "Número": st.column_config.NumberColumn("Nº", format="%d"),
            "ID": "ID ARO", "Nome": "Nome Completo", "Telefone": "Telefone/Contato",
            "CPF": "CPF", "CTF": "CTF IBAMA", "Status": "Status"
        },
        use_container_width=True
    )

st.write("---")
st.markdown("### 💾 Central de Backups e Restauração")
col_back_1, col_back_2 = st.columns(2)

with col_back_1:
    st.markdown("**Exportar Dados Atuais**")
    buffer_csv = io.StringIO()
    df_socios.to_csv(buffer_csv, index=False)
    st.download_button(
        label="📥 Fazer Backup da Lista de Sócios (Formato .CSV)",
        data=buffer_csv.getvalue(),
        file_name="backup_socios_aro.csv",
        mime="text/csv",
        use_container_width=True
    )
    
with col_back_2:
    if is_master:
        st.markdown("**Importar Arquivo de Backup**")
        arquivo_enviado = st.file_uploader("Selecione o arquivo 'backup_socios_aro.csv' salvo:", type=["csv"], key="uploader_socios")
        if arquivo_enviado is not None:
            try:
                df_importado = pd.read_csv(arquivo_enviado)
                colunas_obrigatorias = ["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"]
                
                if all(col in df_importado.columns for col in colunas_obrigatorias):
                    if st.button("🔄 Confirmar Restauração do Banco de Dados", use_container_width=True, type="primary"):
                        st.session_state["dados_socios_internos"] = df_importado
                        salvar_socios_disco()  # Salva o arquivo importado fisicamente no disco do servidor
                        st.success("Banco de dados de sócios restaurado e sincronizado com o servidor!")
                        st.rerun()
                else:
                    st.error("⚠️ O arquivo enviado não possui as colunas oficiais do sistema da ARO.")
            except:
                st.error("Erro ao ler o arquivo CSV.")

if is_master and not df_socios.empty:
    st.write("---")
    st.markdown("### 🗑️ Remover Membro do Sistema")
    lista_opcoes_del = [f"Nº {r['Número']} - {r['Nome']} (ID: {r['ID']})" for _, r in df_socios.iterrows()]
    socio_para_deletar = st.selectbox("Selecione o sócio que deseja apagar:", lista_opcoes_del)
    confirmar_del_socio = st.checkbox("💥 Confirmo que desejo excluir permanentemente este cadastro")
    
    if st.button("❌ Deletar Sócio Selecionado", use_container_width=True):
        if confirmar_del_socio:
            posicao = lista_opcoes_del.index(socio_para_deletar)
            st.session_state["dados_socios_internos"] = df_socios.drop(df_socios.index[posicao]).reset_index(drop=True)
            
            if not st.session_state["dados_socios_internos"].empty:
                st.session_state["dados_socios_internos"]["Número"] = list(range(1, len(st.session_state["dados_socios_internos"]) + 1))
                
            salvar_socios_disco()  # Atualiza o arquivo físico após a remoção
            st.success("Membro excluído do sistema com sucesso!")
            st.rerun()
        else:
            st.error("Marque o quadrado de confirmação de segurança antes de excluir!")
