import streamlit as st
import pandas as pd
import datetime, io, pickle, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

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
            # Mudado para NumberInput para permitir qualquer número de colocação livremente
            num_colocacao = col_r1.number_input("Colocação (Nº):", min_value=1, step=1, value=1)
            r_proprietario = col_r2.text_input("Proprietário:")
            r_ave = col_r3.text_input("Nome da Ave:")
            
            col_r4, col_r5 = st.columns(2)
            r_anilha = col_r4.text_input("Anilha:")
            r_cantos = col_r5.number_input("Quantidade de Cantos:", min_value=0, step=1, value=0)
            
            # Lógica Decrescente: Se faltar pontos para a colocação, assume 0 automaticamente
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

# --- TELA 1: RESULTADOS POR ETAPA (FILTRADO POR DATA E COM EMISSÃO DE PDF) ---
if opcao_tela == "📅 Resultados por Etapa":
    st.markdown("### 📅 Histórico de Etapas Realizadas")
    
    if df_etapas.empty:
        st.info("💡 Nenhuma etapa ou resultado foi lançado no campeonato ainda.")
    else:
        # Puxa todas as datas únicas salvas para o usuário escolher
        lista_datas = sorted(df_etapas["Data"].unique(), key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"), reverse=True)
        data_sel = st.selectbox("Selecione a data da etapa que deseja consultar:", lista_datas)
        
        # Filtra os resultados daquela data específica
        df_filtrado_data = df_etapas[df_etapas["Data"] == data_sel].copy()
        
        # Cria abas por espécie para organizar a lista de ganhadores igual ao painel de torneios
        abas_resultados = st.tabs(especies_validas)
        for i, esp_nome in enumerate(especies_validas):
            with abas_resultados[i]:
                df_res_esp = df_filtrado_data[df_filtrado_data["Espécie"] == esp_nome].copy()
                
                if df_res_esp.empty:
                    st.caption(f"Nenhum resultado registrado para {esp_nome} nesta etapa.")
                else:
                    # Extrai o número da colocação de forma robusta para ordenar corretamente (1, 2, 10, 15...)
                    df_res_esp["Ordem_Col"] = df_res_esp["Colocação"].str.extract(r'(\d+)').astype(int)
                    df_res_esp = df_res_esp.sort_values(by="Ordem_Col").reset_index(drop=True)
                    
                    # Exibe a planilha limpa em modo leitura
                    st.dataframe(
                        df_res_esp[["Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]],
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # --- GERADOR DE RELATÓRIO PDF DESIGNER COM LOGO ---
                    st.write("")
                    if st.button(f"📄 Salvar Relatório Oficial de {esp_nome} em PDF", key=f"pdf_{esp_nome}_{data_sel}", use_container_width=True):
                        pdf_buffer = io.BytesIO()
                        p = canvas.Canvas(pdf_buffer, pagesize=A4)
                        largura_f, altura_f = A4
                        margem_x = 1.5 * cm
                        y_pos = altura_f - 1.5 * cm
                        
                        # Faixa Decorativa Azul Escuro no Cabeçalho
                        p.setFillColor(colors.HexColor("#1E3A8A"))
                        p.rect(margem_x, y_pos - 1.8*cm, largura_f - 2*margem_x, 1.8*cm, fill=True, stroke=False)
                        
                        # Inserção da Logo da ARO com verificação física
                        if os.path.exists(LOGO_PATH):
                            try:
                                p.drawImage(LOGO_PATH, margem_x + 0.3*cm, y_pos - 1.6*cm, width=1.4*cm, height=1.4*cm, mask='auto')
                                texto_offset_x = 2.0 * cm
                            except:
                                texto_offset_x = 0.4 * cm
                        else:
                            texto_offset_x = 0.4 * cm
                            
                        # Textos do Cabeçalho Oficial
                        p.setFillColor(colors.white)
                        p.setFont("Helvetica-Bold", 13)
                        p.drawString(margem_x + texto_offset_x, y_pos - 0.7*cm, "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA")
                        p.setFont("Helvetica", 9)
                        p.drawString(margem_x + texto_offset_x, y_pos - 1.3*cm, f"RELATÓRIO DE RESULTADOS OFICIAIS  |  ETAPA: {data_sel}  |  CATEGORIA: {esp_nome.upper()}")
                        
                        y_pos -= 2.6 * cm
                        
                        # --- CABEÇALHO DA TABELA ---
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
                        
                        # Linhas de Dados com Efeito Zebrado
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
                            
                            # Destaca os pontos em Negrito Azul (Se for 0 pts, fica em cinza)
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
                            label=f"📥 Baixar Relatório PDF Designer - {esp_nome}",
                            data=pdf_buffer,
                            file_name=f"resultado_{esp_nome.lower().replace(' ', '_')}_{data_sel.replace('/', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
# --- TELA 2: CLASSIFICAÇÃO GERAL ACUMULADA DO CAMPEONATO (SOMA AUTOMÁTICA) ---
else:
    st.markdown("### 📊 Classificação Geral do Campeonato Acumulado")
    st.caption("🏆 O ranking abaixo calcula e soma automaticamente todos os pontos conquistados pelas aves em cada etapa realizada.")
    
    if df_etapas.empty:
        st.info("💡 A classificação geral aparecerá assim que os primeiros resultados por etapa forem lançados.")
    else:
        # Agrupa os dados por Ave/Anilha para somar os pontos acumulados de todas as etapas rodadas
        df_ranking = df_etapas.groupby(["Anilha", "Nome da Ave", "Proprietário", "Espécie"])["Pontos"].sum().reset_index()
        df_ranking = df_ranking.rename(columns={"Pontos": "Pontuação Acumulada"})
        
        # Cria as abas por espécie para mostrar quem está liderando o campeonato em cada categoria
        abas_campeonato = st.tabs(especies_validas)
        for i, esp_nome in enumerate(especies_validas):
            with abas_campeonato[i]:
                df_rank_esp = df_ranking[df_ranking["Espécie"] == esp_nome].copy()
                
                if df_rank_esp.empty:
                    st.caption(f"Nenhuma ave da espécie {esp_nome} pontuou no campeonato até o momento.")
                else:
                    # Ordena do maior pontuador para o menor
                    df_rank_esp = df_rank_esp.sort_values(by="Pontuação Acumulada", ascending=False).reset_index(drop=True)
                    
                    # Cria uma coluna visual de posição no campeonato (1º, 2º, 3º...) baseado no índice
                    df_rank_esp.insert(0, "Posição", [f"{x+1}º" for x in df_rank_esp.index])
                    
                    # Exibe a planilha consolidada na tela para os sócios e visitantes conferirem o placar do ano
                    st.dataframe(
                        df_rank_esp[["Posição", "Proprietário", "Nome da Ave", "Anilha", "Pontuação Acumulada"]],
                        hide_index=True,
                        use_container_width=True
                    )

# =========================================================================================
# ⚙️ EXCLUSIVO ADMINISTRATIVO: CENTRAL DE EDIÇÃO, CORREÇÃO E RESET (EXCLUSIVO MASTER)
# =========================================================================================
if role_atual == "master":
    st.write("---")
    st.markdown("### 🛠️ Central de Gerenciamento de Resultados (Master)")
    st.caption("📝 Caso digite uma Anilha, Nome ou Canto errado, corrija diretamente na tabela abaixo. O sistema atualizará a Classificação Geral automaticamente.")
    
    if df_etapas.empty:
        st.caption("Nenhum lançamento para gerenciar ou corrigir no momento.")
    else:
        # Abre a tabela de histórico em modo de edição dinâmica
        df_editado_res = st.data_editor(
            df_etapas,
            hide_index=True,
            column_config={
                "Data": st.column_config.TextColumn("Data", required=True),
                "Espécie": st.column_config.SelectboxColumn("Espécie", options=especies_validas, required=True),
                "Colocação": st.column_config.TextColumn("Colocação", required=True),
                "Proprietário": st.column_config.TextColumn("Proprietário", required=True),
                "Nome da Ave": st.column_config.TextColumn("Nome da Ave", required=True),
                "Anilha": st.column_config.TextColumn("Anilha", required=True),
                "Cantos": st.column_config.NumberColumn("Cantos", min_value=0, step=1),
                "Pontos": st.column_config.NumberColumn("Pontos", min_value=0, step=1)
            },
            key="gerenciador_editor_resultados",
            use_container_width=True
        )
        
        if not df_editado_res.equals(df_etapas):
            df_editado_res = df_editado_res.dropna(subset=["Anilha"]).reset_index(drop=True)
            st.session_state["banco_resultados_viva"]["historico_etapas"] = df_editado_res
            
            with open(ARQUIVO_RESULTADOS, "wb") as f:
                pickle.dump(st.session_state["banco_resultados_viva"], f)
            st.success("🔄 Alterações salvas e sincronizadas no servidor com sucesso!")
            st.rerun()

    st.write("---")
    with st.expander("🗑️ Central de Redefinição de Resultados (Exclusivo Master)"):
        st.warning("🚨 ATENÇÃO: O botão abaixo apagará permanentemente todo o histórico de etapas e pontos acumulados!")
        if st.button("Limpar Todos os Resultados do Banco", use_container_width=True, type="primary"):
            st.session_state["banco_resultados_viva"] = {
                "historico_etapas": pd.DataFrame(columns=["Data", "Espécie", "Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]),
                "campeonato_geral": pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Pontuação Acumulada"])
            }
            with open(ARQUIVO_RESULTADOS, "wb") as f:
                pickle.dump(st.session_state["banco_resultados_viva"], f)
            st.success("Banco de resultados reinicializado com sucesso!")
            st.rerun()
