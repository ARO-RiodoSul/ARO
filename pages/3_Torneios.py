import streamlit as st
import pandas as pd
import datetime
import random
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="Torneios - Painel ARO", page_icon="🦅", layout="wide")
st.title("🦅 Gestão de Torneios - ARO Rio do Sul")

is_master = st.session_state.get("user_role") == "master"

if "data_torneio_aro" not in st.session_state or st.session_state["data_torneio_aro"] is None:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)
elif isinstance(st.session_state["data_torneio_aro"], str):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            st.session_state["data_torneio_aro"] = datetime.datetime.strptime(st.session_state["data_torneio_aro"], fmt).date()
            break
        except ValueError:
            continue

if "torneio_inscricoes_aro" not in st.session_state:
    st.session_state["torneio_inscricoes_aro"] = pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor"])

df_inscritos = st.session_state["torneio_inscricoes_aro"]

# --- 1. DATA EDITÁVEL ---
st.markdown("### 📅 Cronograma do Evento")
if is_master:
    nova_data = st.date_input("Data do Torneio:", value=st.session_state["data_torneio_aro"], format="DD/MM/YYYY", key="edit_data_torneio")
    if nova_data != st.session_state["data_torneio_aro"]:
        st.session_state["data_torneio_aro"] = nova_data
        st.rerun()
else:
    st.markdown(f"**Torneio Dia:** {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}")

st.write("---")

# --- 2. CONTADORES LIMPOS ---
st.markdown("### 📊 Estatísticas de Inscrição")
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
icones_especies = {"Trinca Ferro": "🪵 Trinca Ferro", "Coleiro": "🌾 Coleiro", "Bico de Pimenta": "🌶️ Bico de Pimenta", "Canário": "🟡 Canário", "Azulão": "🔷 Azulão", "Tiziu": "🕶️ Tiziu"}

contagem = {esp: len(df_inscritos[df_inscritos["Espécie"] == esp]) if not df_inscritos.empty else 0 for esp in especies_validas}
total_geral = sum(contagem.values())

cols = st.columns(6)
for i, esp in enumerate(especies_validas):
    cols[i].metric(label=icones_especies[esp], value=str(contagem[esp]))

st.write("")
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

# --- 5. IMPRESSÃO DE FICHAS DE GAIOLA (10x7 cm) ---
if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 🖨️ Fichas de Gaiola para Impressão (10x7 cm)")
    
    if st.button("📄 Gerar Bloco de Fichas Prontos para Impressão", use_container_width=True):
        st.success("Fichas estruturadas com sucesso abaixo! Pressione Ctrl+P no teclado para imprimir.")
        st.write("---")
        
        df_fichas = df_inscritos.sort_values(by=["Espécie", "Estaca"])
        
        st.markdown("""
        <style>
            .grid-fichas { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
            .ficha { width: 10cm; height: 7cm; border: 2px solid #D4AF37; padding: 8px; box-sizing: border-box; background-color: #FAFAFA; color: #111; font-family: sans-serif; overflow: hidden; }
            .ficha-header { text-align: center; font-weight: bold; border-bottom: 2px solid #111; padding-bottom: 2px; margin-bottom: 4px; font-size: 13px; }
            .ficha-estaca { font-size: 20px; font-weight: bold; text-align: center; color: #D4AF37; background: #111; padding: 2px; border-radius: 4px; margin-bottom: 6px; }
            .ficha-linha { font-size: 12px; margin-bottom: 3px; border-bottom: 1px dashed #ccc; padding-bottom: 1px; }
            .ficha-valor { font-size: 13px; font-weight: bold; text-align: right; color: #B22222; margin-top: 5px; }
        </style>
        """, unsafe_allow_html=True)
        
        conteudo_html = '<div class="grid-fichas">'
        for _, row in df_fichas.iterrows():
            conteudo_html += f"""
            <div class="ficha">
                <div class="ficha-header">ARO RIO DO SUL - TORNEIO OFICIAL</div>
                <div class="ficha-estaca">ESTACA / GAIOLA: {int(row['Estaca']):02d}</div>
                <div class="ficha-linha"><b>Espécie:</b> {row['Espécie'].upper()}</div>
                <div class="ficha-linha"><b>Canário/Ave:</b> {row['Nome da Ave']}</div>
                <div class="ficha-linha"><b>Criador:</b> {row['Proprietário']}</div>
                <div class="ficha-linha"><b>Nº Anilha:</b> {row['Anilha']}</div>
                <div class="ficha-valor">VALOR A PAGAR: R$ {float(row['Valor']):,.2f}</div>
            </div>
            """
        conteudo_html += '</div>'
        st.markdown(conteudo_html, unsafe_allow_html=True)

# --- 6. IMAGEM WHATSAPP ---
def criar_imagem(dt, mapa, total):
    W, H = 600, 520
    img = Image.new("RGB", (W, H), "#111625")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, W-20, H-20], outline="#D4AF37", width=2)
    draw.text((W/2, 50), "ARO - RIO DO SUL", fill="#D4AF37", anchor="mm", font_size=26)
    draw.text((W/2, 90), f"TORNEIO DIA: {dt}", fill="#FFFFFF", anchor="mm", font_size=20)
    draw.line([40, 130, W-40, 130], fill="#D4AF37", width=2)
    draw.text((50, 145), "ESPÉCIE", fill="#D4AF37", font_size=16)
    draw.text((W-50, 145), "QUANTIDADE", fill="#D4AF37", anchor="ra", font_size=16)
    draw.line([40, 175, W-40, 175], fill="#D4AF37", width=1)
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
            st.warning("Torneio resetado com sucesso!")
            st.rerun()
