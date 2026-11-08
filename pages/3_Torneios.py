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

def salvar_dados_fisicos():
    with open(ARQUIVO_CONFIRMADOS, "wb") as f:
        pickle.dump(st.session_state["dados_torneios_internos"], f)
    with open(ARQUIVO_PENDENTES, "wb") as f:
        pickle.dump(st.session_state["inscricoes_pendentes_aro"], f)

carregar_dados_fisicos()

if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 11, 8)

especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]

if is_admin:
    nova_data = st.date_input("📅 Data do Torneio:", value=st.session_state["data_torneio_aro"], format="DD/MM/YYYY")
    if nova_data != st.session_state["data_torneio_aro"]:
        st.session_state["data_torneio_aro"] = nova_data
        st.rerun()
else:
    st.markdown(f"### 📅 Torneio Dia: {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}")

df_inscritos_atual = st.session_state["dados_torneios_internos"]
df_pendentes_atual = st.session_state["inscricoes_pendentes_aro"]

st.markdown("### 📊 Estatísticas (Confirmadas)")
contagem = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
cols = st.columns(6)
for i, esp in enumerate(especies_validas): 
    cols[i].metric(label=esp, value=str(contagem[esp]))
st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

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
            
            st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_s], ignore_index=True)
            salvar_dados_fisicos()
            st.success("🎯 Solicitado com sucesso!")
            st.rerun()

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

def gerar_pdf_fichas_canvas(df_inscritos, data_torneio):
    buf = io.BytesIO()
    canvas_obj = canvas.Canvas(buf, pagesize=A4)
    data_str = data_torneio.strftime('%d/%m/%Y')
    m_x, m_y, f_w, f_h = 0.5 * cm, 0.8 * cm, 10.0 * cm, 7.0 * cm
    
    for idx, r in df_inscritos.reset_index(drop=True).iterrows():
        pos = idx % 8
        if pos == 0 and idx > 0:
            canvas_obj.showPage()
        col = pos % 2
        lin = 3 - (pos // 2)
        x = m_x + (col * f_w)
        y = m_y + (lin * f_h)
        
        v_str = "R$ 25,00" if str(r.get("Clube", "")).upper() == "ARO" else "R$ 35,00"
        est_str = str(int(r['Estaca'])) if 'Estaca' in r and not pd.isna(r['Estaca']) else 'N/A'
        
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.rect(x, y, f_w, f_h, stroke=1, fill=0)
        canvas_obj.line(x, y + 5.5*cm, x + f_w, y + 5.5*cm)
        canvas_obj.setFont("Helvetica-Bold", 11)
        canvas_obj.drawCentredString(x + 5.0*cm, y + 5.9*cm, "ARO - RIO DO SUL")
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(x + 0.4*cm, y + 4.8*cm, f"Data: {data_str}")
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(x + 6.0*cm, y + 4.8*cm, f"Estaca: {est_str}")
        
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(x + 0.4*cm, y + 3.7*cm, f"Proprietário: {str(r['Proprietário'])[:35]}")
        canvas_obj.drawString(x + 0.4*cm, y + 2.6*cm, f"Ave: {str(r['Nome da Ave'])[:20]}")
        canvas_obj.drawString(x + 0.4*cm, y + 1.5*cm, f"Espécie: {str(r['Espécie'])}")
        canvas_obj.drawString(x + 0.4*cm, y + 0.4*cm, f"Anilha: {str(r['Anilha'])}")
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(x + 6.0*cm, y + 0.4*cm, f"Valor: {v_str}")
        
    canvas_obj.save()
    buf.seek(0)
    return buf

if role_atual == "master":
    st.write("---")
    st.markdown("### ⚙️ Ferramentas Avançadas do Master")
    col_bt1, col_bt2 = st.columns(2)
    
    with col_bt1:
        st.markdown("**🖨️ Impressão de Fichas**")
        if not df_inscritos_atual.empty:
            pdf_pronto = gerar_pdf_fichas_canvas(df_inscritos_atual, st.session_state["data_torneio_aro"])
            st.download_button(label="📥 Imprimir Todas as Fichas (A4 - 10x7cm)", data=pdf_pronto, file_name="fichas_completas_aro.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.caption("Nenhuma ave confirmada para emitir fichas.")
            
    with col_bt2:
        st.markdown("**🚨 Controle de Temporada**")
        if st.checkbox("Habilitar botão para RESETAR o torneio"):
            if st.button("💥 EXCLUIR TORNEIO TODO (ZERAR)", use_container_width=True, type="primary"):
                st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])
                st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])
                salvar_dados_fisicos()
                st.success("Torneio excluído com sucesso!")
                st.rerun()

    # --- INSCRIÇÃO MANUAL RÁPIDA COM SELEÇÃO DE PREÇO DINÂMICO ---
    st.write("---")
    st.markdown("### ➕ Inscrição Manual Rápida")
    with st.form("form_manual_master", clear_on_submit=True):
        m_prop = st.text_input("Nome do Proprietário:")
        m_ave = st.text_input("Nome da Ave:")
        m_esp = st.selectbox("Espécie:", especies_validas)
        m_anilha = st.text_input("Número da Anilha:")
        m_socio = st.selectbox("Sócio da ARO?", ["Sim", "Não"], index=1) # Padrão Não Sócio
        
        if st.form_submit_button("⚡ Inscrever Ave Manualmente", use_container_width=True):
            if m_prop and m_ave and m_anilha:
                ocupadas = []
                if not df_inscritos_atual.empty and "Estaca" in df_inscritos_atual.columns:
                    df_esp = df_inscritos_atual[df_inscritos_atual["Espécie"] == m_esp]
                    ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
                
                lim = 50 if m_esp in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if m_esp in ["Canário", "Azulão"] else 5)
                livres = [x for x in range(1, lim + 1) if x not in ocupadas]
                sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else lim + 1)
                
                nova_m = pd.DataFrame([{
                    "Proprietário": m_prop.strip(),
                    "Nome da Ave": m_ave.strip(),
                    "Espécie": m_esp,
                    "Anilha": m_anilha.strip(),
                    "Estaca": int(sorteio),
                    "Valor": 25.0 if m_socio == "Sim" else 35.0,
                    "Clube": "ARO" if m_socio == "Sim" else "Outro"
                }])
                
                st.session_state["dados_torneios_internos"] = pd.concat([df_inscritos_atual, nova_m], ignore_index=True)
                salvar_dados_fisicos()
                st.success(f"✅ {m_ave} inserido na Estaca {sorteio} com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ Preencha todos os campos para efetuar a inscrição manual.")

    if not df_inscritos_atual.empty:
        st.write("---")
        st.markdown("### 🗑️ Cancelamento Manual Individual")
        opc_lista = [f"[{r['Espécie']}] Estaca {r['Estaca']} - {r['Nome da Ave']} ({r['Proprietário']})" for _, r in df_inscritos_atual.iterrows()]
        ave_remover = st.selectbox("Escolha uma ave para deletar:", opc_lista)
        if st.checkbox("Confirmo a exclusão desta ave isolada"):
            if st.button("❌ Excluir Ave Selecionada", use_container_width=True):
                idx_alvo = opc_lista.index(ave_remover)
                st.session_state["dados_torneios_internos"] = df_inscritos_atual.drop(df_inscritos_atual.index[idx_alvo]).reset_index(drop=True)
                salvar_dados_fisicos()
                st.success("Ave removida com sucesso!")
                st.rerun()
