import streamlit as st
import pandas as pd
import datetime, io, pickle, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Resultados - ARO", page_icon="🏆", layout="wide")

if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

st.title("🏆 Resultados e Classificação Geral - ARO")

role_atual = str(st.session_state.get("user_role", "")).strip().lower()
is_admin = role_atual in ["master", "diretoria", "admin"]
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
ARQUIVO_RESULTADOS = "backup_resultados_oficial.pkl"

def gerar_imagem_oficial_aro(titulo_banner, subtitulo_info, especie, df_dados, modo="etapa"):
    LARGURA = 1080
    qtd_itens = len(df_dados)
    ALTURA = max(1350, 500 + (qtd_itens * 96) + 110)

    if modo == "geral":
        COR_TOPO = (15, 23, 42)
        COR_BASE = (30, 41, 59)
        COR_DESTAQUE = (234, 179, 8)
        COR_TEXTO_FAIXA = (15, 23, 42)
    else:
        COR_TOPO = (12, 26, 62)
        COR_BASE = (23, 48, 108)
        COR_DESTAQUE = (56, 189, 248)
        COR_TEXTO_FAIXA = (12, 26, 62)

    COR_BRANCO = (255, 255, 255)
    COR_SUAVE = (203, 213, 225)
    COR_CARD_NORMAL = (30, 58, 115) if modo == "etapa" else (38, 52, 75)

    ESTILO_PODIO = {
        1: {"card": (212, 175, 55), "texto": (25, 20, 5), "sub": (55, 45, 10), "badge": (255, 255, 255), "num": (180, 130, 10)},
        2: {"card": (203, 213, 225), "texto": (20, 25, 35), "sub": (50, 60, 75), "badge": (255, 255, 255), "num": (71, 85, 105)},
        3: {"card": (205, 127, 50), "texto": (30, 15, 5), "sub": (65, 35, 10), "badge": (255, 255, 255), "num": (154, 85, 25)},
    }

    img = Image.new("RGB", (LARGURA, ALTURA), COR_TOPO)
    draw = ImageDraw.Draw(img)

    for y in range(ALTURA):
        fator = y / ALTURA
               r = int(COR_TOPO + (COR_BASE - COR_TOPO) * fator)
        g = int(COR_TOPO + (COR_BASE - COR_TOPO) * fator)
        b = int(COR_TOPO + (COR_BASE - COR_TOPO) * fator)

        draw.line([(0, y), (LARGURA, y)], fill=(r, g, b))

    draw.rectangle([22, 22, LARGURA - 22, ALTURA - 22], outline=COR_DESTAQUE, width=4)
    draw.rectangle([32, 32, LARGURA - 32, ALTURA - 32], outline=(255, 255, 255), width=1)

    def get_font(size, bold=False):
        caminhos = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
        ]
        for c in caminhos:
            if os.path.exists(c):
                return ImageFont.truetype(c, size)
        return ImageFont.load_default()

    f_clube = get_font(22, bold=True)
    f_titulo = get_font(48, bold=True)
    f_subtitulo = get_font(25, bold=False)
    f_especie = get_font(30, bold=True)
    f_pos = get_font(30, bold=True)
    f_ave = get_font(28, bold=True)
    f_detalhe = get_font(21, bold=False)
    f_pontos = get_font(30, bold=True)
    f_rodape = get_font(19, bold=False)

    y_cursor = 55

    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            altura_logo = 145
            proporcao = altura_logo / logo.height
            largura_logo = int(logo.width * proporcao)
            logo = logo.resize((largura_logo, altura_logo), Image.Resampling.LANCZOS)
            img.paste(logo, ((LARGURA - largura_logo) // 2, y_cursor), logo)
            y_cursor += altura_logo + 22
        except Exception:
            y_cursor += 15
    else:
        y_cursor += 15

    draw.text((LARGURA // 2, y_cursor), "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA", font=f_clube, fill=COR_DESTAQUE, anchor="mm")
    y_cursor += 44
    draw.text((LARGURA // 2, y_cursor), titulo_banner.upper(), font=f_titulo, fill=COR_BRANCO, anchor="mm")
    y_cursor += 44
    draw.text((LARGURA // 2, y_cursor), subtitulo_info, font=f_subtitulo, fill=COR_SUAVE, anchor="mm")
    y_cursor += 55

    draw.rounded_rectangle([120, y_cursor - 26, LARGURA - 120, y_cursor + 28], radius=16, fill=COR_DESTAQUE)
    draw.text((LARGURA // 2, y_cursor), f"MODALIDADE: {especie.upper()}", font=f_especie, fill=COR_TEXTO_FAIXA, anchor="mm")
    y_cursor += 68

    margem_x = 58
    largura_card = LARGURA - (margem_x * 2)
    altura_card = 82

    for idx, row in df_dados.iterrows():
        pos_num = idx + 1
        if "Ordem_Col" in row:
            pos_num = int(row["Ordem_Col"])

        if pos_num in ESTILO_PODIO:
            st_p = ESTILO_PODIO[pos_num]
            c_card, c_txt, c_sub, c_badge, c_num = st_p["card"], st_p["texto"], st_p["sub"], st_p["badge"], st_p["num"]
        else:
            c_card, c_txt, c_sub, c_badge, c_num = COR_CARD_NORMAL, COR_BRANCO, COR_SUAVE, COR_DESTAQUE, COR_TEXTO_FAIXA

        draw.rounded_rectangle([margem_x, y_cursor, margem_x + largura_card, y_cursor + altura_card], radius=14, fill=c_card)

        cy = y_cursor + (altura_card // 2)
        draw.ellipse([margem_x + 16, cy - 26, margem_x + 68, cy + 26], fill=c_badge)
        draw.text((margem_x + 42, cy), f"{pos_num}º", font=f_pos, fill=c_num, anchor="mm")

        nome_ave = str(row["Nome da Ave"]).upper()
        proprietario = str(row["Proprietário"]).upper()
        anilha = str(row["Anilha"]).upper()

        linha_1 = f"{nome_ave[:22]}  •  {proprietario[:24]}"
        if modo == "etapa":
            cantos_val = int(row["Cantos"])
            linha_2 = f"Anilha: {anilha}   |   Cantos: {cantos_val}"
            pts_val = int(row["Pontos"])
        else:
            linha_2 = f"Anilha: {anilha}"
            pts_val = int(row["Pontuação Acumulada"])

        draw.text((margem_x + 86, y_cursor + 24), linha_1, font=f_ave, fill=c_txt, anchor="lm")
        draw.text((margem_x + 86, y_cursor + 58), linha_2, font=f_detalhe, fill=c_sub, anchor="lm")
        draw.text((margem_x + largura_card - 24, cy), f"{pts_val} pts", font=f_pontos, fill=c_txt, anchor="rm")

        y_cursor += altura_card + 14

    draw.text(
        (LARGURA // 2, ALTURA - 45),
        f"Resultado Oficial ARO • Emitido em {datetime.date.today().strftime('%d/%m/%Y')}",
        font=f_rodape,
        fill=COR_SUAVE,
        anchor="mm"
    )

    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG", quality=95)
    img_buffer.seek(0)
    return img_buffer
# --- CARREGAMENTO FÍSICO DOS DADOS ---
def carregar_resultados_fisicos():
    if os.path.exists(ARQUIVO_RESULTADOS):
        with open(ARQUIVO_RESULTADOS, "rb") as f:
            return pickle.load(f)
    else:
        return {
            "historico_etapas": pd.DataFrame(columns=["Data", "Espécie", "Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]),
            "campeonato_geral": pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Pontuação Acumulada"])
        }

def salvar_resultados_fisicos(dados):
    with open(ARQUIVO_RESULTADOS, "wb") as f:
        pickle.dump(dados, f)

if "banco_resultados_viva" not in st.session_state:
    st.session_state["banco_resultados_viva"] = carregar_resultados_fisicos()

dados_resultados = st.session_state["banco_resultados_viva"]
df_etapas = dados_resultados["historico_etapas"]

if "lista_lote_resultados" not in st.session_state:
    st.session_state["lista_lote_resultados"] = []

# --- MENU DE OPÇÕES NO TOPO ---
opcao_tela = st.radio("Selecione a visualização desejada:", ["📅 Resultados por Etapa", "📊 Classificação Geral do Campeonato"], horizontal=True)

# =========================================================================================
# ⚙️ PAINEL DE LANÇAMENTO EM LOTE COM COLOCAÇÃO E PONTUAÇÃO LIVRE (MASTER / DIRETORIA)
# =========================================================================================
if is_admin:
    st.write("---")
    exp_cadastro = st.expander("📝 Painel de Lançamento de Resultados em Lote (Exclusivo Master/Diretoria)")
    with exp_cadastro:
        st.markdown("##### 1. Configurações Iniciais da Etapa")
        c_conf1, c_conf2, c_conf3 = st.columns(3)
        l_data = c_conf1.date_input("Data da Etapa:", datetime.date.today(), key="l_data_input")
        l_especie = c_conf2.selectbox("Espécie da Rodada:", especies_validas, key="l_especie_select")
        pt_maxima = c_conf3.number_input("Pontuação do 1º Colocado:", min_value=1, value=10, step=1)
        
        st.write("---")
        st.markdown("##### 2. Adicionar Aves Classificadas (Sem limite de posições)")
        
        with st.form("form_lote_individual_ajustado", clear_on_submit=True):
            col_r1, col_r2, col_r3 = st.columns(3)
            num_colocacao = col_r1.number_input("Colocação (Nº):", min_value=1, step=1, value=1)
            r_proprietario = col_r2.text_input("Proprietário:")
            r_ave = col_r3.text_input("Nome da Ave:")
            
            col_r4, col_r5 = st.columns(2)
            r_anilha = col_r4.text_input("Anilha:")
            r_cantos = col_r5.number_input("Quantidade de Cantos:", min_value=0, step=1, value=0)
            
            r_pontos = pt_maxima - (num_colocacao - 1)
            if r_pontos < 0:
                r_pontos = 0
            
            st.caption(f"💡 Esta colocação ({num_colocacao}º Lugar) receberá automaticamente: **{r_pontos} pontos**")
            
            if st.form_submit_button("➕ Adicionar à Lista Temporária", use_container_width=True):
                if not r_proprietario.strip() or not r_ave.strip() or not r_anilha.strip():
                    st.error("❌ Preencha todos os campos da ave antes de adicionar.")
                else:
                    nova_ave_temp = {
                        "Data": l_data.strftime("%d/%m/%Y"),
                        "Espécie": l_especie,
                        "Colocação": f"{num_colocacao}º Lugar",
                        "Proprietário": r_proprietario.strip().upper(),
                        "Nome da Ave": r_ave.strip().upper(),
                        "Anilha": r_anilha.strip().upper(),
                        "Cantos": int(r_cantos),
                        "Pontos": int(r_pontos)
                    }
                    st.session_state["lista_lote_resultados"].append(nova_ave_temp)
                    st.success(f"Ave '{r_ave.upper()}' adicionada temporariamente em {num_colocacao}º Lugar!")
                    st.rerun()

        if st.session_state["lista_lote_resultados"]:
            st.write("")
            st.markdown(f"**📋 Aves Preparadas para Salvar ({l_especie} - {l_data.strftime('%d/%m/%Y')})**")
            df_lote_temp = pd.DataFrame(st.session_state["lista_lote_resultados"])
            st.dataframe(df_lote_temp[["Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]], hide_index=True, use_container_width=True)
            
            cb_lote1, cb_lote2 = st.columns(2)
            if cb_lote1.button("🗑️ Limpar Lista Temporária", use_container_width=True):
                st.session_state["lista_lote_resultados"] = []
                st.rerun()
                
            if cb_lote2.button("💾 CONFIRMAR E SALVAR ETAPA COMPLETA NO SERVIDOR", use_container_width=True, type="primary"):
                st.session_state["banco_resultados_viva"]["historico_etapas"] = pd.concat([df_etapas, df_lote_temp], ignore_index=True)
                salvar_resultados_files = st.session_state["banco_resultados_viva"]
                salvar_resultados_fisicos(salvar_resultados_files)
                st.session_state["lista_lote_resultados"] = []
                st.success("🎯 Todos os resultados da etapa foram consolidados e salvos globalmente com sucesso!")
                st.rerun()
# =========================================================================================
# 📊 EXIBIÇÃO DOS DADOS: VISÍVEL PARA MASTER, DIRETORIA, SÓCIOS E VISITANTES
# =========================================================================================
st.write("")

# --- TELA 1: RESULTADOS POR ETAPA (FILTRADO POR DATA E COM EMISSÃO DE PDF E IMAGEM) ---
if opcao_tela == "📅 Resultados por Etapa":
    st.markdown("### 📅 Histórico de Etapas Realizadas")
    
    if df_etapas.empty:
        st.info("💡 Nenhuma etapa ou resultado foi lançado no campeonato ainda.")
    else:
        lista_datas = sorted(df_etapas["Data"].unique(), key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"), reverse=True)
        data_sel = st.selectbox("Selecione a data da etapa que deseja consultar:", lista_datas)
        
        df_filtrado_data = df_etapas[df_etapas["Data"] == data_sel].copy()
        
        abas_resultados = st.tabs(especies_validas)
        for i, esp_nome in enumerate(especies_validas):
            with abas_resultados[i]:
                df_res_esp = df_filtrado_data[df_filtrado_data["Espécie"] == esp_nome].copy()
                
                if df_res_esp.empty:
                    st.caption(f"Nenhum resultado registrado para {esp_nome} nesta etapa.")
                else:
                    df_res_esp["Ordem_Col"] = df_res_esp["Colocação"].str.extract(r'(\d+)').astype(int)
                    df_res_esp = df_res_esp.sort_values(by="Ordem_Col").reset_index(drop=True)
                    
                    st.dataframe(
                        df_res_esp[["Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]],
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.write("")
                    col_btn_pdf, col_btn_img = st.columns(2)
                    
                    # --- BOTÃO 1: GERADOR DE RELATÓRIO PDF DESIGNER COM LOGO ---
                    with col_btn_pdf:
                        if st.button(f"📄 Salvar Relatório Oficial em PDF", key=f"pdf_{esp_nome}_{data_sel}", use_container_width=True):
                            pdf_buffer = io.BytesIO()
                            p = canvas.Canvas(pdf_buffer, pagesize=A4)
                            largura_f, altura_f = A4
                            margem_x = 1.5 * cm
                            y_pos = altura_f - 1.5 * cm
                            
                            p.setFillColor(colors.HexColor("#1E3A8A"))
                            p.rect(margem_x, y_pos - 1.8*cm, largura_f - 2*margem_x, 1.8*cm, fill=True, stroke=False)
                            
                            if os.path.exists(LOGO_PATH):
                                try:
                                    p.drawImage(LOGO_PATH, margem_x + 0.3*cm, y_pos - 1.6*cm, width=1.4*cm, height=1.4*cm, mask='auto')
                                    texto_offset_x = 2.0 * cm
                                except:
                                    texto_offset_x = 0.4 * cm
                            else:
                                texto_offset_x = 0.4 * cm
                                
                            p.setFillColor(colors.white)
                            p.setFont("Helvetica-Bold", 13)
                            p.drawString(margem_x + texto_offset_x, y_pos - 0.7*cm, "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA")
                            p.setFont("Helvetica", 9)
                            p.drawString(margem_x + texto_offset_x, y_pos - 1.3*cm, f"RELATÓRIO DE RESULTADOS OFICIAIS  |  ETAPA: {data_sel}  |  CATEGORIA: {esp_nome.upper()}")
                            
                            y_pos -= 2.6 * cm
                            
                            p.setFillColor(colors.HexColor("#374151"))
                            p.rect(margem_x, y_pos - 0.6*cm, largura_f - 2*margem_x, 0.6*cm, fill=True, stroke=False)
                            
                            p.setFillColor(colors.white)
                            p.setFont("Helvetica-Bold", 9)
                            p.drawString(margem_x + 0.2*cm, y_pos - 0.4*cm, "COLOCAÇÃO")
                            p.drawString(margem_x + 2.8*cm, y_pos - 0.4*cm, "PROPRIETÁRIO")
                            p.drawString(margem_x + 8.2*cm, y_pos - 0.4*cm, "NOME DA AVE")
                            p.drawString(margem_x + 12.2*cm, y_pos - 0.4*cm, "ANILHA")
                            p.drawString(margem_x + 15.2*cm, y_pos - 0.4*cm, "CANTOS")
                            p.drawString(margem_x + 16.9*cm, y_pos - 0.4*cm, "PONTOS")
                            
                            y_pos -= 0.6 * cm
                            
                            cor_alternada = False
                            p.setFont("Helvetica", 9)
                            
                            for _, row in df_res_esp.iterrows():
                                if y_pos < 2.0 * cm:
                                    p.showPage()
                                    y_pos = altura_f - 2.0 * cm
                                    
                                if cor_alternada:
                                    p.setFillColor(colors.HexColor("#F9FAFB"))
                                    p.rect(margem_x, y_pos - 0.55*cm, largura_f - 2*margem_x, 0.55*cm, fill=True, stroke=False)
                                    
                                p.setFillColor(colors.HexColor("#1F2937"))
                                p.drawString(margem_x + 0.2*cm, y_pos - 0.4*cm, str(row["Colocação"]))
                                p.drawString(margem_x + 2.8*cm, y_pos - 0.4*cm, str(row["Proprietário"])[:28])
                                p.drawString(margem_x + 8.2*cm, y_pos - 0.4*cm, str(row["Nome da Ave"])[:18])
                                p.drawString(margem_x + 12.2*cm, y_pos - 0.4*cm, str(row["Anilha"])[:14])
                                p.drawString(margem_x + 15.2*cm, y_pos - 0.4*cm, str(int(row["Cantos"])))
                                
                                p.setFont("Helvetica-Bold", 9)
                                pontos_valor = int(row['Pontos'])
                                if pontos_valor > 0:
                                    p.setFillColor(colors.HexColor("#1E3A8A"))
                                    p.drawString(margem_x + 16.9*cm, y_pos - 0.4*cm, f"{pontos_valor} pts")
                                else:
                                    p.setFillColor(colors.HexColor("#9CA3AF"))
                                    p.drawString(margem_x + 16.9*cm, y_pos - 0.4*cm, "0 pts")
                                p.setFont("Helvetica", 9)
                                
                                p.setLineWidth(0.3)
                                p.setStrokeColor(colors.HexColor("#E5E7EB"))
                                p.line(margem_x, y_pos - 0.55*cm, largura_f - margem_x, y_pos - 0.55*cm)
                                
                                y_pos -= 0.55 * cm
                                cor_alternada = not cor_alternada
                            
                            p.setFont("Helvetica-Oblique", 8)
                            p.setFillColor(colors.HexColor("#6B7280"))
                            p.drawString(margem_x, 1.0*cm, f"Documento oficial emitido pelo sistema ARO em {datetime.date.today().strftime('%d/%m/%Y')} - Cópia Digital Segura")
                            
                            p.save()
                            pdf_buffer.seek(0)
                            
                            st.download_button(
                                label=f"📥 Baixar Relatório PDF - {esp_nome}",
                                data=pdf_buffer,
                                file_name=f"resultado_{esp_nome.lower().replace(' ', '_')}_{data_sel.replace('/', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"dl_btn_pdf_{esp_nome}_{data_sel}"
                            )
                    # --- BOTÃO 2: GERADOR DE IMAGEM OFICIAL (PÓDIO + LOGO) ---
                    with col_btn_img:
                        if st.button(f"🖼️ Gerar Imagem Oficial (WhatsApp/Insta)", key=f"img_etapa_{esp_nome}_{data_sel}", use_container_width=True):
                            img_etapa_buf = gerar_imagem_oficial_aro(
                                titulo_banner="RESULTADO OFICIAL DA ETAPA",
                                subtitulo_info=f"Data da Etapa: {data_sel}",
                                especie=esp_nome,
                                df_dados=df_res_esp,
                                modo="etapa"
                            )
                            st.image(img_etapa_buf, caption=f"Arte Oficial - {esp_nome} ({data_sel})", use_container_width=True)
                            st.download_button(
                                label=f"📥 Baixar Imagem PNG - {esp_nome}",
                                data=img_etapa_buf,
                                file_name=f"arte_resultado_{esp_nome.lower().replace(' ', '_')}_{data_sel.replace('/', '_')}.png",
                                mime="image/png",
                                use_container_width=True,
                                key=f"dl_btn_img_{esp_nome}_{data_sel}"
                            )

# --- TELA 2: CLASSIFICAÇÃO GERAL ACUMULADA DO CAMPEONATO (SOMA AUTOMÁTICA + IMAGEM) ---
else:
    st.markdown("### 📊 Classificação Geral do Campeonato Acumulado")
    st.caption("🏆 O ranking abaixo calcula e soma automaticamente todos os pontos conquistados pelas aves em cada etapa realizada.")
    
    if df_etapas.empty:
        st.info("💡 A classificação geral aparecerá assim que os primeiros resultados por etapa forem lançados.")
    else:
        df_ranking = df_etapas.groupby(["Anilha", "Nome da Ave", "Proprietário", "Espécie"])["Pontos"].sum().reset_index()
        df_ranking = df_ranking.rename(columns={"Pontos": "Pontuação Acumulada"})
        
        abas_campeonato = st.tabs(especies_validas)
        for i, esp_nome in enumerate(especies_validas):
            with abas_campeonato[i]:
                df_rank_esp = df_ranking[df_ranking["Espécie"] == esp_nome].copy()
                
                if df_rank_esp.empty:
                    st.caption(f"Nenhuma ave da espécie {esp_nome} pontuou no campeonato até o momento.")
                else:
                    df_rank_esp = df_rank_esp.sort_values(by="Pontuação Acumulada", ascending=False).reset_index(drop=True)
                    df_rank_esp.insert(0, "Posição", [f"{idx + 1}º Lugar" for idx in range(len(df_rank_esp))])
                    
                    st.dataframe(
                        df_rank_esp[["Posição", "Proprietário", "Nome da Ave", "Anilha", "Pontuação Acumulada"]],
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.write("")
                    if st.button(f"🏆 Gerar Imagem da Classificação Geral ({esp_nome})", key=f"img_geral_{esp_nome}", use_container_width=True):
                        ano_atual = datetime.date.today().year
                        img_geral_buf = gerar_imagem_oficial_aro(
                            titulo_banner="CLASSIFICAÇÃO GERAL",
                            subtitulo_info=f"Ranking Oficial Acumulado • Temporada {ano_atual}",
                            especie=esp_nome,
                            df_dados=df_rank_esp,
                            modo="geral"
                        )
                        st.image(img_geral_buf, caption=f"Ranking Geral Oficial - {esp_nome}", use_container_width=True)
                        st.download_button(
                            label=f"📥 Baixar Imagem Ranking Geral - {esp_nome}",
                            data=img_geral_buf,
                            file_name=f"classificacao_geral_{esp_nome.lower().replace(' ', '_')}_{ano_atual}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"dl_btn_geral_{esp_nome}"
                        )
