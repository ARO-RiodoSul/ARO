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
socio_vinculado = "Administração" if is_admin else usuarios_dinamicos.get(usuario_logado, {}).get("socio_vinculado", usuario_logado)

ARQUIVO_CONFIRMADOS = "inscricoes_confirmadas.pkl"
ARQUIVO_PENDENTES = "inscricoes_pendentes.pkl"
ARQUIVO_EVENTO = "status_evento.pkl"

def carregar_dados_fisicos():
    if os.path.exists(ARQUIVO_CONFIRMADOS):
        with open(ARQUIVO_CONFIRMADOS, "rb") as f: st.session_state["dados_torneios_internos"] = pickle.load(f)
    else: st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])

    if os.path.exists(ARQUIVO_PENDENTES):
        with open(ARQUIVO_PENDENTES, "rb") as f: st.session_state["inscricoes_pendentes_aro"] = pickle.load(f)
    else: st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])

    st.session_state["torneio_ativo_data"] = pickle.load(open(ARQUIVO_EVENTO, "rb")) if os.path.exists(ARQUIVO_EVENTO) else None

def salvar_dados_fisicos():
    pickle.dump(st.session_state["dados_torneios_internos"], open(ARQUIVO_CONFIRMADOS, "wb"))
    pickle.dump(st.session_state["inscricoes_pendentes_aro"], open(ARQUIVO_PENDENTES, "wb"))
    if st.session_state["torneio_ativo_data"] is not None:
        pickle.dump(st.session_state["torneio_ativo_data"], open(ARQUIVO_EVENTO, "wb"))
    elif os.path.exists(ARQUIVO_EVENTO): os.remove(ARQUIVO_EVENTO)

carregar_dados_fisicos()
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
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
    for i, esp in enumerate(especies_validas): cols[i].metric(label=esp, value=str(contagem[esp]))
    st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

def sortear_estaca(especie):
    ocupadas = []
    if not df_inscritos_atual.empty and "Estaca" in df_inscritos_atual.columns:
        df_esp = df_inscritos_atual[df_inscritos_atual["Espécie"] == especie]
        ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
    lim = 50 if especie in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if especie in ["Canário", "Azulão"] else 5)
    livres = [x for x in range(1, lim + 1) if x not in ocupadas]
    return random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else lim + 1)

if is_admin and torneio_data is not None and not df_pendentes_atual.empty:
    st.write("---")
    st.markdown("### 📩 Inscrições Pendentes de Aprovação")
    for idx, row in df_pendentes_atual.iterrows():
        with st.container():
            c_inf, c_b1, c_b2 = st.columns([4, 1, 1])
            c_inf.write(f"👤 **{row['Proprietário']}** | 🦜 {row['Nome da Ave']} ({row['Espécie']}) | 🏷️ {row['Anilha']}")
            if c_b1.button("✅ Aprovar", key=f"ap_{idx}", use_container_width=True):
                estaca = sortear_estaca(row["Espécie"])
                nova_c = pd.DataFrame([{"Proprietário": row["Proprietário"], "Nome da Ave": row["Nome da Ave"], "Espécie": row["Espécie"], "Anilha": row["Anilha"], "Estaca": int(estaca), "Valor": row["Valor"], "Clube": row.get("Clube", "Outro")}])
                st.session_state["dados_torneios_internos"] = pd.concat([df_inscritos_atual, nova_c], ignore_index=True)
                st.session_state["inscricoes_pendentes_aro"] = df_pendentes_atual.drop(idx).reset_index(drop=True)
                salvar_dados_fisicos(); st.success("Aprovada!"); st.rerun()
            if c_b2.button("❌ Recusar", key=f"re_{idx}", use_container_width=True):
                st.session_state["inscricoes_pendentes_aro"] = df_pendentes_atual.drop(idx).reset_index(drop=True)
                salvar_dados_fisicos(); st.warning("Recusada!"); st.rerun()

if torneio_data is not None:
    st.write("---")
    st.markdown("### 📋 Minhas Inscrições")
    lista_status = []
    if not df_pendentes_atual.empty:
        for _, r in df_pendentes_atual[df_pendentes_atual["Proprietário"] == socio_vinculado].iterrows():
            lista_status.append({"Ave": r["Nome da Ave"], "Espécie": r["Espécie"], "Anilha": r["Anilha"], "Estaca": "⏳ Aguardando...", "Status": "Fila de Aprovação"})
    if not df_inscritos_atual.empty:
        for _, r in df_inscritos_atual[df_inscritos_atual["Proprietário"] == socio_vinculado].iterrows():
            lista_status.append({"Ave": r["Nome da Ave"], "Espécie": r["Espécie"], "Anilha": r["Anilha"], "Estaca": str(int(r["Estaca"])), "Status": "✅ Confirmado"})
    if not lista_status: st.caption("Nenhuma ave cadastrada por você.")
    else: st.dataframe(pd.DataFrame(lista_status), hide_index=True, use_container_width=True)

    st.write("---")
    st.markdown("### 📝 Solicitar Inscrição de Ave")
    df_plantel = st.session_state.get("dados_aves_sistema", pd.DataFrame())
    df_disp = df_plantel if is_admin else (df_plantel[df_plantel["Proprietário"] == socio_vinculado] if not df_plantel.empty else pd.DataFrame())
    if df_disp.empty: st.warning("⚠️ Nenhuma ave cadastrada no seu plantel.")
    else:
        with st.form("form_sol_insc", clear_on_submit=False):
            lista_opcoes = [f"{r['Nome da Ave']} ({r['Espécie']}) - Anilha: {r['Anilha']} | Dono: {r['Proprietário']}" for _, r in df_disp.iterrows()]
            ave_sel = st.selectbox("Selecione a Ave:", lista_opcoes)
            is_socio = st.selectbox("Sócio da ARO?", ["Sim", "Não"])
            if st.form_submit_button("Enviar Solicitação", use_container_width=True):
                ave_obj = df_disp.iloc[lista_opcoes.index(ave_sel)]
                nova_s = pd.DataFrame([{"Proprietário": ave_obj["Proprietário"], "Nome da Ave": ave_obj["Nome da Ave"], "Espécie": ave_obj["Espécie"], "Anilha": ave_obj["Anilha"], "Valor": 25.0 if is_socio == "Sim" else 35.0, "Clube": "ARO" if is_socio == "Sim" else "Outro"}])
                st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_s], ignore_index=True)
                salvar_dados_fisicos(); st.success("🎯 Solicitado!"); st.rerun()

    st.write("---")
    st.markdown("### 🏆 Competidores Confirmados por Categoria")
    abas = st.tabs(especies_validas)
    for i, esp in enumerate(especies_validas):
        with abas[i]:
            df_f = df_inscritos_atual[df_inscritos_atual["Espécie"] == esp] if not df_inscritos_atual.empty else pd.DataFrame()
            if df_f.empty: st.caption("Sem competidores confirmados.")
            else: st.dataframe(df_f.sort_values(by="Estaca"), hide_index=True, column_config={"Estaca": st.column_config.NumberColumn("Estaca", format="%d"), "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f")}, use_container_width=True)

def gerar_pdf_fichas_canvas(df_inscritos, data_torneio):
    buf = io.BytesIO()
    canvas_obj = canvas.Canvas(buf, pagesize=A4)
    data_str = data_torneio.strftime('%d/%m/%Y') if data_torneio else ""
    m_x, m_y, f_w, f_h = 0.5 * cm, 0.8 * cm, 10.0 * cm, 7.0 * cm
    for idx, r in df_inscritos.reset_index(drop=True).iterrows():
        pos = idx % 8
        if pos == 0 and idx > 0: canvas_obj.showPage()
        x = m_x + ((pos % 2) * f_w)
        y = m_y + ((3 - (pos // 2)) * f_h)
        clube_ficha = "ARO" if str(r.get("Clube", "")).upper() == "ARO" else "Outro"
        v_str = "R$ 25,00" if clube_ficha == "ARO" else "R$ 35,00"
        est_str = str(int(r['Estaca'])) if 'Estaca' in r and not pd.isna(r['Estaca']) else 'N/A'
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.rect(x, y, f_w, f_h, stroke=1, fill=0)
        canvas_obj.line(x, y + 5.3*cm, x + f_w, y + 5.3*cm)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawCentredString(x + 5.0*cm, y + 5.8*cm, "ARO - RIO DO SUL")
        canvas_obj.setFont("Helvetica-Bold", 11)
        canvas_obj.drawString(x + 0.4*cm, y + 4.5*cm, f"DATA: {data_str}")
        canvas_obj.setFont("Helvetica-Bold", 13)
        canvas_obj.drawString(x + 5.8*cm, y + 4.5*cm, f"ESTACA: {est_str}")
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(x + 0.4*cm, y + 3.5*cm, f"PROPRIETÁRIO: {str(r['Proprietário']).upper()[:32]}")
        canvas_obj.drawString(x + 0.4*cm, y + 2.6*cm, f"AVE: {str(r['Nome da Ave']).upper()[:22]}")
        canvas_obj.drawString(x + 0.4*cm, y + 1.8*cm, f"ESPÉCIE: {str(r['Espécie']).upper()}")
        canvas_obj.drawString(x + 0.4*cm, y + 1.0*cm, f"CLUBE: {clube_ficha}")
        canvas_obj.drawString(x + 0.4*cm, y + 0.3*cm, f"ANILHA: {str(r['Anilha']).upper()}")
        canvas_obj.setFont("Helvetica-Bold", 12)
