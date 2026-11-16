import streamlit as st
import pandas as pd
import datetime, io, pickle, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Finanças - Painel ARO", page_icon="💰", layout="wide")

if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

st.title("💰 Fluxo de Caixa - ARO Rio do Sul")
is_master = st.session_state.get("user_role") == "master"

# Inclusão de Novembro 2026 no início da lista
lista_meses = ["Novembro 2026", "Dezembro 2026"] + [
    f"{m} {a}" for a in ["2027", "2028"] 
    for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
]

ARQUIVO_FINANCAS_FISICO = "backup_financas_oficial.pkl"

def criar_df_mes_padrao():
    return pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)])

def criar_estrutura_torneio_padrao():
    return {
        "titulo_evento": "",
        "receitas": [{"desc": "", "valor": 0.0} for _ in range(5)],
        "despesas": [{"desc": "", "valor": 0.0} for _ in range(5)]
    }

# BRIDGE DE COMPARTILHAMENTO DE RECURSO GLOBAL ENTRE SESSÕES E CELULARES
@st.cache_resource
def obter_banco_financeiro_global():
    if os.path.exists(ARQUIVO_FINANCAS_FISICO):
        try:
            with open(ARQUIVO_FINANCAS_FISICO, "rb") as f:
                dados = pickle.load(f)
                if "meses" not in dados:
                    dados["meses"] = {}
                for m in lista_meses:
                    if m not in dados["meses"]:
                        dados["meses"][m] = criar_df_mes_padrao()
                if "saldo_torneio_rascunho" not in dados:
                    dados["saldo_torneio_rascunho"] = criar_estrutura_torneio_padrao()
                return dados
        except:
            pass
    estrutura_base = {
        "saldo_anterior": 0.0,
        "meses": {m: criar_df_mes_padrao() for m in lista_meses},
        "saldo_torneio_rascunho": criar_estrutura_torneio_padrao()
    }
    with open(ARQUIVO_FINANCAS_FISICO, "wb") as f:
        pickle.dump(estrutura_base, f)
    return estrutura_base

# Sincroniza a memória local da página com a ponte física do servidor
if "banco_financeiro_viva" not in st.session_state:
    st.session_state["banco_financeiro_viva"] = obter_banco_financeiro_global()

for m in lista_meses:
    if m not in st.session_state["banco_financeiro_viva"]["meses"]:
        st.session_state["banco_financeiro_viva"]["meses"][m] = criar_df_mes_padrao()
if "saldo_torneio_rascunho" not in st.session_state["banco_financeiro_viva"]:
    st.session_state["banco_financeiro_viva"]["saldo_torneio_rascunho"] = criar_estrutura_torneio_padrao()

dados_mestre = st.session_state["banco_financeiro_viva"]
df_global_financas = dados_mestre["meses"]
saldo_anterior = dados_mestre["saldo_anterior"]

def persistir_financeiro_disco():
    with open(ARQUIVO_FINANCAS_FISICO, "wb") as f:
        pickle.dump(st.session_state["banco_financeiro_viva"], f)

# Cálculo dos acumulados
total_entradas_geral = 0.0
total_saidas_geral = 0.0
for m in lista_meses:
    df_m = df_global_financas[m]
    if df_m is not None and not df_m.empty:
        total_entradas_geral += pd.to_numeric(df_m["Entradas"], errors='coerce').fillna(0).sum()
        total_saidas_geral += pd.to_numeric(df_m["Saídas"], errors='coerce').fillna(0).sum()

saldo_gestao = total_entradas_geral - total_saidas_geral
saldo_total = saldo_anterior + saldo_gestao

st.markdown("### 📊 Resumo Consolidado Geral")
with st.container():
    if is_master:
        novo_saldo_anterior = st.number_input("Saldo Anterior (R$)", value=float(saldo_anterior), step=100.0, key="edit_saldo_ant")
        if novo_saldo_anterior != saldo_anterior:
            st.session_state["banco_financeiro_viva"]["saldo_anterior"] = novo_saldo_anterior
            persistir_financeiro_disco()
            st.rerun()
    else:
        st.metric(label="Saldo Anterior", value=f"R$ {saldo_anterior:,.2f}")

st.write("---")
col_meio_1, col_meio_2 = st.columns(2)
with col_meio_1: st.metric(label="Total de Entradas", value=f"R$ {total_entradas_geral:,.2f}")
with col_meio_2: st.metric(label="Total de Saídas", value=f"R$ {total_saidas_geral:,.2f}")

st.write("---")
col_baixo_1, col_baixo_2 = st.columns(2)
with col_baixo_1: st.metric(label="Saldo (Gestão Atual)", value=f"R$ {saldo_gestao:,.2f}")
with col_baixo_2: st.metric(label="Saldo (Total)", value=f"R$ {saldo_total:,.2f}")

st.write("---")
st.markdown("### 📅 Lançamentos Mensais")
mes_selecionado = st.selectbox("Selecione o mês para visualizar/editar:", lista_meses)
df_atual = df_global_financas[mes_selecionado]

total_entradas_mes = pd.to_numeric(df_atual["Entradas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
total_saidas_mes = pd.to_numeric(df_atual["Saídas"], errors='coerce').fillna(0).sum() if not df_atual.empty else 0.0
saldo_mes = total_entradas_mes - total_saidas_mes

col_mes_1, col_mes_2, col_mes_3 = st.columns(3)
with col_mes_1: st.metric("Entradas do Mês", f"R$ {total_entradas_mes:,.2f}")
with col_mes_2: st.metric("Saídas do Mês", f"R$ {total_saidas_mes:,.2f}")
with col_mes_3: st.metric("Balanço do Mês", f"R$ {saldo_mes:,.2f}")

st.write("")
st.markdown(f"**Tabela de Movimentações - {mes_selecionado}**")
if is_master:
    df_editado = st.data_editor(
        df_atual,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Dia": st.column_config.NumberColumn("Dia", min_value=1, max_value=31, step=1, format="%d", required=True),
            "Entradas": st.column_config.NumberColumn("Entradas (R$)", min_value=0.0, format="%.2f", default=0.0),
            "Saídas": st.column_config.NumberColumn("Saídas (R$)", min_value=0.0, format="%.2f", default=0.0),
            "Motivo": st.column_config.TextColumn("Motivo/Descrição")
        },
        key=f"editor_financeiro_{mes_selecionado}",
        use_container_width=True
    )
    
    if not df_editado.equals(df_atual):
        df_editado["Dia"] = pd.to_numeric(df_editado["Dia"], errors='coerce')
        df_editado = df_editado.dropna(subset=["Dia"]).sort_values(by="Dia").reset_index(drop=True)
        st.session_state["banco_financeiro_viva"]["meses"][mes_selecionado] = df_editado
        persistir_financeiro_disco()
        st.rerun()
else:
    st.dataframe(df_atual, hide_index=True, column_config={"Dia": "Dia", "Entradas": st.column_config.NumberColumn("Entradas (R$)", format="%.2f"), "Saídas": st.column_config.NumberColumn("Saídas (R$)", format="%.2f"), "Motivo": "Motivo/Descrição"}, use_container_width=True)

st.write("---")
st.markdown("### 💾 Central de Backups do Caixa")
col_fback_1, col_fback_2 = st.columns(2)

with col_fback_1:
    st.markdown("**Exportar Movimentações**")
    buffer_pkl = pickle.dumps(st.session_state["banco_financeiro_viva"])
    st.download_button(label="📥 Fazer Backup de Todo o Caixa (.PKL)", data=buffer_pkl, file_name="backup_financas_aro.pkl", mime="application/octet-stream", use_container_width=True)

with col_fback_2:
    if is_master:
        st.markdown("**Importar Arquivo de Backup**")
        arquivo_fin_enviado = st.file_uploader("Selecione o arquivo '.pkl' para restaurar:", type=["pkl"], key="uploader_financas")
        if arquivo_fin_enviado is not None:
            try:
                dados_importados = pickle.load(arquivo_fin_enviado)
                if "saldo_anterior" in dados_importados and "meses" in dados_importados:
                    for m in lista_meses:
                        if m not in dados_importados["meses"]:
                            dados_importados["meses"][m] = criar_df_mes_padrao()
                    if "saldo_torneio_rascunho" not in dados_importados:
                        dados_importados["saldo_torneio_rascunho"] = criar_estrutura_torneio_padrao()
                        
                    if st.button("🔄 Confirmar Restauração do Caixa", use_container_width=True, type="primary"):
                        st.session_state["banco_financeiro_viva"] = dados_importados
                        persistir_financeiro_disco()
                        st.success("Todo o fluxo de caixa foi restaurado com sucesso globalmente!")
                        st.rerun()
            except:
                st.error("Arquivo inválido.")

# =========================================================================================
# 🖨️ GERADOR DE RELATÓRIO PDF EXCLUSIVO POR MÊS SELECIONADO (EXCLUSIVO MASTER)
# =========================================================================================
if is_master:
    st.write("---")
    st.markdown("### 🖨️ Relatórios do Sistema")
    st.caption(f"O relatório abaixo será gerado exclusivamente para o período selecionado: **{mes_selecionado}**.")
    
    if st.button(f"📄 Salvar Relatório de {mes_selecionado} em PDF", use_container_width=True):
        df_m = df_global_financas[mes_selecionado]
        df_filtro = pd.DataFrame()
        if df_m is not None and not df_m.empty:
            df_filtro = df_m[(df_m["Entradas"] > 0) | (df_m["Saídas"] > 0) | (df_m["Motivo"].str.strip() != "")]
            
        if df_filtro.empty:
            st.warning(f"⚠️ Não existem movimentações ou lançamentos registrados no mês de {mes_selecionado} para gerar o PDF.")
        else:
            pdf_buffer = io.BytesIO()
            p = canvas.Canvas(pdf_buffer, pagesize=A4)
            largura_f, altura_f = A4
            
            margem_x = 1.5 * cm
            y_pos = altura_f - 2.0 * cm
            
            p.setFont("Helvetica-Bold", 14)
            p.drawString(margem_x, y_pos, "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA")
            y_pos -= 0.6 * cm
            
            p.setFont("Helvetica", 11)
            p.drawString(margem_x, y_pos, f"RELATÓRIO FINANCEIRO MENSAL - PERÍODO: {str(mes_selecionado).upper()}")
            y_pos -= 0.4 * cm
            
            p.setLineWidth(1)
            p.line(margem_x, y_pos, largura_f - margem_x, y_pos)
            y_pos -= 0.8 * cm
            
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margem_x, y_pos, f"Entradas do Mês: R$ {total_entradas_mes:,.2f}")
            p.drawString(margem_x + 6.0*cm, y_pos, f"Saídas do Mês: R$ {total_saidas_mes:,.2f}")
            p.drawString(margem_x + 12.0*cm, y_pos, f"Balanço Período: R$ {saldo_mes:,.2f}")
            y_pos -= 0.4 * cm
            
            p.setFont("Helvetica", 9)
            p.drawString(margem_x, y_pos, f"Saldo Anterior Geral: R$ {saldo_anterior:,.2f}  |  Saldo Total Acumulado do Caixa: R$ {saldo_total:,.2f}")
            y_pos -= 0.5 * cm
            
            p.setLineWidth(0.5)
            p.line(margem_x, y_pos, largura_f - margem_x, y_pos)
            y_pos -= 0.8 * cm
            
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margem_x, y_pos, "DIA")
            p.drawString(margem_x + 1.5*cm, y_pos, "ENTRADAS (R$)")
            p.drawString(margem_x + 5.0*cm, y_pos, "SAÍDAS (R$)")
            p.drawString(margem_x + 8.5*cm, y_pos, "MOTIVO / DESCRIÇÃO DOS LANÇAMENTOS")
            y_pos -= 0.3 * cm
            p.line(margem_x, y_pos, largura_f - margem_x, y_pos)
            y_pos -= 0.5 * cm
            
            p.setFont("Helvetica", 9)
            df_impressao = df_filtro.copy()
            df_impressao["Dia"] = pd.to_numeric(df_impressao["Dia"], errors='coerce').fillna(0).astype(int)
            df_impressao = df_impressao.sort_values(by="Dia")
            
            for _, row in df_impressao.iterrows():
                if y_pos < 2.0 * cm:
                    p.showPage()
                    p.setFont("Helvetica", 9)
                    y_pos = altura_f - 2.0 * cm
                    
                    p.setFont("Helvetica-Bold", 10)
                    p.drawString(margem_x, y_pos, "DIA")
                    p.drawString(margem_x + 1.5*cm, y_pos, "ENTRADAS (R$)")
                    p.drawString(margem_x + 5.0*cm, y_pos, "SAÍDAS (R$)")
                    p.drawString(margem_x + 8.5*cm, y_pos, "MOTIVO / DESCRIÇÃO DOS LANÇAMENTOS")
                    y_pos -= 0.3 * cm
                    p.line(margem_x, y_pos, largura_f - margem_x, y_pos)
                    y_pos -= 0.5 * cm
                    p.setFont("Helvetica", 9)
                
                p.drawString(margem_x + 0.1*cm, y_pos, str(int(row["Dia"])))
                p.drawString(margem_x + 1.5*cm, y_pos, f"R$ {float(row['Entradas']):,.2f}")
                p.drawString(margem_x + 5.0*cm, y_pos, f"R$ {float(row['Saídas']):,.2f}")
                
                motivo_texto = str(row["Motivo"]).strip()
                if len(motivo_texto) > 55:
                    motivo_texto = motivo_texto[:52] + "..."
                p.drawString(margem_x + 8.5*cm, y_pos, motivo_texto)
                
                y_pos -= 0.5 * cm
            
            p.save()
            pdf_buffer.seek(0)
            
            st.download_button(
                label=f"📥 Baixar Relatório - {mes_selecionado}.pdf",
                data=pdf_buffer,
                file_name=f"relatorio_financeiro_{str(mes_selecionado).replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
# =========================================================================================
# 🏆 NOVO MÓDULO: SALDO DE TORNEIO (EXCLUSIVO MASTER - GERADOR DE IMAGEM PARA DIRETORIA)
# =========================================================================================
if is_master:
    st.write("---")
    st.markdown("### 🏆 Saldo de Torneio")
    st.caption("Preencha as receitas e despesas do evento para gerar uma imagem e compartilhar com a diretoria. Os dados ficam salvos até você apagá-los manualmente.")
    
    rascunho_torneio = st.session_state["banco_financeiro_viva"]["saldo_torneio_rascunho"]
    alterou_torneio = False

    titulo_torneio = st.text_input(
        "Identificação / Data do Torneio (opcional - aparece no topo da imagem):",
        value=rascunho_torneio.get("titulo_evento", ""),
        placeholder="Ex: Etapa 15/11/2026 - Sede ARO",
        key="torneio_titulo_input"
    )
    if titulo_torneio != rascunho_torneio.get("titulo_evento", ""):
        rascunho_torneio["titulo_evento"] = titulo_torneio
        alterou_torneio = True

    st.markdown("#### 🟢 Receitas")
    total_receitas_torneio = 0.0
    for i in range(5):
        c_rec_1, c_rec_2 = st.columns([3, 1])
        with c_rec_1:
            desc_r = st.text_input(
                f"Descrição da Receita {i+1}",
                value=rascunho_torneio["receitas"][i]["desc"],
                placeholder=f"Ex: Inscrições / Fichas {i+1}",
                label_visibility="collapsed",
                key=f"torneio_rec_desc_{i}"
            )
        with c_rec_2:
            val_r = st.number_input(
                f"Valor Receita {i+1} (R$)",
                value=float(rascunho_torneio["receitas"][i]["valor"]),
                min_value=0.0,
                step=10.0,
                format="%.2f",
                label_visibility="collapsed",
                key=f"torneio_rec_val_{i}"
            )
        
        if desc_r != rascunho_torneio["receitas"][i]["desc"] or val_r != float(rascunho_torneio["receitas"][i]["valor"]):
            rascunho_torneio["receitas"][i]["desc"] = desc_r
            rascunho_torneio["receitas"][i]["valor"] = val_r
            alterou_torneio = True
            
        total_receitas_torneio += val_r

    st.markdown("#### 🔴 Despesas")
    total_despesas_torneio = 0.0
    for i in range(5):
        c_desp_1, c_desp_2 = st.columns([3, 1])
        with c_desp_1:
            desc_d = st.text_input(
                f"Motivo da Despesa {i+1}",
                value=rascunho_torneio["despesas"][i]["desc"],
                placeholder=f"Ex: Troféus / Arbitragem / Café {i+1}",
                label_visibility="collapsed",
                key=f"torneio_desp_desc_{i}"
            )
        with c_desp_2:
            val_d = st.number_input(
                f"Valor Despesa {i+1} (R$)",
                value=float(rascunho_torneio["despesas"][i]["valor"]),
                min_value=0.0,
                step=10.0,
                format="%.2f",
                label_visibility="collapsed",
                key=f"torneio_desp_val_{i}"
            )
            
        if desc_d != rascunho_torneio["despesas"][i]["desc"] or val_d != float(rascunho_torneio["despesas"][i]["valor"]):
            rascunho_torneio["despesas"][i]["desc"] = desc_d
            rascunho_torneio["despesas"][i]["valor"] = val_d
            alterou_torneio = True
            
        total_despesas_torneio += val_d

    # Salva automaticamente no disco sempre que qualquer campo for alterado
    if alterou_torneio:
        persistir_financeiro_disco()

    saldo_final_torneio = total_receitas_torneio - total_despesas_torneio

    st.write("")
    col_t_res1, col_t_res2, col_t_res3 = st.columns(3)
    with col_t_res1:
        st.metric("Total Receitas", f"R$ {total_receitas_torneio:,.2f}")
    with col_t_res2:
        st.metric("Total Despesas", f"R$ {total_despesas_torneio:,.2f}")
    with col_t_res3:
        st.metric("Saldo Final", f"R$ {saldo_final_torneio:,.2f}")

    def carregar_fonte_segura(tamanho, negrito=False):
        caminhos = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "arialbd.ttf" if negrito else "arial.ttf"
        ]
        for c in caminhos:
            if os.path.exists(c):
                try:
                    return ImageFont.truetype(c, tamanho)
                except:
                    pass
        return ImageFont.load_default()

    def criar_imagem_saldo_torneio(dados_t, tot_rec, tot_desp, saldo_f):
        recs_ativas = [r for r in dados_t["receitas"] if r["desc"].strip() != "" or float(r["valor"]) > 0]
        desps_ativas = [d for d in dados_t["despesas"] if d["desc"].strip() != "" or float(d["valor"]) > 0]
        
        if not recs_ativas:
            recs_ativas = [{"desc": "Nenhum lançamento", "valor": 0.0}]
        if not desps_ativas:
            desps_ativas = [{"desc": "Nenhum lançamento", "valor": 0.0}]

        largura = 900
        altura = 260 + (len(recs_ativas) * 44) + 70 + (len(desps_ativas) * 44) + 170
        img = Image.new("RGB", (largura, altura), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        f_titulo = carregar_fonte_segura(28, negrito=True)
        f_subtitulo = carregar_fonte_segura(18, negrito=False)
        f_secao = carregar_fonte_segura(21, negrito=True)
        f_texto = carregar_fonte_segura(19, negrito=False)
        f_texto_bold = carregar_fonte_segura(19, negrito=True)
        f_saldo_final = carregar_fonte_segura(26, negrito=True)

        # Cabeçalho escuro
        draw.rectangle([0, 0, largura, 115], fill=(30, 41, 59))
        draw.text((40, 22), "ARO - SALDO DE TORNEIO", fill=(250, 204, 21), font=f_titulo)
        sub_txt = dados_t.get("titulo_evento", "").strip()
        if not sub_txt:
            sub_txt = "Associação Rio do Sul de Ornitologia"
        draw.text((40, 68), sub_txt, fill=(241, 245, 249), font=f_subtitulo)

        y = 145
        # Bloco Receitas
        draw.rectangle([40, y, largura - 40, y + 44], fill=(220, 252, 231))
        draw.text((55, y + 10), "RECEITAS", fill=(22, 101, 52), font=f_secao)
        draw.text((largura - 270, y + 10), f"Total: R$ {tot_rec:,.2f}", fill=(22, 101, 52), font=f_secao)
        y += 54

        for idx, item in enumerate(recs_ativas):
            cor_fundo = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
            draw.rectangle([40, y, largura - 40, y + 40], fill=cor_fundo, outline=(226, 232, 240))
            desc_limpa = item["desc"].strip() if item["desc"].strip() else "Entrada sem descrição"
            if len(desc_limpa) > 45:
                desc_limpa = desc_limpa[:42] + "..."
            draw.text((55, y + 9), desc_limpa, fill=(30, 41, 59), font=f_texto)
            draw.text((largura - 230, y + 9), f"R$ {float(item['valor']):,.2f}", fill=(22, 101, 52), font=f_texto_bold)
            y += 42

        y += 28
        # Bloco Despesas
        draw.rectangle([40, y, largura - 40, y + 44], fill=(254, 226, 226))
        draw.text((55, y + 10), "DESPESAS", fill=(153, 27, 27), font=f_secao)
        draw.text((largura - 270, y + 10), f"Total: R$ {tot_desp:,.2f}", fill=(153, 27, 27), font=f_secao)
        y += 54

        for idx, item in enumerate(desps_ativas):
            cor_fundo = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
            draw.rectangle([40, y, largura - 40, y + 40], fill=cor_fundo, outline=(226, 232, 240))
            desc_limpa = item["desc"].strip() if item["desc"].strip() else "Despesa sem motivo"
            if len(desc_limpa) > 45:
                desc_limpa = desc_limpa[:42] + "..."
            draw.text((55, y + 9), desc_limpa, fill=(30, 41, 59), font=f_texto)
            draw.text((largura - 230, y + 9), f"R$ {float(item['valor']):,.2f}", fill=(153, 27, 27), font=f_texto_bold)
            y += 42

        y += 35
        # Caixa Saldo Final
        cor_box = (219, 234, 254) if saldo_f >= 0 else (254, 202, 202)
        cor_txt_saldo = (30, 58, 138) if saldo_f >= 0 else (153, 27, 27)
        draw.rectangle([40, y, largura - 40, y + 75], fill=cor_box, outline=cor_txt_saldo, width=2)
        draw.text((60, y + 22), "SALDO FINAL DO TORNEIO:", fill=cor_txt_saldo, font=f_saldo_final)
        draw.text((largura - 280, y + 22), f"R$ {saldo_f:,.2f}", fill=cor_txt_saldo, font=f_saldo_final)

        buf_img = io.BytesIO()
        img.save(buf_img, format="PNG")
        buf_img.seek(0)
        return buf_img

    st.write("")
    if st.button("🖼️ Gerar Imagem do Saldo do Torneio", use_container_width=True):
        imagem_pronta = criar_imagem_saldo_torneio(
            rascunho_torneio,
            total_receitas_torneio,
            total_despesas_torneio,
            saldo_final_torneio
        )
        st.image(imagem_pronta, caption="Pré-visualização do Saldo de Torneio", use_container_width=True)
        st.download_button(
            label="📥 Baixar Imagem para Enviar à Diretoria (.PNG)",
            data=imagem_pronta,
            file_name="saldo_torneio_aro.png",
            mime="image/png",
            use_container_width=True,
            type="primary"
        )
