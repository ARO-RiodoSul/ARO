import streamlit as st
import pandas as pd
import datetime
import random
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Torneios - ARO", page_icon="🦅", layout="wide")
st.title("🦅 Gestão de Torneios - ARO Rio do Sul")

is_master = st.session_state.get("user_role") == "master"

if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)
if "torneio_inscricoes_aro" not in st.session_state:
    st.session_state["torneio_inscricoes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor"])

df_inscritos = st.session_state["torneio_inscricoes_aro"]

# --- 1. DATA EDITÁVEL ---
if is_master:
    nova_data = st.date_input("📅 Data do Torneio:", value=st.session_state["data_torneio_aro"], format="DD/MM/YYYY")
    if nova_data != st.session_state["data_torneio_aro"]:
        st.session_state["data_torneio_aro"] = nova_data
        st.rerun()
else:
    st.markdown(f"### 📅 Torneio Dia: {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}")

# --- 2. CONTADORES LIMPOS ---
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
contagem = {esp: len(df_inscritos[df_inscritos["Espécie"] == esp]) if not df_inscritos.empty else 0 for esp in especies_validas}

cols = st.columns(6)
for i, esp in enumerate(especies_validas):
    cols[i].metric(label=esp, value=str(contagem[esp]))
st.info(f"✨ **TOTAL DE GAIOLAS / INSCRITOS:** {sum(contagem.values())}")

# --- 3. INSCRIÇÃO MASTER ---
if is_master:
    st.write("---")
    with st.form("form_inscrever", clear_on_submit=True):
        st.markdown("### 📝 Nova Inscrição")
        p = st.text_input("Proprietário:")
        n = st.text_input("Nome da Ave:")
        e = st.selectbox("Espécie:", especies_validas)
        a = st.text_input("Anilha:")
        socio = st.selectbox("Sócio?", ["Sim", "Não"])
        
        if st.form_submit_button("Inscrever Ave", use_container_width=True):
            if p.strip() and n.strip() and a.strip():
                ocupadas = df_inscritos[df_inscritos["Espécie"] == e]["Estaca"].tolist()
                limite = 50 if e in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if e in ["Canário", "Azulão"] else 5)
                livres = [x for x in range(1, limite + 1) if x not in ocupadas]
                sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else limite + 1)
                
                v_ficha = 25.00 if socio == "Sim" else 35.00
                nova = pd.DataFrame([{"Proprietário": p.strip(), "Nome da Ave": n.strip(), "Espécie": e, "Anilha": a.strip(), "Estaca": int(sorteio), "Valor": v_ficha}])
                st.session_state["torneio_inscricoes_aro"] = pd.concat([df_inscritos, nova], ignore_index=True)
                st.success("Inscrito com sucesso!")
                st.rerun()

# --- 4. CONSULTA POR ABAS ---
st.write("---")
st.markdown("### 🏆 Lista de Competidores")
abas = st.tabs(especies_validas)
for i, esp in enumerate(especies_validas):
    with abas[i]:
        df_f = df_inscritos[df_inscritos["Espécie"] == esp] if not df_inscritos.empty else pd.DataFrame()
        if df_f.empty:
            st.caption("Nenhum pássaro cadastrado nesta categoria.")
        else:
            st.dataframe(df_f.sort_values(by="Estaca"), hide_index=True, column_config={"Estaca": st.column_config.NumberColumn("Estaca", format="%d"), "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f")}, use_container_width=True)

# --- 5. EMISSÃO DE PDF ADESIVO 10x7cm PRETO E BRANCO ---
def gerar_pdf_fichas(df_dados):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    df_ordenado = df_dados.sort_values(by=["Espécie", "Estaca"])
    
    largura_f, altura_f = 10 * cm, 7 * cm
    margem_x, margem_y = 0.5 * cm, 1.0 * cm
    x_at, y_at = 0, 0
    
    for _, r in df_ordenado.iterrows():
        px = margem_x + (x_at * largura_f)
        py = margem_y + (y_at * altura_f)
        
        pdf.setLineWidth(1.2)
        pdf.rect(px, py, largura_f, altura_f)
        
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawCentredString(px + (largura_f/2), py + altura_f - 16, "ARO RIO DO SUL - TORNEIO OFICIAL")
        pdf.line(px + 6, py + altura_f - 22, px + largura_f - 6, py + altura_f - 22)
        
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(px + (largura_f/2), py + altura_f - 46, f"ESTACA: {int(r['Estaca']):02d}")
        pdf.line(px + 6, py + altura_f - 54, px + largura_f - 6, py + altura_f - 54)
        
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(px + 12, py + altura_f - 70, "AVE:")
        pdf.drawString(px + 12, py + altura_f - 88, "CRIADOR:")
        pdf.drawString(px + 12, py + altura_f - 106, "ANILHA:")
        pdf.drawString(px + 12, py + altura_f - 124, "ESPÉCIE:")
        
        pdf.setFont("Helvetica", 11)
        pdf.drawString(px + 45, py + altura_f - 70, str(r['Nome da Ave']))
        pdf.drawString(px + 75, py + altura_f - 88, str(r['Proprietário']))
        pdf.drawString(px + 68, py + altura_f - 106, str(r['Anilha']))
        pdf.drawString(px + 75, py + altura_f - 124, str(r['Espécie']).upper())
        
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawRightString(px + largura_f - 12, py + 12, f"VALOR: R$ {float(r['Valor']):,.2f}")
        
        x_at += 1
        if x_at >= 2:
            x_at = 0
            y_at += 1
            if y_at >= 4:
                y_at = 0
                pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 🖨️ Central de Impressão Adesiva")
    pdf_b = gerar_pdf_fichas(df_inscritos)
    st.download_button(label="📥 Baixar Fichas em PDF (Preto e Branco - 10x7cm)", data=pdf_b, file_name="fichas_aro.pdf", mime="application/pdf", use_container_width=True)

# --- 6. EXCLUSÃO INDIVIDUAL NO CELULAR ---
if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 🗑️ Remover Inscrição")
    opcoes = [f"[{r['Espécie']}] Estaca {r['Estaca']} - {r['Nome da Ave']} ({r['Proprietário']})" for _, r in df_inscritos.iterrows()]
    sel = st.selectbox("Selecione a ave:", opcoes)
    if st.checkbox("Confirmar cancelamento da ave selecionada"):
        if st.button("❌ Deletar Ave Selecionada", use_container_width=True):
            idx = opcoes.index(sel)
            st.session_state["torneio_inscricoes_aro"] = df_inscritos.drop(df_inscritos.index[idx]).reset_index(drop=True)
            st.success("Removida!")
            st.rerun()

# --- 7. ZERAR TORNEIO COMPLETO ---
if is_master:
    st.write("---")
    st.markdown("### ⚠️ Configurações Avançadas")
    if st.checkbox("💥 ATIVAR CONFIRMAÇÃO PARA RESETAR O TORNEIO"):
        if st.button("🗑️ ZERAR TORNEIO COMPLETO", type="primary", use_container_width=True):
            st.session_state["torneio_inscricoes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor"])
            st.warning("Torneio zerado com sucesso!")
            st.rerun()
