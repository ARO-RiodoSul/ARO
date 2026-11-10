import streamlit as st
import pandas as pd
import datetime, pickle, os

st.set_page_config(page_title="Resultados - ARO", page_icon="🏆", layout="wide")

if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

st.title("🏆 Resultados e Classificação Geral - ARO")

role_atual = str(st.session_state.get("user_role", "")).strip().lower()
is_admin = role_atual in ["master", "diretoria", "admin"]
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]

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

# Inicializa o banco de dados na sessão viva do app
if "banco_resultados_viva" not in st.session_state:
    st.session_state["banco_resultados_viva"] = carregar_resultados_fisicos()

dados_resultados = st.session_state["banco_resultados_viva"]
df_etapas = dados_resultados["historico_etapas"]

# --- MENU DE OPÇÕES NO TOPO ---
opcao_tela = st.radio("Selecione a visualização desejada:", ["📅 Resultados por Etapa", "📊 Classificação Geral do Campeonato"], horizontal=True)

# =========================================================================================
# ⚙️ FORMULÁRIO DE LANÇAMENTO EXCLUSIVO: MASTER / DIRETORIA
# =========================================================================================
if is_admin:
    st.write("---")
    exp_cadastro = st.expander("📝 Painel de Lançamento de Resultados (Exclusivo Master/Diretoria)")
    with exp_cadastro:
        with st.form("form_cadastro_resultado", clear_on_submit=True):
            col_r1, col_r2, col_r3 = st.columns(3)
            r_data = col_r1.date_input("Data da Etapa:", datetime.date.today())
            r_especie = col_r2.selectbox("Espécie:", especies_validas)
            r_colocacao = col_r3.selectbox("Colocação:", [f"{i}º Lugar" for i in range(1, 11)])
            
            col_r4, col_r5, col_r6 = st.columns(3)
            r_proprietario = col_r4.text_input("Proprietário:")
            r_ave = col_r5.text_input("Nome da Ave:")
            r_anilha = col_r6.text_input("Anilha:")
            
            col_r7, col_r8 = st.columns(2)
            r_cantos = col_r7.number_input("Quantidade de Cantos:", min_value=0, step=1, value=0)
            
            # Tabela de pontuação padrão do campeonato (ex: 1º ganha 10pts, 2º ganha 9pts...)
            pontos_map = {"1º Lugar": 10, "2º Lugar": 9, "3º Lugar": 8, "4º Lugar": 7, "5º Lugar": 6, "6º Lugar": 5, "7º Lugar": 4, "8º Lugar": 3, "9º Lugar": 2, "10º Lugar": 1}
            r_pontos = pontos_map.get(r_colocacao, 0)
            
            st.markdown(f"**Pontuação automática para {r_colocacao}:** `{r_pontos} pontos`")
            
            if st.form_submit_button("Salvar Resultado no Servidor", use_container_width=True):
                if not r_proprietario.strip() or not r_ave.strip() or not r_anilha.strip():
                    st.error("❌ Por favor, preencha todos os campos do competidor.")
                else:
                    # Cria a nova linha estruturada
                    novo_registro = pd.DataFrame([{
                        "Data": r_data.strftime("%d/%m/%Y"),
                        "Espécie": r_especie,
                        "Colocação": r_colocacao,
                        "Proprietário": r_proprietario.strip(),
                        "Nome da Ave": r_ave.strip(),
                        "Anilha": r_anilha.strip(),
                        "Cantos": int(r_cantos),
                        "Pontos": int(r_pontos)
                    }])
                    
                    # Anexa e salva no arquivo físico pkl
                    st.session_state["banco_resultados_viva"]["historico_etapas"] = pd.concat([df_etapas, novo_registro], ignore_index=True)
                    salvar_resultados_fisicos(st.session_state["banco_resultados_viva"])
                    st.success("🎯 Resultado cadastrado e computado com sucesso!"); st.rerun()

# =========================================================================================
# 📊 EXIBIÇÃO DOS DADOS: VISÍVEL PARA MASTER, DIRETORIA, SÓCIOS E VISITANTES
# =========================================================================================
st.write("")

# --- TELA 1: RESULTADOS POR ETAPA (FILTRADO POR DATA) ---
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
                    # Força a ordenação correta do 1º ao 10º colocado
                    df_res_esp["Ordem_Col"] = df_res_esp["Colocação"].str.extract(r'(\d+)').astype(int)
                    df_res_esp = df_res_esp.sort_values(by="Ordem_Col").reset_index(drop=True)
                    
                    # Exibe a planilha limpa em modo leitura
                    st.dataframe(
                        df_res_esp[["Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]],
                        hide_index=True,
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

# --- BOTÃO EXCLUSIVO MASTER PARA RESETAR O CAMPEONATO SE NECESSÁRIO ---
if role_atual == "master":
    st.write("---")
    with st.expander("🗑️ Central de Redefinição de Resultados (Exclusivo Master)"):
        st.warning("🚨 ATENÇÃO: O botão abaixo apagará permanentemente todo o histórico de etapas e pontos acumulados!")
        if st.button("Limpar Todos os Resultados do Banco", use_container_width=True, type="primary"):
            st.session_state["banco_resultados_viva"] = {
                "historico_etapas": pd.DataFrame(columns=["Data", "Espécie", "Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]),
                "campeonato_geral": pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Pontuação Acumulada"])
            }
            salvar_resultados_files = st.session_state["banco_resultados_viva"]
            with open(ARQUIVO_RESULTS if 'ARQUIVO_RESULTS' in locals() else ARQUIVO_RESULTADOS, "wb") as f:
                pickle.dump(st.session_state["banco_resultados_viva"], f)
            st.success("Banco de resultados reinicializado com sucesso!")
            st.rerun()
