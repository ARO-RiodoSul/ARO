import streamlit as st
import pandas as pd
import datetime
import random
import io
import pickle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Torneios - ARO", page_icon="🦅", layout="wide")
st.title("🦅 Gestão de Torneios - ARO Rio do Sul")

is_master = st.session_state.get("user_role") == "master"

# Converte a data texto do app.py em objeto de data real para o st.date_input
if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 11, 8)
elif isinstance(st.session_state["data_torneio_aro"], str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            st.session_state["data_torneio_aro"] = datetime.datetime.strptime(st.session_state["data_torneio_aro"].strip(), fmt).date()
            break
        except ValueError:
            continue
    if isinstance(st.session_state["data_torneio_aro"], str):
        st.session_state["data_torneio_aro"] = datetime.date(2026, 11, 8)

if "dados_torneios_internos" not in st.session_state:
    st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])

df_inscritos = st.session_state["dados_torneios_internos"]

for col in ["Valor", "Clube"]:
    if col not in df_inscritos.columns:
        df_inscritos[col] = 25.00 if col == "Valor" else "ARO"

# --- 1. DATA DO TORNEIO ---
if is_master:
    nova_data = st.date_input("📅 Data do Torneio:", value=st.session_state["data_torneio_aro"], format="DD/MM/YYYY")
    if nova_data != st.session_state["data_torneio_aro"]:
        st.session_state["data_torneio_aro"] = nova_data
        try:
            with open("backup_data_torneio.txt", "w") as f:
                f.write(nova_data.strftime("%d/%m/%Y"))
        except: pass
        st.rerun()
else:
    st.markdown(f"### 📅 Torneio Dia: {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}")

# --- 2. CONTADORES LIMPOS ---
st.markdown("### 📊 Estatísticas de Inscrição")
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
contagem = {esp: len(df_inscritos[df_inscritos["Espécie"] == esp]) if not df_inscritos.empty else 0 for esp in especies_validas}

cols = st.columns(6)
for i, esp in enumerate(especies_validas):
    cols[i].metric(label=esp, value=str(contagem[esp]))
st.info(f"✨ **TOTAL DE GAIOLAS / INSCRITOS:** {sum(contagem.values())}")

# --- 3. FORMULÁRIO DE INSCRIÇÃO MASTER ---
if is_master:
    st.write("---")
    with st.form("form_inscrever", clear_on_submit=True):
        st.markdown("### 📝 Nova Inscrição de Ave")
        p = st.text_input("Proprietário:")
        n = st.text_input("Nome da Ave:")
        e = st.selectbox("Espécie:", especies_validas)
        a = st.text_input("Anilha:")
        socio = st.selectbox("Sócio?", ["Sim", "Não"])
        
        if st.form_submit_button("Inscrever Ave", use_container_width=True):
            if p.strip() and n.strip() and a.strip():
                ocupadas = []
                if not df_inscritos.empty:
                    df_esp = df_inscritos[df_inscritos["Espécie"] == e]
                    if "Estaca" in df_esp.columns:
                        ocupadas = pd.to_numeric(df_esp["Estaca"], errors='coerce').dropna().astype(int).tolist()
                
                limite = 50 if e in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else (25 if e in ["Canário", "Azulão"] else 5)
                livres = [x for x in range(1, limite + 1) if x not in ocupadas]
                sorteio = random.choice(livres) if livres else (max(ocupadas) + 1 if ocupadas else limite + 1)
                
                v_ficha = 25.00 if socio == "Sim" else 35.00
                clube_nome = "ARO" if socio == "Sim" else "Outro"
                
                nova = pd.DataFrame([{"Proprietário": p.strip(), "Nome da Ave": n.strip(), "Espécie": e, "Anilha": a.strip(), "Estaca": int(sorteio), "Valor": v_ficha, "Clube": clube_nome}])
                st.session_state["dados_torneios_internos"] = pd.concat([df_inscritos, nova], ignore_index=True)
                try:
                    pickle.dump(st.session_state["dados_torneios_internos"], open("backup_torneios_v2.pkl", "wb"))
                except: pass
                st.success(f"Inscrito com sucesso! Estaca: {sorteio}")
                st.rerun()
            else:
                st.error("Preencha todos os campos!")

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

# --- 5. EMISSÃO DE PDF ADESIVO P&B ---
def gerar_pdf_fichas(df_dados, data_evento):
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
        
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(px + (largura_f/2), py + altura_f - 14, "ARO RIO DO SUL - TORNEIO OFICIAL")
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(px + (largura_f/2), py + altura_f - 25, f"DATA DO EVENTO: {data_evento}")
        pdf.line(px + 6, py + altura_f - 30, px + largura_f - 6, py + altura_f - 30)
        
        try: estaca_num = int(float(r.get('Estaca', 1)))
        except: estaca_num = 1
            
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawCentredString(px + (largura_f/2), py + altura_f - 51, f"ESTACA: {estaca_num:02d}")
        pdf.line(px + 6, py + altura_f - 57, px + largura_f - 6, py + altura_f - 57)
        
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(px + 12, py + altura_f - 71, "AVE:")
        pdf.drawString(px + 12, py + altura_f - 86, "PROPRIETÁRIO:")
        pdf.drawString(px + 12, py + altura_f - 101, "ANILHA:")
        pdf.drawString(px + 12, py + altura_f - 116, "CLUBE:")
        pdf.drawString(px + 12, py + altura_f - 131, "ESPÉCIE:")
        
        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(px + 45, py + altura_f - 71, str(r.get('Nome da Ave', '')))
        pdf.drawString(px + 105, py + altura_f - 86, str(r.get('Proprietário', '')))
        pdf.drawString(px + 68, py + altura_f - 101, str(r.get('Anilha', '')))
        pdf.drawString(px + 65, py + altura_f - 116, str(r.get('Clube', 'ARO')).upper())
        pdf.drawString(px + 75, py + altura_f - 131, str(r.get('Espécie', '')).upper())
        
        try: valor_val = float(r.get('Valor', 25.00))
        except: valor_val = 25.00
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawRightString(px + largura_f - 12, py + 12, f"VALOR: R$ {valor_val:,.2f}")
        
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
    dt_str = st.session_state["data_torneio_aro"].strftime('%d/%m/%Y') if isinstance(st.session_state["data_torneio_aro"], datetime.date) else str(st.session_state["data_torneio_aro"])
    pdf_b = gerar_pdf_fichas(df_inscritos, dt_str)
    st.download_button(label="📥 Baixar Fichas em PDF (Preto e Branco - 10x7cm)", data=pdf_b, file_name="fichas_aro.pdf", mime="application/pdf", use_container_width=True)

# --- 6. EXCLUSÃO CELULAR ---
if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 🗑️ Remover Inscrição")
    opcoes = [f"[{r['Espécie']}] Estaca {r['Estaca']} - {r['Nome da Ave']} ({r['Proprietário']})" for _, r in df_inscritos.iterrows()]
    sel = st.selectbox("Selecione a ave:", opcoes)
    if st.checkbox("Confirmar cancelamento da ave selecionada"):
        if st.button("❌ Deletar Ave Selecionada", use_container_width=True):
            idx = opcoes.index(sel)
            st.session_state["dados_torneios_internos"] = df_inscritos.drop(df_inscritos.index[idx]).reset_index(drop=True)
            try: pickle.dump(st.session_state["dados_torneios_internos"], open("backup_torneios_v2.pkl", "wb"))
            except: pass
            st.success("Removida!")
            st.rerun()

# --- 7. ZERAR TORNEIO COMPLETO ---
if is_master:
    st.write("---")
    st.markdown("### ⚠️ Configurações Avançadas")
    if st.checkbox("💥 ATIVAR CONFIRMAÇÃO PARA RESETAR O TORNEIO"):
        if st.button("🗑️ ZERAR TORNEIO COMPLETO", type="primary", use_container_width=True):
            st.session_state["dados_torneios_internos"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])
            try: pickle.dump(st.session_state["dados_torneios_internos"], open("backup_torneios_v2.pkl", "wb"))
            except: pass
            st.warning("Torneio zerado com sucesso!")
            st.rerun()
