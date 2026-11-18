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
        with open(ARQUIVO_CONFIRMADOS, "rb") as f: st.session_state["dados_torneios_internos"] = pickle.load(f)
    else: st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])

    if os.path.exists(ARQUIVO_PENDENTES):
        with open(ARQUIVO_PENDENTES, "rb") as f: st.session_state["inscricoes_pendentes_aro"] = pickle.load(f)
    else: st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])

    if os.path.exists(ARQUIVO_EVENTO):
        with open(ARQUIVO_EVENTO, "rb") as f: st.session_state["torneio_ativo_data"] = pickle.load(f)
    else: st.session_state["torneio_ativo_data"] = None

def salvar_dados_fisicos():
    with open(ARQUIVO_CONFIRMADOS, "wb") as f: pickle.dump(st.session_state["dados_torneios_internos"], f)
    with open(ARQUIVO_PENDENTES, "wb") as f: pickle.dump(st.session_state["inscricoes_pendentes_aro"], f)
    if st.session_state["torneio_ativo_data"] is not None:
        with open(ARQUIVO_EVENTO, "wb") as f: pickle.dump(st.session_state["torneio_ativo_data"], f)
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

# =========================================================================================
# 🌐 ÁREA DO VISITANTE: ESTATÍSTICAS + SOLICITAR INSCRIÇÃO + CONSULTA DE COMPETIDORES
# =========================================================================================
if role_atual == "visitante":
    if torneio_data is None:
        st.warning("⚠️ Nenhum torneio cadastrado no momento.")
    else:
        st.markdown("### 📊 Estatísticas (Confirmadas)")
        contagem = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
        cols = st.columns(6)
        for i, esp in enumerate(especies_validas): 
            cols[i].metric(label=esp, value=str(contagem[esp]))
        st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

        if "sucesso_inscricao_visitante" not in st.session_state:
            st.session_state["sucesso_inscricao_visitante"] = False

        st.write("---")
        
        if st.session_state["sucesso_inscricao_visitante"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.success("### 🎉 INSCRIÇÃO SOLICITADA COM SUCESSO!")
            st.markdown(
                """
                <div style='background-color: #DEF7EC; padding: 20px; border-radius: 8px; border-left: 5px solid #0E9F6E;'>
                    <h3 style='color: #03543F; margin-top: 0;'>🚨 Atenção, Competidor!</h3>
                    <p style='color: #046C4E; font-size: 16px; font-weight: bold;'>
                        Sua solicitação foi salva. Assim que um membro da diretoria da ARO aprovar, 
                        o seu nome e o número da sua estaca aparecerão na tabela de competidores abaixo!
                    </p>
                </div>
                <br>
                """, 
                unsafe_allow_html=True
            )
            st.balloons()
            if st.button("➕ Realizar Outra Inscrição", use_container_width=True, type="primary"):
                st.session_state["sucesso_inscricao_visitante"] = False
                st.rerun()
                
        else:
            st.markdown("### 📝 Solicitar Inscrição")
            v_categoria_socio = st.radio(
                "Selecione sua categoria:",
                ["Sócio ARO", "Não Sócio"],
                horizontal=True,
                key="v_cat_socio_radio"
            )
            valor_calc_v = 25.0 if v_categoria_socio == "Sócio ARO" else 35.0
            clube_calc_v = "ARO" if v_categoria_socio == "Sócio ARO" else "Outro"

            with st.form("form_solicitacao_visitante_visual", clear_on_submit=True):
                v_proprietario = st.text_input("Proprietário:")
                v_ave = st.text_input("Ave:")
                v_especie = st.selectbox("Espécie:", especies_validas)
                v_anilha = st.text_input("Anilha:")
                
                st.markdown(f"**Valor da Inscrição ({v_categoria_socio}):** `R$ {valor_calc_v:.2f}`".replace(".", ","))
                
                if st.form_submit_button("Solicitar Inscrição", use_container_width=True):
                    if not v_proprietario.strip() or not v_ave.strip() or not v_anilha.strip():
                        st.error("❌ Por favor, preencha todos os campos do formulário antes de enviar.")
                    else:
                        nova_solicitacao_v = pd.DataFrame([{
                            "Proprietário": v_proprietario.strip(),
                            "Nome da Ave": v_ave.strip(),
                            "Espécie": v_especie,
                            "Anilha": v_anilha.strip(),
                            "Valor": valor_calc_v,
                            "Clube": clube_calc_v
                        }])
                        st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_solicitacao_v], ignore_index=True)
                        salvar_dados_fisicos()
                        st.session_state["sucesso_inscricao_visitante"] = True
                        st.rerun()

        st.write("---")
        st.markdown("### 🏆 Competidores Confirmados por Categoria")
        abas_v = st.tabs(especies_validas)
        for i, esp in enumerate(especies_validas):
            with abas_v[i]:
                df_f = df_inscritos_atual[df_inscritos_atual["Espécie"] == esp].copy() if not df_inscritos_atual.empty else pd.DataFrame()
                if df_f.empty:
                    st.caption(f"Nenhum competidor confirmado para {esp} até o momento.")
                else:
                    df_f["Estaca"] = pd.to_numeric(df_f["Estaca"], errors="coerce").fillna(0).astype(int)
                    df_f = df_f.sort_values(by="Estaca").reset_index(drop=True)
                    st.dataframe(df_f[["Estaca", "Proprietário", "Nome da Ave", "Anilha", "Clube"]], hide_index=True, use_container_width=True)
                    
    st.stop()
# =========================================================================================
# 🔐 ÁREA LOGADA (SÓCIOS, DIRETORIA E MASTER)
# =========================================================================================
if torneio_data is not None:
    st.markdown("### 📊 Estatísticas (Confirmadas)")
    contagem = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
    cols = st.columns(6)
    for i, esp in enumerate(especies_validas):
        cols[i].metric(label=esp, value=str(contagem[esp]))
    st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

    if role_atual == "master":
        if st.button("📸 Gerar Imagem das Estatísticas (para WhatsApp)", use_container_width=True):
            from PIL import Image, ImageDraw, ImageFont
            import reportlab
            
            dados_whats = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
            total_gaiolas_whats = sum(dados_whats.values())
            
            img_w, img_h = 800, 720
            imagem_stats = Image.new("RGB", (img_w, img_h), "#FFFFFF")
            draw = ImageDraw.Draw(imagem_stats)
            draw.rectangle([(10, 10), (img_w - 10, img_h - 10)], outline="#1E3A8A", width=4)
            
            rl_dir = os.path.dirname(reportlab.__file__)
            fonte_bold = os.path.join(rl_dir, "fonts", "VeraBd.ttf")
            f_titulo = ImageFont.truetype(fonte_bold, 34) if os.path.exists(fonte_bold) else ImageFont.load_default()
            f_sub = ImageFont.truetype(fonte_bold, 24) if os.path.exists(fonte_bold) else ImageFont.load_default()
            f_item = ImageFont.truetype(fonte_bold, 26) if os.path.exists(fonte_bold) else ImageFont.load_default()
            
            draw.text((img_w // 2, 50), "ARO RIO DO SUL", fill="#1E3A8A", font=f_titulo, anchor="mm")
            draw.text((img_w // 2, 95), f"Estatísticas Confirmadas • {torneio_data.strftime('%d/%m/%Y')}", fill="#374151", font=f_sub, anchor="mm")
            draw.line([(45, 130), (img_w - 45, 130)], fill="#1E3A8A", width=2)
            
            y_posicao = 175
            for esp, qtd in dados_whats.items():
                draw.text((65, y_posicao), f"{esp.upper()}", fill="#1F2937", font=f_item, anchor="lm")
                draw.text((img_w - 65, y_posicao), f"{qtd}", fill="#1E3A8A", font=f_item, anchor="rm")
                draw.line([(65, y_posicao + 30), (img_w - 65, y_posicao + 30)], fill="#E5E7EB", width=2)
                y_posicao += 60
                
            draw.rectangle([(45, 570), (img_w - 45, 655)], fill="#EBF5FF", outline="#3B82F6", width=2)
            draw.text((img_w // 2, 612), f"TOTAL DE GAIOLAS CONFIRMADAS: {total_gaiolas_whats}", fill="#1E3A8A", font=f_item, anchor="mm")
            
            buf_whats = io.BytesIO()
            imagem_stats.save(buf_whats, format="PNG")
            buf_whats.seek(0)
            
            st.image(buf_whats, width=380)
            st.download_button(
                label="📥 Baixar Imagem das Estatísticas para o Celular / PC",
                data=buf_whats,
                file_name="estatisticas_torneio_aro.png",
                mime="image/png",
                use_container_width=True,
                type="primary"
            )

if is_admin and torneio_data is not None:
    st.write("---")
    st.markdown("### 📩 Inscrições Pendentes de Aprovação")
    if df_pendentes_atual.empty:
        st.caption("Nenhuma solicitação pendente no momento.")
    else:
        for idx, row in df_pendentes_atual.iterrows():
            with st.container():
                c_inf, c_b1, c_b2 = st.columns([4, 1, 1])
                c_inf.write(f"👤 **{row['Proprietário']}** | 🦜 {row['Nome da Ave']} ({row['Espécie']}) | 🏷️ {row['Anilha']} | 🏛️ {row.get('Clube', 'Outro')}")
                if c_b1.button("✅ Aprovar", key=f"ap_{idx}", use_container_width=True):
                    ocupadas = []
                    if not df_inscritos_atual.empty and "Estaca" in df_inscritos_atual.columns:
                        df_esp = df_inscritos_atual[df_inscritos_atual["Espécie"] == row["Espécie"]]
                        ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
                    lim = 50 if row["Espécie"] in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if row["Espécie"] in ["Canário", "Azulão"] else 5)
                    livres = [x for x in range(1, lim + 1) if x not in ocupadas]
                    sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else lim + 1)
                    nova_c = pd.DataFrame([{
                        "Proprietário": row["Proprietário"],
                        "Nome da Ave": row["Nome da Ave"],
                        "Espécie": row["Espécie"],
                        "Anilha": row["Anilha"],
                        "Estaca": int(sorteio),
                        "Valor": row["Valor"],
                        "Clube": row.get("Clube", "Outro")
                    }])
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

    st.write("---")
    st.markdown("### 📝 Solicitar Inscrição (Sócio ARO)")
    if st.session_state.get("sucesso_inscricao_socio", False):
        st.success("✅ Solicitação enviada! Aguarde a aprovação da diretoria.")
        if st.button("➕ Nova Solicitação", key="btn_nova_sol_socio"):
            st.session_state["sucesso_inscricao_socio"] = False
            st.rerun()
    else:
        with st.form("form_sol_insc_simplificado", clear_on_submit=True):
            s_proprietario = st.text_input("Nome do Proprietário:", value="" if is_admin else str(socio_vinculado))
            s_ave = st.text_input("Nome da Ave:")
            s_especie = st.selectbox("Espécie:", especies_validas)
            s_anilha = st.text_input("Número da Anilha:")
            
            st.text_input("Categoria / Clube:", value="Sócio ARO (R$ 25,00)", disabled=True)
            
            if st.form_submit_button("Solicitar Inscrição", use_container_width=True):
                if not s_proprietario.strip() or not s_ave.strip() or not s_anilha.strip():
                    st.error("❌ Por favor, preencha todos os campos antes de enviar.")
                else:
                    nova_s = pd.DataFrame([{
                        "Proprietário": s_proprietario.strip(),
                        "Nome da Ave": s_ave.strip(),
                        "Espécie": s_especie,
                        "Anilha": s_anilha.strip(),
                        "Valor": 25.0,
                        "Clube": "ARO"
                    }])
                    st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_s], ignore_index=True)
                    salvar_dados_fisicos()
                    st.session_state["sucesso_inscricao_socio"] = True
                    st.rerun()
    st.write("---")
    st.markdown("### 🏆 Competidores Confirmados por Categoria")
    abas = st.tabs(especies_validas)
    for i, esp in enumerate(especies_validas):
        with abas[i]:
            df_f = df_inscritos_atual[df_inscritos_atual["Espécie"] == esp] if not df_inscritos_atual.empty else pd.DataFrame()
            if df_f.empty:
                st.caption("Sem competidores confirmados.")
            else:
                st.dataframe(
                    df_f.sort_values(by="Estaca"),
                    hide_index=True,
                    column_config={
                        "Estaca": st.column_config.NumberColumn("Estaca", format="%d"),
                        "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f")
                    },
                    use_container_width=True
                )
def gerar_pdf_fichas_canvas(df_inscritos, data_torneio):
    buf = io.BytesIO()
    canvas_obj = canvas.Canvas(buf, pagesize=A4)
    largura_a4, altura_a4 = A4
    data_str = data_torneio.strftime('%d/%m/%Y') if data_torneio else ""

    # 10,1 cm x 3,2 cm garante 0,4 cm de margem lateral segura na folha A4 (21,0 cm)
    f_w = 10.1 * cm
    f_h = 3.2 * cm

    m_x = (largura_a4 - (2 * f_w)) / 2.0
    m_y = (altura_a4 - (8 * f_h)) / 2.0

    for idx, r in df_inscritos.reset_index(drop=True).iterrows():
        pos = idx % 16
        if pos == 0 and idx > 0:
            canvas_obj.showPage()

        col = pos % 2
        lin = 7 - (pos // 2)
        x = m_x + (col * f_w)
        y = m_y + (lin * f_h)

        clube_ficha = "ARO" if str(r.get("Clube", "")).upper() == "ARO" else "Outro"
        v_str = "R$ 25,00" if clube_ficha == "ARO" else "R$ 35,00"
        est_str = str(int(r['Estaca'])) if 'Estaca' in r and not pd.isna(r['Estaca']) else 'N/A'
        especie_str = str(r.get('Espécie', '')).upper()
        prop_str = str(r.get('Proprietário', '')).upper()[:32]
        anel_str = str(r.get('Anilha', '')).upper()[:28]
        ave_str = str(r.get('Nome da Ave', '')).upper()[:17]

        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setFillColor(colors.black)

        # Borda externa da etiqueta
        canvas_obj.setLineWidth(0.6)
        canvas_obj.rect(x, y, f_w, f_h, stroke=1, fill=0)

        pad_x = 0.22 * cm

        # 1. TOPO: Espécie automática + Valor
        y_esp = y + 2.75 * cm
        canvas_obj.setFont("Helvetica-Bold", 8.5)
        canvas_obj.drawString(x + pad_x, y_esp, f"Espécie: {especie_str}")
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.drawRightString(x + f_w - pad_x, y_esp, f"Valor: {v_str}")

        # 2. LINHA PROPRIETÁRIO
        y_prop = y + 2.15 * cm
        canvas_obj.setFont("Helvetica-BoldOblique", 10)
        lbl_prop = "Proprietário: "
        w_lbl_prop = canvas_obj.stringWidth(lbl_prop, "Helvetica-BoldOblique", 10)
        canvas_obj.drawString(x + pad_x, y_prop, lbl_prop)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(x + pad_x + w_lbl_prop, y_prop - 0.05 * cm, x + f_w - pad_x, y_prop - 0.05 * cm)
        canvas_obj.setFont("Helvetica-Bold", 9.5)
        canvas_obj.drawString(x + pad_x + w_lbl_prop + 0.1 * cm, y_prop, prop_str)

        # 3. LINHA Nº. ANEL COMPLETO
        y_anel = y + 1.55 * cm
        canvas_obj.setFont("Helvetica-BoldOblique", 9.5)
        lbl_anel = "Nº. Anel Completo: "
        w_lbl_anel = canvas_obj.stringWidth(lbl_anel, "Helvetica-BoldOblique", 9.5)
        canvas_obj.drawString(x + pad_x, y_anel, lbl_anel)
        canvas_obj.line(x + pad_x + w_lbl_anel, y_anel - 0.05 * cm, x + f_w - pad_x, y_anel - 0.05 * cm)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawString(x + pad_x + w_lbl_anel + 0.1 * cm, y_anel, anel_str)

        # 4. TABELA INFERIOR (4 colunas)
        tab_x = x + pad_x
        tab_w = f_w - (2 * pad_x)
        tab_y_bot = y + 0.18 * cm
        tab_h_dados = 0.62 * cm
        tab_h_cab = 0.42 * cm
        tab_y_mid = tab_y_bot + tab_h_dados
        tab_y_top = tab_y_mid + tab_h_cab

        c1_w = tab_w * 0.38
        c2_w = tab_w * 0.24
        c3_w = tab_w * 0.21
        c4_w = tab_w * 0.17

        col_xs = [
            tab_x,
            tab_x + c1_w,
            tab_x + c1_w + c2_w,
            tab_x + c1_w + c2_w + c3_w,
            tab_x + tab_w
        ]

        canvas_obj.setLineWidth(0.7)
        canvas_obj.rect(tab_x, tab_y_bot, tab_w, tab_h_dados + tab_h_cab, stroke=1, fill=0)
        canvas_obj.line(tab_x, tab_y_mid, tab_x + tab_w, tab_y_mid)

        for cx in col_xs[1:-1]:
            canvas_obj.line(cx, tab_y_bot, cx, tab_y_top)

        # Cabeçalhos da tabela
        canvas_obj.setFont("Helvetica-BoldOblique", 7.5)
        canvas_obj.drawCentredString((col_xs[0] + col_xs[1]) / 2, tab_y_mid + 0.12 * cm, "NOME PÁSSARO")
        canvas_obj.drawCentredString((col_xs[1] + col_xs[2]) / 2, tab_y_mid + 0.12 * cm, "CLUBE")
        canvas_obj.drawCentredString((col_xs[2] + col_xs[3]) / 2, tab_y_mid + 0.12 * cm, "DATA")
        canvas_obj.drawCentredString((col_xs[3] + col_xs[4]) / 2, tab_y_mid + 0.12 * cm, "Nº ESTACA")

        # Valores preenchidos na tabela
        canvas_obj.setFont("Helvetica-Bold", 8.5)
        canvas_obj.drawCentredString((col_xs[0] + col_xs[1]) / 2, tab_y_bot + 0.20 * cm, ave_str)
        canvas_obj.drawCentredString((col_xs[1] + col_xs[2]) / 2, tab_y_bot + 0.20 * cm, clube_ficha.upper())
        canvas_obj.drawCentredString((col_xs[2] + col_xs[3]) / 2, tab_y_bot + 0.20 * cm, data_str)
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawCentredString((col_xs[3] + col_xs[4]) / 2, tab_y_bot + 0.18 * cm, est_str)

    canvas_obj.save()
    buf.seek(0)
    return buf
if role_atual == "master":
    st.write("---")
    st.markdown("### ⚙️ Painel de Controle de Eventos (Master)")
    if torneio_data is None:
        st.markdown("#### 🟢 Abrir Nova Temporada / Torneio")
        data_nova_criar = st.date_input("Escolha a data do novo Torneio:", value=datetime.date(2026, 11, 15), format="DD/MM/YYYY")
        if st.button("🚀 ABRIR E LIBERAR INSCRIÇÕES", use_container_width=True, type="primary"):
            st.session_state["torneio_ativo_data"] = data_nova_criar
            st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])
            st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])
            salvar_dados_fisicos(); st.success("Torneio liberado!"); st.rerun()
    else:
        cbt1, cbt2 = st.columns([1.4, 1])
        with cbt1:
            st.markdown("**🖨️ Impressão de Fichas (16 por folha A4)**")
            if not df_inscritos_atual.empty:
                opcoes_fichas = [
                    f"Estaca {int(r['Estaca'])} | {r['Espécie']} - {r['Nome da Ave']} ({r['Proprietário']})"
                    for _, r in df_inscritos_atual.iterrows()
                ]

                if "fichas_selecionadas_box" not in st.session_state:
                    st.session_state["fichas_selecionadas_box"] = list(opcoes_fichas)
                else:
                    atual_sel = [item for item in st.session_state["fichas_selecionadas_box"] if item in opcoes_fichas]
                    if "ultima_lista_opcoes_fichas" in st.session_state:
                        novas_entradas = [item for item in opcoes_fichas if item not in st.session_state["ultima_lista_opcoes_fichas"]]
                        atual_sel.extend(novas_entradas)
                    st.session_state["fichas_selecionadas_box"] = atual_sel
                st.session_state["ultima_lista_opcoes_fichas"] = list(opcoes_fichas)

                todas_marcadas = len(st.session_state["fichas_selecionadas_box"]) == len(opcoes_fichas)
                texto_botao_toggle = "🔲 Desmarcar Todas" if todas_marcadas else "☑️ Selecionar Todas"

                if st.button(texto_botao_toggle, key="btn_toggle_todas_fichas", use_container_width=True):
                    if todas_marcadas:
                        st.session_state["fichas_selecionadas_box"] = []
                    else:
                        st.session_state["fichas_selecionadas_box"] = list(opcoes_fichas)
                    st.rerun()

                selecionadas = st.multiselect(
                    "Fichas selecionadas (clique no 'x' para remover alguma):",
                    options=opcoes_fichas,
                    key="fichas_selecionadas_box"
                )

                if selecionadas:
                    indices_escolhidos = [opcoes_fichas.index(item) for item in selecionadas]
                    df_para_imprimir = df_inscritos_atual.iloc[indices_escolhidos].copy()
                    pdf_p = gerar_pdf_fichas_canvas(df_para_imprimir, torneio_data)
                    st.download_button(
                        label=f"📥 Baixar PDF ({len(df_para_imprimir)} ficha(s) - 10,1x3,2cm)",
                        data=pdf_p,
                        file_name="fichas_selecionadas_aro.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                else:
                    st.info("Nenhuma ficha selecionada. Clique em 'Selecionar Todas' ou escolha acima.")
            else:
                st.caption("Nenhuma ave confirmada.")

        with cbt2:
            st.markdown("**🚨 Encerrar Evento Atual**")
            if st.checkbox("Habilitar botão de fechamento definitivo"):
                if st.button("💥 EXCLUIR E FECHAR TORNEIO", use_container_width=True, type="primary"):
                    st.session_state["torneio_ativo_data"] = None
                    st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])
                    st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])
                    salvar_dados_fisicos(); st.success("Torneio encerrado!"); st.rerun()

        st.write("---")
        st.markdown("### ➕ Inscrição Manual Rápida")
        with st.form("form_manual_master", clear_on_submit=True):
            m_prop, m_ave = st.text_input("Nome do Proprietário:"), st.text_input("Nome da Ave:")
            m_esp, m_anilha = st.selectbox("Espécie:", especies_validas), st.text_input("Número da Anilha:")
            m_socio = st.selectbox("Sócio da ARO?", ["Sim", "Não"], index=1)
            if st.form_submit_button("⚡ Inscrever Ave Manualmente", use_container_width=True):
                if m_prop and m_ave and m_anilha:
                    ocupadas = []
                    if not df_inscritos_atual.empty and "Estaca" in df_inscritos_atual.columns:
                        df_esp = df_inscritos_atual[df_inscritos_atual["Espécie"] == m_esp]
                        ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
                    lim = 50 if m_esp in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if m_esp in ["Canário", "Azulão"] else 5)
                    livres = [x for x in range(1, lim + 1) if x not in ocupadas]
                    sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else lim + 1)
                    nova_m = pd.DataFrame([{"Proprietário": m_prop.strip(), "Nome da Ave": m_ave.strip(), "Espécie": m_esp, "Anilha": m_anilha.strip(), "Estaca": int(sorteio), "Valor": 25.0 if m_socio == "Sim" else 35.0, "Clube": "ARO" if m_socio == "Sim" else "Outro"}])
                    st.session_state["dados_torneios_internos"] = pd.concat([df_inscritos_atual, nova_m], ignore_index=True)
                    salvar_dados_fisicos(); st.success(f"✅ Ave inserida na Estaca {sorteio}!"); st.rerun()

        if not df_inscritos_atual.empty:
            st.write("---")
            st.markdown("### 🗑️ Cancelamento Manual Individual")
            opc_lista = [f"[{r['Espécie']}] Estaca {r['Estaca']} - {r['Nome da Ave']} ({r['Proprietário']})" for _, r in df_inscritos_atual.iterrows()]
            sel_cancelar = st.selectbox("Selecione a inscrição que deseja remover:", opc_lista)
            if st.button("🗑️ Remover Inscrição Selecionada", use_container_width=True):
                idx_remover = opc_lista.index(sel_cancelar)
                st.session_state["dados_torneios_internos"] = df_inscritos_atual.drop(idx_remover).reset_index(drop=True)
                salvar_dados_fisicos()
                st.warning("Inscrição removida com sucesso!")
                st.rerun()
