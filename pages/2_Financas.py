import streamlit as st
import pandas as pd
import datetime, io, pickle, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

st.set_page_config(page_title="Finanças - Painel ARO", page_icon="💰", layout="wide")

if st.session_state.get("user_role") not in ["master", "diretoria"]:
    st.error("🔒 Acesso Restrito! Esta página é exclusiva para membros do nível Master ou Diretoria.")
    st.stop()

st.title("💰 Fluxo de Caixa - ARO Rio do Sul")
is_master = st.session_state.get("user_role") == "master"

lista_meses = ["Dezembro 2026"] + [f"{m} {a}" for a in ["2027", "2028"] for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]]

ARQUIVO_FINANCAS_FISICO = "backup_financas_oficial.pkl"

# BRIDGE DE COMPARTILHAMENTO DE RECURSO GLOBAL ENTRE SESSÕES E CELULARES
@st.cache_resource
def obter_banco_financeiro_global():
    if os.path.exists(ARQUIVO_FINANCAS_FISICO):
        try:
            with open(ARQUIVO_FINANCAS_FISICO, "rb") as f:
                return pickle.load(f)
        except:
            pass
    # Se o arquivo físico não existir, cria a estrutura inicial padrão
    estrutura_base = {
        "saldo_anterior": 0.0,
        "meses": {m: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m in lista_meses}
    }
    with open(ARQUIVO_FINANCAS_FISICO, "wb") as f:
        pickle.dump(estrutura_base, f)
    return estrutura_base

# Sincroniza a memória local da página com a ponte física do servidor
if "banco_financeiro_viva" not in st.session_state:
    st.session_state["banco_financeiro_viva"] = obter_banco_financeiro_global()

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
                    if st.button("🔄 Confirmar Restauração do Caixa", use_container_width=True, type="primary"):
                        st.session_state["banco_financeiro_viva"] = dados_importados
                        persistir_financeiro_disco()
                        st.success("Todo o fluxo de caixa foi restaurado com sucesso globalmente!")
                        st.rerun()
            except:
                st.error("Arquivo inválido.")

# =========================================================================================
# 🖨️ NOVO: GERADOR DE RELATÓRIO PDF EXCLUSIVO POR MÊS SELECIONADO (EXCLUSIVO MASTER)
# =========================================================================================
if is_master:
    st.write("---")
    st.markdown("### 🖨️ Relatórios do Sistema")
    st.caption(f"O relatório abaixo será gerado exclusivamente para o período selecionado: **{mes_selecionado}**.")
    
    if st.button(f"📄 Salvar Relatório de {mes_selecionado} em PDF", use_container_width=True):
        # Filtra apenas linhas que possuem alguma movimentação real preenchida
        df_m = df_global_financas[mes_selecionado]
        df_filtro = pd.DataFrame()
        if df_m is not None and not df_m.empty:
            df_filtro = df_m[(df_m["Entradas"] > 0) | (df_m["Saídas"] > 0) | (df_m["Motivo"].str.strip() != "")]
            
        if df_filtro.empty:
            st.warning(f"⚠️ Não existem movimentações ou lançamentos registrados no mês de {mes_selecionado} para gerar o PDF.")
        else:
            # Inicializa o canvas do ReportLab voltado para A4
            pdf_buffer = io.BytesIO()
            p = canvas.Canvas(pdf_buffer, pagesize=A4)
            largura_f, altura_f = A4
            
            # Configuração de margens básicas de segurança
            margem_x = 1.5 * cm
            y_pos = altura_f - 2.0 * cm
            
            # --- CABEÇALHO DO DOCUMENTO (PRETO E BRANCO) ---
            p.setFont("Helvetica-Bold", 14)
            p.drawString(margem_x, y_pos, "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA")
            y_pos -= 0.6 * cm
            
            p.setFont("Helvetica", 11)
            p.drawString(margem_x, y_pos, f"RELATÓRIO FINANCEIRO MENSAL - PERÍODO: {str(mes_selecionado).upper()}")
            y_pos -= 0.4 * cm
            
            p.setLineWidth(1)
            p.line(margem_x, y_pos, largura_f - margem_x, y_pos)
            y_pos -= 0.8 * cm
            
            # --- RESUMO FINANCEIRO DO MÊS ---
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
            
            # --- CABEÇALHO DA TABELA ---
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margem_x, y_pos, "DIA")
            p.drawString(margem_x + 1.5*cm, y_pos, "ENTRADAS (R$)")
            p.drawString(margem_x + 5.0*cm, y_pos, "SAÍDAS (R$)")
            p.drawString(margem_x + 8.5*cm, y_pos, "MOTIVO / DESCRIÇÃO DOS LANÇAMENTOS")
            y_pos -= 0.3 * cm
            p.line(margem_x, y_pos, largura_f - margem_x, y_pos)
            y_pos -= 0.5 * cm
            
            # --- RENDERIZAÇÃO DOS LANÇAMENTOS FLUIDOS ---
            p.setFont("Helvetica", 9)
            df_impressao = df_filtro.copy()
            df_impressao["Dia"] = pd.to_numeric(df_impressao["Dia"], errors='coerce').fillna(0).astype(int)
            df_impressao = df_impressao.sort_values(by="Dia")
            
            for _, row in df_impressao.iterrows():
                # Validação de quebra de página automática se estourar o limite vertical
                if y_pos < 2.0 * cm:
                    p.showPage()
                    p.setFont("Helvetica", 9)
                    y_pos = altura_f - 2.0 * cm
                    
                    # Reaplica o cabeçalho da tabela na nova folha
                    p.setFont("Helvetica-Bold", 10)
                    p.drawString(margem_x, y_pos, "DIA")
                    p.drawString(margem_x + 1.5*cm, y_pos, "ENTRADAS (R$)")
                    p.drawString(margem_x + 5.0*cm, y_pos, "SAÍDAS (R$)")
                    p.drawString(margem_x + 8.5*cm, y_pos, "MOTIVO / DESCRIÇÃO DOS LANÇAMENTOS")
                    y_pos -= 0.3 * cm
                    p.line(margem_x, y_pos, largura_f - margem_x, y_pos)
                    y_pos -= 0.5 * cm
                    p.setFont("Helvetica", 9)
                
                # Renderiza a linha de dados físicos
                p.drawString(margem_x + 0.1*cm, y_pos, str(int(row["Dia"])))
                p.drawString(margem_x + 1.5*cm, y_pos, f"R$ {float(row['Entradas']):,.2f}")
                p.drawString(margem_x + 5.0*cm, y_pos, f"R$ {float(row['Saídas']):,.2f}")
                
                # Truncamento básico de segurança na string do motivo para não estourar a margem direita
                motivo_texto = str(row["Motivo"]).strip()
                if len(motivo_texto) > 55:
                    motivo_texto = motivo_texto[:52] + "..."
                p.drawString(margem_x + 8.5*cm, y_pos, motivo_texto)
                
                y_pos -= 0.5 * cm
            
            # Fecha o documento PDF e disponibiliza para download
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
