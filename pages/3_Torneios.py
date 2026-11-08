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

# Inicialização segura dos bancos de dados locais em memória
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

# Puxa os dados atualizados em tempo real antes de desenhar a tela
df_inscritos_atual = st.session_state["dados_torneios_internos"]
df_pendentes_atual = st.session_state["inscricoes_pendentes_aro"]

st.markdown("### 📊 Estatísticas (Confirmadas)")
contagem = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
cols = st.columns(6)
for i, esp in enumerate(especies_validas): 
    cols[i].metric(label=esp, value=str(contagem[esp]))
st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

# --- FILA DE APROVAÇÃO (EXCLUSIVO ADMIN / MASTER / DIRETORIA) ---
if is_admin:
    st.write("---")
    st.markdown("### 📩 Inscrições Pendentes de Aprovação")
    if df_pendentes_atual.empty:
        st.caption("Nenhuma solicitação pendente no momento.")
    else:
        for idx, row in df_pendentes_atual.iterrows():
            with st.container():
                c_inf, c_b1, c_b2 = st.columns([4, 1, 1])
                c_inf.write(f"👤 **{row['Proprietário']}** | 🦜 {row['Nome da Ave']} ({row['Espécie']}) | 🏷️ {row['Anilha']}")
                
                if c_b1.button("✅ Aprovar", key=f"ap_{idx}", use_container_width=True):
                    ocupadas = []
                    if not df_inscritos_atual.empty:
                        df_esp = df_inscritos_atual[df_inscritos_atual["Espécie"] == row["Espécie"]]
                        if "Estaca" in df_esp.columns: 
                            ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
                    
                    lim = 50 if row["Espécie"] in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if row["Espécie"] in ["Canário", "Azulão"] else 5)
                    livres = [x for x in range(1, lim + 1) if x not in ocupadas]
                    sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else lim + 1)
                    
                    nova_c = pd.DataFrame([{"Proprietário": row["Proprietário"], "Nome da Ave": row["Nome da Ave"], "Espécie": row["Espécie"], "Anilha": row["Anilha"], "Estaca": int(sorteio), "Valor": row["Valor"], "Clube": row["Clube"]}])
                    st.session_state["dados_torneios_internos"] = pd.concat([df_inscritos_atual, nova_c], ignore_index=True)
                    st.session_state["inscricoes_pendentes_aro"] = df_pendentes_atual.drop(idx).reset_index(drop=True)
                    st.success("Inscrição aprovada com sucesso!")
                    st.rerun()
                    
                if c_b2.button("❌ Recusar", key=f"re_{idx}", use_container_width=True):
                    st.session_state["inscricoes_pendentes_aro"] = df_pendentes_atual.drop(idx).reset_index(drop=True)
                    st.warning("Inscrição recusada!")
                    st.rerun()

# --- NOVA SEÇÃO: MINHAS INSCRIÇÕES (ACOMPANHAMENTO DO SÓCIO) ---
st.write("---")
st.markdown("### 📋 Minhas Inscrições")
lista_status = []

if not df_pendentes_atual.empty:
    filtrado_p = df_pendentes_atual[df_pendentes_atual["Proprietário"] == socio_vinculado]
    for _, r in filtrado_p.iterrows():
        lista_status.append({"Ave": r["Nome da Ave"], "Espécie": r["Espécie"], "Anilha": r["Anilha"], "Estaca": "⏳ Aguardando...", "Status": "Fila de Aprovação"})

if not df_inscritos_atual.empty:
    filtrado_i = df_inscritos_atual[df_inscritos_atual["Proprietário"] == socio_vinculado]
    for _, r in filtrado_i.iterrows():
        lista_status.append({"Ave": r["Nome da Ave"], "Espécie": r["Espécie"], "Anilha": r["Anilha"], "Estaca": str(int(r["Estaca"])), "Status": "✅ Inscrito Confirmado"})

if len(lista_status) == 0:
    st.caption("Você não possui nenhuma ave cadastrada neste torneio até o momento.")
else:
    st.dataframe(pd.DataFrame(lista_status), hide_index=True, use_container_width=True)

# --- FORMULÁRIO DE INSCRIÇÃO ---
st.write("---")
st.markdown("### 📝 Solicitar Inscrição de Ave")
df_plantel = st.session_state.get("dados_aves_sistema", pd.DataFrame())
df_disp = df_plantel if is_admin else (df_plantel[df_plantel["Proprietário"] == socio_vinculado] if not df_plantel.empty else pd.DataFrame())

if df_disp.empty:
    st.warning("⚠️ Nenhuma ave encontrada no seu plantel. Cadastre as aves antes na aba correspondente.")
else:
    with st.form("form_sol_insc", clear_on_submit=False):
        lista_opcoes = [f"{r['Nome da Ave']} ({r['Espécie']}) - Anilha: {r['Anilha']} | Dono: {r['Proprietário']}" for _, r in df_disp.iterrows()]
        ave_sel = st.selectbox("Selecione a Ave:", lista_opcoes)
        is_socio_clube = st.selectbox("Sócio da ARO?", ["Sim", "Não"])
        
        if st.form_submit_button("Enviar Solicitação", use_container_width=True):
            idx_sel = lista_opcoes.index(ave_sel)
            ave_obj = df_disp.iloc[idx_sel]
            
            nova_s = pd.DataFrame([{
                "Proprietário": ave_obj["Proprietário"], 
                "Nome da Ave": ave_obj["Nome da Ave"], 
                "Espécie": ave_obj["Espécie"], 
                "Anilha": ave_obj["Anilha"], 
                "Valor": 25.0 if is_socio_clube == "Sim" else 35.0, 
                "Clube": "ARO" if is_socio_clube == "Sim" else "Outro"
            }])
            
            st.session_state["inscricoes_pendentes_aro"] = pd.concat([st.session_state["inscricoes_pendentes_aro"], nova_s], ignore_index=True)
            st.success("🎯 Solicitado com sucesso! Verifique a tabela acima.")
            st.rerun()

# --- VISUALIZAÇÃO GERAL DE CONFIRMADOS (ABAS) ---
st.write("---")
st.markdown("### 🏆 Competidores Confirmados por Categoria")
abas = st.tabs(especies_validas)
for i, esp in enumerate(especies_validas):
    with abas[i]:
        df_f = df_inscritos_atual[df_inscritos_atual["Espécie"] == esp] if not df_inscritos_atual.empty else pd.DataFrame()
        if df_f.empty: 
            st.caption("Sem competidores validados nesta espécie.")
        else: 
            st.dataframe(df_f.sort_values(by="Estaca"), hide_index=True, column_config={"Estaca": st.column_config.NumberColumn("Estaca", format="%d"), "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f")}, use_container_width=True)

# --- SISTEMA DE BACKUPS (ADMIN/MASTER) ---
if is_admin:
    st.write("---")
    st.markdown("### 💾 Central de Backups (.PKL)")
    cb1, cb2 = st.columns(2)
    with cb1:
        dados_e = {"confirmados": df_inscritos_atual, "pendentes": df_pendentes_atual, "data": st.session_state["data_torneio_aro"]}
        st.download_button("📥 Baixar Arquivo de Inscrições", data=pickle.dumps(dados_e), file_name="backup_torneio_aro.pkl", mime="application/octet-stream", use_container_width=True)
    with cb2:
        arq_t = st.file_uploader("Subir Backup Existente:", type=["pkl"], key="up_t")
        if arq_t is not None:
            try:
                dados_i = pickle.load(arq_t)
                if st.button("🔄 Confirmar Restauração Global", use_container_width=True, type="primary"):
                    st.session_state["dados_torneios_internos"] = dados_i["confirmados"]
                    st.session_state["inscricoes_pendentes_aro"] = dados_i["pendentes"]
                    st.session_state["data_torneio_aro"] = dados_i["data"]
                    st.success("Sistema restaurado!"); st.rerun()
            except: 
                st.error("Arquivo inválido.")

# --- EXCLUSÃO INDIVIDUAL DE INSCRITOS (EXCLUSIVO MASTER) ---
if role_atual == "master" and not df_inscritos_atual.empty:
    st.write("---")
    st.markdown("### 🗑️ Cancelamento Manual de Inscrição")
    opc = [f"[{r['Espécie']}] Estaca {r['Estaca']} - {r['Nome da Ave']} ({r['Proprietário']})" for _, r in df_inscritos_atual.iterrows()]
    sel = st.selectbox("Escolha a ave registrada para remover:", opc)
    if st.checkbox("Li e aceito excluir permanentemente esta vaga"):
        if st.button("❌ Remover do Torneio", use_container_width=True):
            idx_del = opc.index(sel)
            st.session_state["dados_torneios_internos"] = df_inscritos_atual.drop(df_inscritos_atual.index[idx_del]).reset_index(drop=True)
            st.success("Registro apagado!")
            st.rerun()
