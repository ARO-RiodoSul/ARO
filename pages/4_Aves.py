import streamlit as st
import pandas as pd
import io
import pickle

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Minhas Aves - Painel ARO", page_icon="🦅", layout="wide")

# --- TRAVA DE SEGURANÇA GLOBAL ---
if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

if st.session_state.get("user_role") == "visitante":
    st.error("🔒 Acesso Restrito! Visitantes não possuem permissão para gerenciar plantéis de aves.")
    st.stop()

st.title("🦅 Plantel de Aves - ARO Rio do Sul")

role_atual = st.session_state.get("user_role")
usuario_logado = st.session_state.get("username")

# Identificar qual Sócio Oficial está usando o app (puxando do login dinâmico)
if role_atual in ["master", "diretoria"]:
    socio_vinculado = "Administração"
else:
    usuarios_dinamicos = st.session_state.get("banco_usuarios_dinamicos", {})
    socio_vinculado = usuarios_dinamicos.get(usuario_logado, {}).get("socio_vinculado", usuario_logado)

# CARREGAMENTO INTELIGENTE INTEGRADO NA MEMÓRIA VIVA (100% Livre de bloqueios de arquivos)
if "dados_aves_sistema" not in st.session_state:
    st.session_state["dados_aves_sistema"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha"])

df_aves = st.session_state["dados_aves_sistema"]

# --- 1. FORMULÁRIO DE CADASTRO DE AVE ---
st.markdown("### 📝 Cadastrar Nova Ave no Plantel")
st.caption(f"Conectado como: **{usuario_logado}** | Vínculo de Proprietário: **{socio_vinculado}**")

with st.form("form_cadastro_ave", clear_on_submit=True):
    col_f1, col_f2, col_f3 = st.columns(3)
    nome_passaro = col_f1.text_input("Nome do Pássaro/Ave:")
    especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
    especie_selecionada = col_f2.selectbox("Espécie:", especies_validas)
    anilha_passaro = col_f3.text_input("Número da Anilha:")
        
    proprietario_final = socio_vinculado
    if role_atual in ["master", "diretoria"]:
        df_socios = st.session_state.get("dados_socios_internos", pd.DataFrame())
        lista_proprietarios = [usuario_logado]
        if not df_socios.empty and "Nome" in df_socios.columns:
            lista_proprietarios.extend(df_socios["Nome"].dropna().str.strip().tolist())
        proprietario_final = st.selectbox("Cadastrar em nome de qual Proprietário?", [x for x in lista_proprietarios if x != ""])

    if st.form_submit_button("Salvar Ave no Plantel", use_container_width=True):
        if nome_passaro.strip() and anilha_passaro.strip():
            if not df_aves.empty and anilha_passaro.strip() in df_aves["Anilha"].astype(str).str.strip().tolist():
                st.error("⚠️ Esta anilha já está cadastrada no sistema!")
            else:
                nova_ave = pd.DataFrame([{
                    "Proprietário": proprietario_final,
                    "Nome da Ave": nome_passaro.strip(),
                    "Espécie": especie_selecionada,
                    "Anilha": anilha_passaro.strip()
                }])
                st.session_state["dados_aves_sistema"] = pd.concat([df_aves, nova_ave], ignore_index=True)
                st.success(f"Ave '{nome_passaro.strip()}' adicionada com sucesso na memória viva!")
                st.rerun()
        else:
            st.error("Por favor, preencha o Nome e a Anilha da ave.")

st.write("---")

# --- 2. EXIBIÇÃO E GERENCIAMENTO DO PLANTEL ---
st.markdown("### 🏆 Aves Registradas")

if role_atual in ["master", "diretoria"]:
    st.info("🛡️ Modo Administração: Você possui visão global de todas as aves cadastradas no clube.")
    if df_aves.empty:
        st.caption("Nenhuma ave cadastrada no clube até o momento.")
    else:
        st.dataframe(df_aves.sort_values(by="Proprietário"), hide_index=True, use_container_width=True)
else:
    df_filtrado_socio = df_aves[df_aves["Proprietário"] == socio_vinculado] if not df_aves.empty else pd.DataFrame()
    if df_filtrado_socio.empty:
        st.info("Você ainda não possui nenhuma ave cadastrada no seu plantel.")
    else:
        st.dataframe(df_filtrado_socio, hide_index=True, use_container_width=True)

st.write("---")

# --- 3. CENTRAL DE BACKUP DE AVES FIXA (PROTEÇÃO CONTRA REBOOTS) ---
st.markdown("### 💾 Central de Backups do Plantel")
col_aback_1, col_aback_2 = st.columns(2)

with col_aback_1:
    st.markdown("**Exportar Dados Atuais**")
    buffer_aves_pkl = pickle.dumps(st.session_state["dados_aves_sistema"])
    st.download_button(
        label="📥 Fazer Backup de Todas as Aves (Formato .PKL)",
        data=buffer_aves_pkl,
        file_name="backup_aves_aro.pkl",
        mime="application/octet-stream",
        use_container_width=True
    )
    
with col_aback_2:
    if role_atual in ["master", "diretoria"]:
        st.markdown("**Importar Arquivo de Backup**")
        arquivo_aves_enviado = st.file_uploader("Selecione o arquivo 'backup_aves_aro.pkl' para restaurar o plantel:", type=["pkl"], key="uploader_aves_din")
        if arquivo_aves_enviado is not None:
            try:
                dados_aves_importados = pickle.load(arquivo_aves_enviado)
                if isinstance(dados_aves_importados, pd.DataFrame):
                    if st.button("🔄 Confirmar Restauração de Aves", use_container_width=True, type="primary"):
                        st.session_state["dados_aves_sistema"] = dados_aves_importados
                        st.success("Plantel de aves restaurado com sucesso!")
                        st.rerun()
            except:
                pass

# --- 4. EXCLUSÃO DE AVE COMPATÍVEL COM CELULAR ---
if not df_aves.empty:
    df_excluir_opcoes = df_aves if role_atual in ["master", "diretoria"] else df_aves[df_aves["Proprietário"] == socio_vinculado]
    if not df_excluir_opcoes.empty:
        st.write("---")
        st.markdown("### 🗑️ Remover Ave do Plantel")
        lista_opcoes_del = [f"[{r['Espécie']}] {r['Nome da Ave']} - Anilha: {r['Anilha']} ({r['Proprietário']})" for _, r in df_excluir_opcoes.iterrows()]
        ave_para_deletar_txt = st.selectbox("Selecione a ave que deseja remover:", lista_opcoes_del, key="del_ave_box")
        if st.checkbox("⚠️ Confirmo que desejo apagar esta ave do meu plantel", key="check_del_ave"):
            if st.button("❌ Excluir Ave Selecionada", use_container_width=True):
                posicao = lista_opcoes_del.index(ave_para_deletar_txt)
                indice_original = df_excluir_opcoes.index[posicao]
                st.session_state["dados_aves_sistema"] = df_aves.drop(indice_original).reset_index(drop=True)
                st.success("Ave removida do plantel!")
                st.rerun()
