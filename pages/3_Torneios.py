import streamlit as st
import pandas as pd
import datetime, random, io, pickle, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

st.set_page_config(page_title="Torneios - ARO", page_icon="🦅", layout="wide")

if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

st.title("🦅 Gestão de Torneios - ARO Rio do Sul")

role_atual = str(st.session_state.get("user_role", "")).strip().lower()
usuario_logado = str(st.session_state.get("username", "")).strip().lower()
is_admin = role_atual in ["master", "diretoria", "admin"] or usuario_logado in ["master", "admin"]

usuarios_dinamicos = st.session_state.get("banco_usuarios_dinamicos", {})
socio_vinculado = "Administração" if is_admin else usuarios_dinamicos.get(st.session_state.get("username"), {}).get("socio_vinculado", st.session_state.get("username"))

ARQUIVO_CONFIRMADOS = "inscricoes_confirmadas.pkl"
ARQUIVO_PENDENTES = "inscricoes_pendentes.pkl"
ARQUIVO_EVENTO = "status_evento.pkl"

def carregar_dados_fisicos():
    if os.path.exists(ARQUIVO_CONFIRMADOS):
        with open(ARQUIVO_CONFIRMADOS, "rb") as f:
            st.session_state["dados_torneios_internos"] = pickle.load(f)
    else:
        st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])

    if os.path.exists(ARQUIVO_PENDENTES):
        with open(ARQUIVO_PENDENTES, "rb") as f:
            st.session_state["inscricoes_pendentes_aro"] = pickle.load(f)
    else:
        st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])

    if os.path.exists(ARQUIVO_EVENTO):
        with open(ARQUIVO_EVENTO, "rb") as f:
            st.session_state["torneio_ativo_data"] = pickle.load(f)
    else:
        st.session_state["torneio_ativo_data"] = None

def salvar_dados_fisicos():
    with open(ARQUIVO_CONFIRMADOS, "wb") as f:
        pickle.dump(st.session_state["dados_torneios_internos"], f)
    with open(ARQUIVO_PENDENTES, "wb") as f:
        pickle.dump(st.session_state["inscricoes_pendentes_aro"], f)
    if st.session_state["torneio_ativo_data"] is not None:
        with open(ARQUIVO_EVENTO, "wb") as f:
            pickle.dump(st.session_state["torneio_ativo_data"], f)
    elif os.path.exists(ARQUIVO_EVENTO):
        os.remove(ARQUIVO_EVENTO)

carregar_dados_fisicos()
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]

# --- VERIFICAÇÃO DE EVENTO ATIVO ---
torneio_data = st.session_state["torneio_ativo_data"]

if torneio_data is None:
    st.warning("⚠️ Nenhum torneio cadastrado no momento.")
else:
    st.markdown(f"### 📅 Torneio Ativo para o Dia: **{torneio_data.strftime('%d/%m/%Y')}**")

df_inscritos_atual = st.session_state["dados_torneios_internos"]
df_pendentes_atual = st.session_state["inscricoes_pendentes_aro"]

if torneio_data is not None:
    st.markdown("### 📊 Estatísticas (Confirmadas)")
    contagem = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
    cols = st.columns(6)
    for i, esp in enumerate(especies_validas): 
        cols[i].metric(label=esp, value=str(contagem[esp]))
    st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

# =========================================================================================
# 🌐 FLUXO EXCLUSIVO: VISITANTE / CONVIDADO
# =========================================================================================
if role_atual == "visitante":
    if torneio_data is None:
        st.info("💡 Quando um torneio for cadastrado pela diretoria, o formulário de inscrições para visitantes aparecerá aqui automaticamente.")
    else:
        st.write("---")
        st.markdown("### 📝 Inscrição para não sócio")
        
        with st.form("form_visitante_exclusivo", clear_on_submit=True):
            v_proprietario = st.text_input("Proprietario:")
            v_ave = st.text_input("Ave:")
            v_especie = st.selectbox("Espécie:", especies_validas)
            v_anilha = st.text_input("Anilha:")
            v_clube = st.text_input("Clube:")
            
            st.markdown("**Valor da Inscrição:** `R$ 35,00`")
            
            if st.form_submit_button("Solicitar Inscrição", use_container_width=True):
                if not v_proprietario.strip() or not v_ave.strip() or not v_anilha.strip() or not v_clube.strip():
                    st.error("❌ Por favor, preencha todos os campos do formulário.")
                else:
                    nova_solicitacao_v = pd.DataFrame([{
                        "Proprietário": v_proprietario.strip(),
                        "Nome da Ave": v_ave.strip(),
                        "Espécie": v_especie,
                        "Anilha": v_anilha.strip(),
                        "Valor": 35.0,
                        "Clube": v_clube.strip()
                    }])
                    
                    st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_solicitacao_v], ignore_index=True)
                    salvar_dados_fisicos()
                    
                    st.markdown("---")
                    st.success("✅ **Inscrição solicitada, aguarde a aprovação de um membro da diretoria ARO**")
                    st.markdown("---")
                    st.balloons()
                    
    st.stop()  # Garante o bloqueio completo do restante da página para o visitante
# =========================================================================================
# 🔒 FLUXO NORMAL: MASTER, DIRETORIA E SÓCIOS CLUBE (INALTERADO)
# =========================================================================================

if is_admin and torneio_data is not None:
    st.write("---")
    st.markdown("### 📩 Inscrições Pendentes de Aprovação")
    if df_pendentes_atual.empty:
        st.caption("Nenhuma solicitação pendente no momento.")
    else:
        for idx, row in df_pendentes_atual.iterrows():
            with st.container():
                c_inf, c_b1, c_b2 = st.columns([4, 1, 1])
                c_inf.write(f"👤 **{row['Proprietário']}** | 🦜 {row['Nome da Ave']} ({row['Espécie']}) | 🏷️ {row['Anilha']} | 🏢 Clube: {row.get('Clube', 'Outro')}")
                
                if c_b1.button("✅ Aprovar", key=f"ap_{idx}", use_container_width=True):
                    ocupadas = []
                    if not df_inscritos_atual.empty and "Estaca" in df_inscritos_atual.columns:
                        df_esp = df_inscritos_atual[df_inscritos_atual["Espécie"] == row["Espécie"]]
                        ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
                    
                    lim = 50 if row["Espécie"] in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if row["Espécie"] in ["Canário", "Azulão"] else 5)
                    livres = [x for x in range(1, lim + 1) if x not in ocupadas]
                    sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else lim + 1)
                    
                    nova_c = pd.DataFrame([{"Proprietário": row["Proprietário"], "Nome da Ave": row["Nome da Ave"], "Espécie": row["Espécie"], "Anilha": row["Anilha"], "Estaca": int(sorteio), "Valor": row["Valor"], "Clube": row.get("Clube", "Outro")}])
                    st.session_state["dados_torneios_internos"] = pd.concat([df_inscritos_atual, nova_c], ignore_index=True)
                    st.session_state["inscricoes_pendentes_aro"] = df_pendentes_atual.drop(idx).reset_index(drop=True)
                    salvar_dados_fisicos()
                    st.success("Aprovada!")
                    st.rerun()
                    
                if c_b2.button("❌ Recusar", key=f"re_{idx}", use_container_width=True):
                    st.session_state["inscricoes_pendentes_aro"] = df_pendentes_atual.drop(idx).reset_index(drop=True)
                    salvar_dados_fisicos()
                    st.warning("Recusada!")
                    st.rerun()

if torneio_data is not None:
    # --- EXIBIÇÃO DE TODAS AS INSCRIÇÕES SE FOR ADMIN/MASTER ---
    if is_admin:
        st.write("---")
        st.markdown("### 🏆 Todas as Inscrições Confirmadas no Torneio")
        if df_inscritos_atual.empty:
            st.caption("Nenhum participante inscrito ou confirmado até o momento.")
        else:
            # Organiza os dados para exibição clara na planilha
            df_exibicao_master = df_inscritos_atual.copy()
            df_exibicao_master["Estaca"] = pd.to_numeric(df_exibicao_master["Estaca"], errors="coerce").fillna(0).astype(int)
            df_exibicao_master = df_exibicao_master.sort_values(by=["Espécie", "Estaca"]).reset_index(drop=True)
            st.dataframe(df_exibicao_master, hide_index=True, use_container_width=True)
    
    # --- VISÃO HISTÓRICA DO SÓCIO COMUM ---
    else:
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
            st.caption("Você não possui nenhuma ave cadastrada neste torneio.")
        else: 
            st.dataframe(pd.DataFrame(lista_status), hide_index=True, use_container_width=True)

    # --- FORMULÁRIO DE SOLICITAÇÃO NORMAL (SÓCIOS E ADMINS) ---
    st.write("---")
    st.markdown("### 📝 Solicitar Inscrição de Ave")
    df_plantel = st.session_state.get("dados_aves_sistema", pd.DataFrame())
    df_disp = df_plantel if is_admin else (df_plantel[df_plantel["Proprietário"] == socio_vinculado] if not df_plantel.empty else pd.DataFrame())
    
    if df_disp.empty: 
        st.warning("⚠️ Nenhuma ave encontrada no plantel para realizar inscrições.")
    else:
        with st.form("form_sol_insc", clear_on_submit=False):
            lista_opcoes = [f"{r['Nome da Ave']} ({r['Espécie']}) - Anilha: {r['Anilha']} | Dono: {r['Proprietário']}" for _, r in df_disp.iterrows()]
            ave_sel = st.selectbox("Selecione a Ave:", lista_opcoes)
            is_socio_clube = st.selectbox("Sócio da ARO?", ["Sim", "Não"])
            
            if st.form_submit_button("Enviar Solicitação", use_container_width=True):
                ave_obj = df_disp.iloc[lista_opcoes.index(ave_sel)]
                nova_s = pd.DataFrame([{
                    "Proprietário": ave_obj["Proprietário"], 
                    "Nome da Ave": ave_obj["Nome da Ave"], 
                    "Espécie": ave_obj["Espécie"], 
                    "Anilha": ave_obj["Anilha"], 
                    "Valor": 25.0 if is_socio_clube == "Sim" else 35.0, 
                    "Clube": "ARO" if is_socio_clube == "Sim" else "Outro"
                }])
                st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_s], ignore_index=True)
                salvar_dados_fisicos()
                st.success("Solicitação enviada com sucesso!")
                st.rerun()
