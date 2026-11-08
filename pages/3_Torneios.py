import streamlit as st
import pandas as pd
import datetime
import random
from PIL import Image, ImageDraw
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Torneios - Painel ARO", page_icon="🦅", layout="wide")
st.title("🦅 Gestão de Torneios - ARO Rio do Sul")

is_master = st.session_state.get("user_role") == "master"

if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)
if "torneio_inscricoes_aro" not in st.session_state:
    st.session_state["torneio_inscricoes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor"])

df_inscritos = st.session_state["torneio_inscricoes_aro"]

# --- 1. DATA EDITÁVEL ---
st.markdown("### 📅 Cronograma do Evento")
if is_master:
    nova_data = st.date_input("Data do Torneio:", value=st.session_state["data_torneio_aro"], format="DD/MM/YYYY")
    if nova_data != st.session_state["data_torneio_aro"]:
        st.session_state["data_torneio_aro"] = nova_data
        st.rerun()
else:
    st.markdown(f"**Torneio Dia:** {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}")

# --- 2. CONTADORES LIMPOS ---
st.markdown("### 📊 Estatísticas de Inscrição")
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
icones_especies = {"Trinca Ferro": "🪵 Trinca Ferro", "Coleiro": "🌾 Coleiro", "Bico de Pimenta": "🌶️ Bico de Pimenta", "Canário": "🟡 Canário", "Azulão": "🔷 Azulão", "Tiziu": "🕶️ Tiziu"}

contagem = {esp: len(df_inscritos[df_inscritos["Espécie"] == esp]) if not df_inscritos.empty else 0 for esp in especies_validas}
total_geral = sum(contagem.values())

cols = st.columns(6)
for i, esp in enumerate(especies_validas):
    cols[i].metric(label=icones_especies[esp], value=str(contagem[esp]))
st.info(f"✨ **TOTAL DE GAIOLAS / AVES INSCRITAS:** {total_geral}")
st.write("---")

# --- 3. FORMULÁRIO DE INSCRIÇÃO ---
if is_master:
    st.markdown("### 📝 Nova Inscrição de Ave")
    with st.form("form_inscrever", clear_on_submit=True):
        p = st.text_input("Proprietário:")
        n = st.text_input("Nome da Ave:")
        e = st.selectbox("Espécie:", especies_validas)
        a = st.text_input("Anilha:")
        socio_op = st.selectbox("Sócio?", ["Sim", "Não"])
        
        if st.form_submit_button("Inscrever Ave", use_container_width=True):
            if p.strip() and n.strip() and a.strip():
                ocupadas = df_inscritos[df_inscritos["Espécie"] == e]["Estaca"].tolist()
                limite = 50 if e in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if e in ["Canário", "Azulão"] else 5)
                livres = [x for x in range(1, limite + 1) if x not in ocupadas]
                sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else limite + 1)
                
                valor_ficha = 25.00 if socio_op == "Sim" else 35.00
                nova = pd.DataFrame([{"Proprietário": p.strip(), "Nome da Ave": n.strip(), "Espécie": e, "Anilha": a.strip(), "Estaca": int(sorteio), "Valor": valor_ficha}])
                st.session_state["torneio_inscricoes_aro"] = pd.concat([df_inscritos, nova], ignore_index=True)
                st.success(f"Sucesso! Ave inscrita na Estaca: {sorteio}")
                st.rerun()
            else:
                st.error("Preencha todos os campos!")
    st.write("---")

# --- 4. EXIBIÇÃO EM ABAS ---
st.markdown("### 🏆 Competidores por Categoria")
abas = st.tabs([icones_especies[esp] for esp in especies_validas])
for i, esp in enumerate(especies_validas):
    with abas[i]:
        df_f = df_inscritos[df_inscritos["Espécie"] == esp]
        if df_f.empty:
            st.info(f"Nenhum pássaro cadastrado em {esp}.")
        else:
            st.dataframe(df_f.sort_values(by="Estaca"), hide_index=True, column_config={"Estaca": st.column_config.NumberColumn("Estaca", format="%d"), "Valor": st.column_config.NumberColumn("Taxa (R$)", format="%.2f")}, use_container_width=True)

# --- 5. EXPORTAÇÃO DIRETA EM PDF P&B (10x7cm) ---
def gerar_pdf_fichas(df_dados):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    df_ordenado = df_dados.sort_values(by=["Espécie", "Estaca"])
    
    largura_f, altura_f = 10 * cm, 7 * cm
    margem_x, margem_y = 0.5 * cm, 2.0 * cm
    x_atual, y_atual = 0, 0
    
    for _, row in df_ordenado.iterrows():
        px = margem_x + (x_atual * largura_f)
        py = margem_y + (y_atual * altura_f)
        
        pdf.setLineWidth(1)
        pdf.setStrokeColorRGB(0, 0, 0)
        pdf.rect(px, py, largura_f, altura_f)
        
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawCentredString(px + (largura_f/2), py + altura_f - 12, "ARO RIO DO SUL - TORNEIO OFICIAL")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(px + (largura_f/2), py + altura_f - 30, f"ESTACA: {int(row['Estaca']):02d}")
        
        pdf.setFont("Helvetica", 9)
        pdf.drawString(px + 10, py + altura_f - 45, f"Espécie: {str(row['Espécie']).upper()}")
        pdf.drawString(px + 10, py + altura_f - 58, f"Ave: {str(row['Nome da Ave'])}")
        pdf.drawString(px + 10, py + altura_f - 71, f"Criador: {str(row['Proprietário'])}")
        pdf.drawString(px + 10, py + altura_f - 84, f"Anilha: {str(row['Anilha'])}")
        
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawRightString(px + largura_f - 10, py + 10, f"VALOR: R$ {float(row['Valor']):.2f}")
        
        x_atual += 1
        if x_atual >= 2:
            x_atual = 0
            y_atual += 1
            if y_atual >= 3:
                y_atual = 0
                pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 🖨️ Fichas Adesivas em PDF (Preto e Branco)")
    pdf_data = gerar_pdf_fichas(df_inscritos)
    st.download_button(label="📥 Baixar Fichas em PDF para Adesivo (P&B)", data=pdf_data, file_name="fichas_adesivas_aro.pdf", mime="application/pdf", use_container_width=True)

# --- 6. IMAGEM WHATSAPP ---
def criar_imagem(dt, mapa, total):
    W, H = 600, 520
    img = Image.new("RGB", (W, H), "#111625")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, W-20, H-20], outline="#D4AF37", width=2)
    draw.text((W/2, 50), "ARO - RIO DO SUL", fill="#D4AF37", anchor="mm", font_size=26)
    draw.text((W/2, 90), f"TORNEIO DIA: {dt}", fill="#FFFFFF", anchor="mm", font_size=20)
    draw.line([40, 130, W-40, 130], fill="#D4AF37", width=2)
    y = 190
    for esp, qtd in mapa.items():
        draw.text((50, y), esp.upper(), fill="#FFFFFF", font_size=16)
        draw.text((W-50, y), str(qtd), fill="#FFFFFF", anchor="ra", font_size=16)
        draw.line([40, y+25, W-40, y+25], fill="#2D3748", width=1)
        y += 40
    draw.line([40, y, W-40, y], fill="#D4AF37", width=2)
    draw.text((50, y+15), "TOTAL GERAL DE GAIOLAS", fill="#D4AF37", font_size=18)
    draw.text((W-50, y+15), str(total), fill="#D4AF37", anchor="ra", font_size=18)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 📊 Exportação Compartilhada")
    img_b = criar_imagem(st.session_state["data_torneio_aro"].strftime('%d/%m/%Y'), contagem, total_geral)
    st.image(img_b, width=380)
    st.download_button("📥 Baixar Cartaz para WhatsApp", data=img_b, file_name="aro_torneio.png", mime="image/png", use_container_width=True)

# --- 7. EXCLUSÃO CELULAR ---
if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 🗑️ Cancelar Inscrição")
    opcoes = [f"[{r['Espécie']}] Estaca {r['Estaca']} - {r['Nome da Ave']} ({r['Proprietário']})" for _, r in df_inscritos.iterrows()]
    sel = st.selectbox("Escolha a ave para remover:", opcoes)
    if st.checkbox("⚠️ Confirmar remoção desta ave", key="chk_del_u"):
        if st.button("❌ Deletar Ave Selecionada", use_container_width=True):
            idx = opcoes.index(sel)
            st.session_state["torneio_inscricoes_aro"] = df_inscritos.drop(df_inscritos.index[idx]).reset_index(drop=True)
            st.success("Ave removida!")
            st.rerun()

# --- 8. ZERAR TORNEIO COMPLETO ---
if is_master:
    st.write("---")
    st.markdown("### ⚠️ Zona de Perigo Administrativa")
    if st.checkbox("💥 CONFIRMAR EXCLUSÃO DE TODOS OS INSCRITOS", key="chk_reset"):
        if st.button("🗑️ ZERAR TORNEIO COMPLETO", type="primary", use_container_width=True):
            st.session_state["torneio_inscricoes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor"])
            st.warning("Torneio resetado!")
            st.rerun()
