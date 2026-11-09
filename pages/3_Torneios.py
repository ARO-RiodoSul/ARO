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

if torneio_data is not None:
    st.markdown("### 📊 Estatísticas (Confirmadas)")
    contagem = {esp: len(df_inscritos_atual[df_inscritos_atual["Espécie"] == esp]) if not df_inscritos_atual.empty else 0 for esp in especies_validas}
    cols = st.columns(6)
    for i, esp in enumerate(especies_validas): cols[i].metric(label=esp, value=str(contagem[esp]))
    st.info(f"✨ **TOTAL DE GAIOLAS CONFIRMADAS:** {sum(contagem.values())}")

# =========================================================================================
# 🌐 FLUXO EXCLUSIVO: VISITANTE / CONVIDADO
# =========================================================================================
if role_atual == "visitante":
    if torneio_data is not None:
        st.write("---")
        st.markdown("### 📝 inscrição para não socio")
        
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
                    nova_v = pd.DataFrame([{
                        "Proprietário": v_proprietario.strip(),
                        "Nome da Ave": v_ave.strip(),
                        "Espécie": v_especie,
                        "Anilha": v_anilha.strip(),
                        "Valor": 35.0,
                        "Clube": v_clube.strip()
                    }])
                    st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_v], ignore_index=True)
                    salvar_dados_fisicos()
                    st.success("✅ inscrição solicitada, aguarde a aprovação de um membro da diretoria ARO")
                    st.rerun()
    st.stop()  # Trava o visitante aqui! Nenhuma linha abaixo será executada por ele.

# =========================================================================================
# 🔒 FLUXO NORMAL: MASTER, DIRETORIA E SÓCIOS CLUBE (CÓDIGO ORIGINAL CONTINUA ABAIXO)
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
                c_inf.write(f"👤 **{row['Proprietário']}** | 🦜 {row['Nome da Ave']} ({row['Espécie']}) | 🏷️ {row['Anilha']}")
                if c_b1.button("✅ Approvar", key=f"ap_{idx}", use_container_width=True):
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
                    st.success("Aprovada!"); st.rerun()
                if c_b2.button("❌ Recusar", key=f"re_{idx}", use_container_width=True):
                    st.session_state["inscricoes_pendentes_aro"] = df_pendentes_atual.drop(idx).reset_index(drop=True)
                    salvar_dados_fisicos()
                    st.warning("Recusada!"); st.rerun()
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
    st.markdown("### 📝 Solicitar Inscrição de Ave")
    df_plantel = st.session_state.get("dados_aves_sistema", pd.DataFrame())
    df_disp = df_plantel if is_admin else (df_plantel[df_plantel["Proprietário"] == socio_vinculado] if not df_plantel.empty else pd.DataFrame())
    if df_disp.empty: 
        st.warning("⚠️ Nenhuma ave cadastrada no seu plantel.")
    else:
        with st.form("form_sol_insc", clear_on_submit=False):
            lista_opcoes = [f"{r['Nome da Ave']} ({r['Espécie']}) - Anilha: {r['Anilha']} | Dono: {r['Proprietário']}" for _, r in df_disp.iterrows()]
            ave_sel = st.selectbox("Selecione a Ave:", lista_opcoes)
            is_socio_clube = st.selectbox("Sócio da ARO?", ["Sim", "Não"])
            if st.form_submit_button("Enviar Solicitação", use_container_width=True):
                ave_obj = df_disp.iloc[lista_opcoes.index(ave_sel)]
                nova_s = pd.DataFrame([{"Proprietário": ave_obj["Proprietário"], "Nome da Ave": ave_obj["Nome da Ave"], "Espécie": ave_obj["Espécie"], "Anilha": ave_obj["Anilha"], "Valor": 25.0 if is_socio_clube == "Sim" else 35.0, "Clube": "ARO" if is_socio_clube == "Sim" else "Outro"}])
                st.session_state["inscricoes_pendentes_aro"] = pd.concat([df_pendentes_atual, nova_s], ignore_index=True)
                salvar_dados_fisicos()
                st.success("🎯 Solicitado com sucesso!"); st.rerun()

    st.write("---")
    st.markdown("### 🏆 Competidores Confirmados por Categoria")
    abas = st.tabs(especies_validas)
    for i, esp in enumerate(especies_validas):
        with abas[i]:
            df_f = df_inscritos_atual[df_inscritos_atual["Espécie"] == esp].copy() if not df_inscritos_atual.empty else pd.DataFrame()
            if df_f.empty:
                st.caption(f"Nenhum competidor confirmado para {esp} até o momento.")
            else:
                df_f["Estaca"] = pd.to_numeric(df_f["Estaca"], errors="coerce").fillna(0).astype(int)
                df_f = df_f.sort_values(by="Estaca").reset_index(drop=True)
                st.dataframe(df_f[["Estaca", "Proprietário", "Nome da Ave", "Anilha", "Clube", "Valor"]], hide_index=True, use_container_width=True)

# =========================================================================================
# ⚙️ EXCLUSIVO ADMINISTRATIVO: GERAÇÃO DE PDF E REINICIAR TORNEIO
# =========================================================================================
if is_admin and torneio_data is not None:
    st.write("---")
    st.markdown("### 🖨️ Central de Impressão de Etiquetas (10x7cm)")
    
    if st.button("📄 Gerar Caderno de Etiquetas PDF (Preto e Branco)", use_container_width=True):
        if df_inscritos_atual.empty:
            st.error("Não há inscrições confirmadas para gerar etiquetas.")
        else:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            largura_folha, altura_folha = A4
            
            # Dimensões solicitadas: 10cm x 7cm
            w_box = 10 * cm
            h_box = 7 * cm
            
            # Margens e espaçamentos otimizados para papel adesivo
            margin_x = 0.5 * cm
            margin_y = 0.5 * cm
            gap_x = 0.2 * cm
            gap_y = 0.2 * cm
            
            x_atual = margin_x
            y_atual = altura_folha - margin_y - h_box
            
            # Ordena por espécie e estaca antes de imprimir
            df_etiquetas = df_inscritos_atual.copy()
            df_etiquetas["Estaca"] = pd.to_numeric(df_etiquetas["Estaca"], errors="coerce").fillna(0).astype(int)
            df_etiquetas = df_etiquetas.sort_values(by=["Espécie", "Estaca"])
            
            for _, r in df_etiquetas.iterrows():
                if y_atual < margin_y:
                    p.showPage()
                    x_atual = margin_x
                    y_atual = altura_folha - margin_y - h_box
                
                # Desenho do contorno da etiqueta (Preto e Branco)
                p.setStrokeColor(colors.black)
                p.setLineWidth(1)
                p.rect(x_atual, y_atual, w_box, h_box)
                
                # Cabeçalho da Associação
                p.setFont("Helvetica-Bold", 11)
                p.drawString(x_atual + 0.4*cm, y_atual + 6.0*cm, "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA")
                p.setLineWidth(0.5)
                p.line(x_atual + 0.4*cm, y_atual + 5.7*cm, x_atual + w_box - 0.4*cm, y_atual + 5.7*cm)
                
                # Dados da Ave e Proprietário
                p.setFont("Helvetica-Bold", 10)
                p.drawString(x_atual + 0.4*cm, y_atual + 4.9*cm, f"PROPRIETÁRIO: {str(r['Proprietário']).upper()}")
                p.drawString(x_atual + 0.4*cm, y_atual + 4.1*cm, f"AVE: {str(r['Nome da Ave']).upper()}")
                
                p.setFont("Helvetica", 9)
                p.drawString(x_atual + 0.4*cm, y_atual + 3.3*cm, f"ESPÉCIE: {str(r['Espécie']).upper()}")
                p.drawString(x_atual + 0.4*cm, y_atual + 2.5*cm, f"ANILHA: {str(r['Anilha']).upper()}")
                p.drawString(x_atual + 0.4*cm, y_atual + 1.7*cm, f"CLUBE: {str(r.get('Clube', 'ARO')).upper()}")
                
                # Destaque para a Estaca e Valor cobrado
                p.setLineWidth(1)
                p.rect(x_atual + w_box - 3.2*cm, y_atual + 0.4*cm, 2.8*cm, 2.0*cm)
                
                p.setFont("Helvetica-Bold", 8)
                p.drawString(x_atual + w_box - 3.1*cm, y_atual + 2.1*cm, "ESTACA")
                p.setFont("Helvetica-Bold", 18)
                p.drawRightString(x_atual + w_box - 0.6*cm, y_atual + 0.8*cm, str(int(r['Estaca'])))
                
                p.setFont("Helvetica-Bold", 8)
                p.drawString(x_atual + 0.4*cm, y_atual + 0.5*cm, f"VALOR: R$ {r['Valor']:.2f}")
                
                # Próxima posição da grade
                x_atual += w_box + gap_x
                if x_atual + w_box > largura_folha - margin_x:
                    x_atual = margin_x
                    y_atual -= (h_box + gap_y)
            
            p.save()
            buffer.seek(0)
            st.download_button(
                label="📥 Baixar Fichas e Etiquetas em PDF",
                data=buffer,
                file_name=f"etiquetas_torneio_{torneio_data.strftime('%d_%m_%Y')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )

    st.write("---")
    st.markdown("### ⚠️ Administração Geral do Torneio")
    exp_reset = st.expander("Clique para expandir as opções de reinicialização")
    with exp_reset:
        st.warning("🚨 ATENÇÃO: O botão abaixo apagará definitivamente todas as aves inscritas e redefinirá os arquivos físicos.")
        if st.button("🗑️ Reiniciar e Limpar Dados do Torneio Atual", use_container_width=True, type="primary"):
            st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])
            st.session_state["inscricoes_pendentes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Valor", "Clube"])
            st.session_state["torneio_ativo_data"] = None
            salvar_dados_fisicos()
            st.success("Torneio reinicializado com sucesso!"); st.rerun()
