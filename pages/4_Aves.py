import streamlit as st
import pandas as pd
import os
import pickle

# CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Minhas Aves - Painel ARO", page_icon="🦅", layout="wide")

# --- TRAVA DE SEGURANÇA GLOBAL ---
# Garante que Sócios, Diretoria e Master acessem, mas bloqueia Visitantes deslogados ou convidados
if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

if st.session_state.get("user_role") == "visitante":
    st.error("🔒 Acesso Restrito! Visitantes não possuem permissão para gerenciar plantéis de aves.")
    st.stop()

st.title("🦅 Plantel de Aves - ARO Rio do Sul")

# Identificar o perfil e o vínculo do usuário atual
role_atual = st.session_state.get("user_role")
usuario_logado = st.session_state.get("username")

# Identificar qual Sócio Oficial está usando o app (puxando do login dinâmico)
# Se for Master ou Diretoria, define como 'Administração' para controle geral
if role_atual in ["master", "diretoria"]:
    socio_vinculado = "Administração"
else:
    # Busca o vínculo correto mapeado no app.py
    usuarios_dinamicos = st.session_state.get("banco_usuarios_dinamicos", {})
    socio_vinculado = usuarios_dinamicos.get(usuario_logado, {}).get("socio_vinculado", usuario_logado)

# --- CARREGAMENTO DO BANCO DE DADOS DE AVES ---
if "dados_aves_sistema" not in st.session_state:
    if os.path.exists("./backup_aves.pkl"):
        try:
            st.session_state["dados_aves_sistema"] = pickle.load(open("./backup_aves.pkl", "rb"))
        except:
            st.session_state["dados_aves_sistema"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha"])
    else:
        st.session_state["dados_aves_sistema"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha"])

df_aves = st.session_state["dados_aves_sistema"]

# --- 1. FORMULÁRIO DE CADASTRO DE AVE ---
st.markdown("### 📝 Cadastrar Nova Ave no Plantel")
st.caption(f"Conectado como: **{usuario_logado}** | Vínculo de Proprietário: **{socio_vinculado}**")

with st.form("form_cadastro_ave", clear_on_submit=True):
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        nome_passaro = st.text_input("Nome do Pássaro/Ave:")
    with col_f2:
        especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
        especie_selecionada = st.selectbox("Espécie:", especies_validas)
    with col_f3:
        anilha_passaro = st.text_input("Número da Anilha:")
        
    # Se for Master ou Diretoria cadastrando, permite digitar o nome de qualquer proprietário
    proprietario_final = socio_vinculado
    if role_atual in ["master", "diretoria"]:
        st.write("")
        df_socios = st.session_state.get("dados_socios_internos", pd.DataFrame())
        lista_proprietarios = [usuario_logado]
        if not df_socios.empty and "Nome" in df_socios.columns:
            lista_proprietarios.extend(df_socios["Nome"].dropna().str.strip().tolist())
        lista_proprietarios = [x for x in lista_proprietarios if x != ""]
        proprietario_final = st.selectbox("Cadastrar em nome de qual Proprietário?", lista_proprietarios)

    if st.form_submit_button("Salvar Ave no Plantel", use_container_width=True):
        if nome_passaro.strip() and anilha_passaro.strip():
            # Verificar se a anilha já existe para evitar duplicidade
            if not df_aves.empty and anilha_passaro.strip() in df_aves["Anilha"].astype(str).tolist():
                st.error("⚠️ Esta anilha já está cadastrada no sistema!")
            else:
                nova_ave = pd.DataFrame([{
                    "Proprietário": proprietario_final,
                    "Nome da Ave": nome_passaro.strip(),
                    "Espécie": especie_selecionada,
                    "Anilha": anilha_passaro.strip()
                }])
                
                st.session_state["dados_aves_sistema"] = pd.concat([df_aves, nova_ave], ignore_index=True)
                try:
                    with open("./backup_aves.pkl", "wb") as f:
                        pickle.dump(st.session_state["dados_aves_sistema"], f)
                    st.success(f"Ave '{nome_passaro.strip()}' cadastrada com sucesso!")
                    st.rerun()
                except:
                    st.error("Erro ao gravar arquivo físico de backup de aves.")
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
        # Exibe todas as aves do clube ordenadas por proprietário
        st.dataframe(df_aves.sort_values(by="Proprietário"), hide_index=True, use_container_width=True)
else:
    # FILTRO DE SÓCIO: Exibe apenas as aves onde o Proprietário for igual ao Sócio Vinculado dele
    df_filtrado_socio = df_aves[df_aves["Proprietário"] == socio_vinculado]
    
    if df_filtrado_socio.empty:
        st.info("Você ainda não possui nenhuma ave cadastrada no seu plantel.")
    else:
        st.dataframe(df_filtrado_socio, hide_index=True, use_container_width=True)

# --- 3. EXCLUSÃO DE AVE COMPATÍVEL COM CELULAR (EXCLUSIVO PROPRIETÁRIO OU MASTER) ---
if not df_aves.empty:
    # Filtra o que o usuário atual tem direito de excluir
    if role_atual in ["master", "diretoria"]:
        df_excluir_opcoes = df_aves
    else:
        df_excluir_opcoes = df_aves[df_aves["Proprietário"] == socio_vinculado]
        
    if not df_excluir_opcoes.empty:
        st.write("---")
        st.markdown("### 🗑️ Remover Ave do Plantel")
        
        lista_opcoes_del = []
        for idx, row in df_excluir_opcoes.iterrows():
            lista_opcoes_del.append(f"[{row['Espécie']}] {row['Nome da Ave']} - Anilha: {row['Anilha']} (Proprietário: {row['Proprietário']})")
            
        ave_para_deletar_txt = st.selectbox("Selecione a ave que deseja remover:", lista_opcoes_del, key="del_ave_box")
        confirmar_del_ave = st.checkbox("⚠️ Confirmo que desejo apagar esta ave do meu plantel", key="check_del_ave")
        
        if st.button("❌ Excluir Ave Selecionada", use_container_width=True):
            if confirmar_del_ave:
                posicao = lista_opcoes_del.index(ave_para_deletar_txt)
                indice_original = df_excluir_opcoes.index[posicao]
                
                st.session_state["dados_aves_sistema"] = df_aves.drop(indice_original).reset_index(drop=True)
                try:
                    with open("./backup_aves.pkl", "wb") as f:
                        pickle.dump(st.session_state["dados_aves_sistema"], f)
                    st.success("Ave removida do plantel!")
                    st.rerun()
                except:
                    st.error("Erro ao atualizar arquivo físico.")
            else:
                st.error("Marque o quadrado de confirmação de segurança antes de excluir.")
