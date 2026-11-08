import streamlit as st
import pandas as pd
import datetime, random, io, pickle

st.set_page_config(page_title="Torneios - ARO", page_icon="🦅", layout="wide")

if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

st.title("🦅 Gestão de Torneios - ARO Rio do Sul")
role_atual = st.session_state.get("user_role")
usuario_logado = st.session_state.get("username")
is_admin = role_atual in ["master", "diretoria"]

usuarios_dinamicos = st.session_state.get("banco_usuarios_dinamicos", {})
socio_vinculado = "Administração" if is_admin else usuarios_dinamicos.get(usuario_logado, {}).get("socio_vinculado", usuario_logado)

# Inicialização segura das chaves na memória
if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 11, 8)
if "dados_torneios_internos" not in st.session_state:
    st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])
if "inscricoes_pendentes_aro" not in st.session_state:
    st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])

especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]

if is_admin:
    nova_data = st.date_input("📅 Data do Torneio:", value=st.session_state["data_torneio_aro"], format="DD/MM/YYYY")
    if nova_data != st.session_state["data_torneio_aro"]:
        st.session_state["data_torneio_aro"] = nova_data
        st.rerun()
else:
    st.markdown(f"### 📅 Torneio Dia: {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}")

st.markdown("### 📊 Estatísticas (Confirmadas)")
df_inscritos_atual = st.session_state["dados_torneios_internos"]
contagem = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
cols = st.columns(6)
for i, esp in enumerate(especies_validas): 
    cols[i].metric(label=esp, value=str(contagem[esp]))
st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

# --- FILA DE APROVAÇÃO (LENDO DIRETO DO SESSION STATE REALTIME) ---
if is_admin:
    st.write("---")
    st.markdown("### 📩 Inscrições Pendentes de Aprovação")
    
    # Buscando os dados em tempo real da memória global
    dados_pendentes_live = st.session_state["inscricoes_pendentes_aro"]
    
    if dados_pendentes_live.empty:
        st.caption("Nenhuma solicitação pendente no momento.")
    else:
        for idx, row in dados_pendentes_live.iterrows():
            with st.container():
                c_inf, c_b1, c_b2 = st.columns([4, 1, 1])
                c_inf.write(f"👤 **{row['Proprietário']}** | 🦜 {row['Nome da Ave']} ({row['Espécie']}) | 🏷️ {row['Anilha']}")
                
                if c_b1.button("✅ Aprovar", key=f"ap_{idx}", use_container_width=True):
                    df_inscritos = st.session_state["dados_torneios_internos"]
                    ocupadas = []
                    if not df_inscritos.empty:
                        df_esp = df_inscritos[df_inscritos["Espécie"] == row["Espécie"]]
                        if "Estaca" in df_esp.columns: 
                            ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
                    
                    lim = 50 if row["Espécie"] in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if row["Espécie"] in ["Canário", "Azulão"] else 5)
                    livres = [x for x in range(1, lim + 1) if x not in ocupadas]
                    sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else lim + 1)
                    
                    nova_c = pd.DataFrame([{"Proprietário": row["Proprietário"], "Nome da Ave": row["Nome da Ave"], "Espécie": row["Espécie"], "Anilha": row["Anilha"], "Estaca": int(sorteio), "Valor": row["Valor"], "Clube": row["Clube"]}])
                    
                    # Atualização segura das duas tabelas
                    st.session_state["dados_torneios_internos"] = pd.concat([df_inscritos, nova_c], ignore_index=True)
                    st.session_state["inscricoes_pendentes_aro"] = dados_pendentes_live.drop(idx).reset_index(drop=True)
                    st.success("Aprovada!")
                    st.rerun()
                    
                if c_b2.button("❌ Recusar", key=f"re_{idx}", use_container_width=True):
                    st.session_state["inscricoes_pendentes_aro"] = dados_pendentes_live.drop(idx).reset_index(drop=True)
                    st.warning("Recusada!")
                    st.rerun()

# --- FUNÇÃO CALLBACK DO FORMULÁRIO ---
def processar_solicitacao_inscricao(df_dados_origem, opcoes_lista):
    selecionado = st.session_state.get("input_ave_selecionada")
    is_socio = st.session_state.get("input_is_socio_clube")
    
    if selecionado and selecionado in opcoes_lista:
        idx_real = opcoes_lista.index(selecionado)
        ave_obj = df_dados_origem.iloc[idx_real]
        
        nova_s = pd.DataFrame([{
            "Proprietário": ave_obj["Proprietário"], 
            "Nome da Ave": ave_obj["Nome da Ave"], 
            "Espécie": ave_obj["Espécie"], 
            "Anilha": ave_obj["Anilha"], 
            "Valor": 25.0 if is_socio == "Sim" else 35.0, 
            "Clube": "ARO" if is_socio == "Sim" else "Outro"
        }])
        
        st.session_state["inscricoes_pendentes_aro"] = pd.concat([st.session_state["inscricoes_pendentes_aro"], nova_s], ignore_index=True)
        st.session_state["sucesso_envio_torneio"] = True

# --- FORMULÁRIO DE INSCRIÇÃO ---
st.write("---")
st.markdown("### 📝 Solicitar Inscrição de Ave")
df_plantel = st.session_state.get("dados_aves_sistema", pd.DataFrame())
df_disp = df_plantel if is_admin else (df_plantel[df_plantel["Proprietário"] == socio_vinculado] if not df_plantel.empty else pd.DataFrame())

if df_disp.empty:
    st.warning("⚠️ Nenhuma ave cadastrada no seu plantel. Cadastre suas aves na página 'Minhas Aves' primeiro!")
else:
    if st.session_state.get("sucesso_envio_torneio", False):
        st.success("🎯 Enviada com sucesso! Aguarde a aprovação da administração.")
        st.session_state["sucesso_envio_torneio"] = False
        
    with st.form("form_sol_insc", clear_on_submit=True):
        lista_opcoes = [f"{r['Nome da Ave']} ({r['Espécie']}) - Anilha: {r['Anilha']} | Dono: {r['Proprietário']}" for _, r in df_disp.iterrows()]
        
        st.selectbox("Selecione a Ave:", lista_opcoes, key="input_ave_selecionada")
        st.selectbox("Sócio da ARO?", ["Sim", "Não"], key="input_is_socio_clube")
        
        st.form_submit_button(
            "Enviar Solicitação", 
            use_container_width=True, 
            on_click=processar_solicitacao_inscricao, 
            args=(df_disp, lista_opcoes)
        )

# --- CONFIRMADOS EM ABAS ---
st.write("---")
st.markdown("### 🏆 Competidores Confirmados")
df_inscritos_print = st.session_state["dados_torneios_internos"]
abas = st.tabs(especies_validas)
for i, esp in enumerate(especies_validas):
    with abas[i]:
        df_f = df_inscritos_print[df_inscritos_print["Espécie"] == esp] if not df_inscritos_print.empty else pd.DataFrame()
        if df_f.empty: 
            st.caption("Nenhum pássaro confirmado.")
        else: 
            st.dataframe(df_f.sort_values(by="Estaca"), hide_index=True, column_config={"Estaca": st.column_config.NumberColumn("Estaca", format="%d"), "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f")}, use_container_width=True)

# --- BACKUP E CONFIGURAÇÕES ADMINISTRATIVAS (EXCLUSIVO MASTER/DIRETORIA) ---
if is_admin:
    st.write("---")
    st.markdown("### 💾 Central de Backups")
    cb1, cb2 = st.columns(2)
    with cb1:
        st.markdown("**Exportar Inscrições**")
        dados_e = {"confirmados": st.session_state["dados_torneios_internos"], "pendentes": st.session_state["inscricoes_pendentes_aro"], "data": st.session_state["data_torneio_aro"]}
        st.download_button("📥 Exportar Backup do Torneio (.PKL)", data=pickle.dumps(dados_e), file_name="backup_torneio_aro.pkl", mime="application/octet-stream", use_container_width=True)
    with cb2:
        st.markdown("**Importar Backup**")
        arq_t = st.file_uploader("Importar backup do torneio:", type=["pkl"], key="up_t")
        if arq_t is not None:
            try:
                dados_i = pickle.load(arq_t)
                if "confirmados" in dados_i and "pendentes" in dados_i:
                    if st.button("🔄 Confirmar Restauração", use_container_width=True, type="primary"):
                        st.session_state["dados_torneios_internos"] = dados_i["confirmados"]
                        st.session_state["inscricoes_pendentes_aro"] = dados_i["pendentes"]
                        st.session_state["data_torneio_aro"] = dados_i["data"]
                        st.success("Restaurado!")
                        st.rerun()
            except: 
                pass

# --- EXCLUSÃO INDIVIDUAL E RESET (EXCLUSIVO MASTER) ---
if role_atual == "master":
    df_inscritos_del = st.session_state["dados_torneios_internos"]
    if not df_inscritos_del.empty:
        st.write("---")
        st.markdown("### 🗑️ Cancelar Inscrição")
        opc = [f"[{r['Espécie']}] Estaca {r['Estaca']} - {r['Nome da Ave']} ({r['Proprietário']})" for _, r in df_inscritos_del.iterrows()]
        sel = st.selectbox("Selecione a ave para remover:", opc)
        if st.checkbox("Confirmar cancelamento da ave"):
            if st.button("❌ Deletar Ave do Torneio", use_container_width=True):
                idx_del = opc.index(sel)
                st.session_state["dados_torneios_internos"] = df_inscritos_del.drop(df_inscritos_del.index[idx_del]).reset_index(drop=True)
                st.success("Inscrição cancelada com sucesso!")
                st.rerun()
