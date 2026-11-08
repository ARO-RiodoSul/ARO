import streamlit as st
import pandas as pd
import datetime
import random

# Configuração da página
st.set_page_config(page_title="Torneios - Painel ARO", page_icon="🦅", layout="wide")

# Título do Módulo
st.title("🦅 Gestão de Torneios - ARO Rio do Sul")

# Validar nível de acesso
is_master = st.session_state.get("user_role") == "master"

# Sincronização e inicialização da data global
if "data_torneio_aro" not in st.session_state or st.session_state["data_torneio_aro"] is None:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)
elif isinstance(st.session_state["data_torneio_aro"], str):
    try:
        st.session_state["data_torneio_aro"] = datetime.datetime.strptime(st.session_state["data_torneio_aro"], "%Y-%m-%d").date()
    except ValueError:
        try:
            st.session_state["data_torneio_aro"] = datetime.datetime.strptime(st.session_state["data_torneio_aro"], "%d/%m/%Y").date()
        except ValueError:
            st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)

# Inicializar banco de inscrições se não existir
if "torneio_inscricoes_aro" not in st.session_state:
    st.session_state["torneio_inscricoes_aro"] = pd.DataFrame(
        columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca"]
    )

df_inscritos = st.session_state["torneio_inscricoes_aro"]

# --- 1. CABEÇALHO COM DATA EDITÁVEL (EXCLUSIVO MASTER) ---
st.markdown("### 📅 Cronograma do Evento")
if is_master:
    nova_data = st.date_input("Data do Torneio:", value=st.session_state["data_torneio_aro"], format="DD/MM/YYYY", key="edit_data_torneio")
    if nova_data != st.session_state["data_torneio_aro"]:
        st.session_state["data_torneio_aro"] = nova_data
        st.rerun()
else:
    st.markdown(f"**Torneio Dia:** {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}")

st.write("---")

# --- 2. ÍCONES E CONTADORES LIMPOS POR ESPÉCIE + TOTALIZADOR ---
st.markdown("### 📊 Estatísticas de Inscrição")

especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
icones_especies = {
    "Trinca Ferro": "🪵 Trinca Ferro",
    "Coleiro": "🌾 Coleiro",
    "Bico de Pimenta": "🌶️ Bico de Pimenta",
    "Canário": "🟡 Canário",
    "Azulão": "🔷 Azulão",
    "Tiziu": "🕶️ Tiziu"
}

# Calcular quantidades atuais por espécie
contagem = {esp: 0 for esp in especies_validas}
total_geral_inscritos = 0
if not df_inscritos.empty:
    total_geral_inscritos = len(df_inscritos)
    for esp in especies_validas:
        contagem[esp] = len(df_inscritos[df_inscritos["Espécie"] == esp])

# Exibir os contadores mostrando apenas o número puro (sem a palavra 'inscrito')
cols_contador = st.columns(6)
for i, esp in enumerate(especies_validas):
    with cols_contador[i]:
        st.metric(label=icones_especies[esp], value=str(contagem[esp]))

# Adição do Totalizador Geral embaixo da lista de espécies
st.write("")
st.info(f"✨ **TOTAL DE AVES INSCRITAS NO TORNEIO:** {total_geral_inscritos} aves cadastradas.")
st.write("---")

# --- 3. FORMULÁRIO DE INSCRIÇÃO (EXCLUSIVO MASTER) ---
if is_master:
    st.markdown("### 📝 Nova Inscrição de Ave")
    
    with st.form("formulario_inscricao", clear_on_submit=True):
        proprietario = st.text_input("Proprietário:")
        nome_ave = st.text_input("Nome da Ave:")
        especie = st.selectbox("Espécie:", especies_validas)
        anilha = st.text_input("Anilha:")
        
        botao_inscrever = st.form_submit_button("Inscrever Ave", use_container_width=True)
        
        if botao_inscrever:
            if proprietario.strip() == "" or nome_ave.strip() == "" or anilha.strip() == "":
                st.error("Por favor, preencha todos os campos para efetuar a inscrição.")
            else:
                estacas_ocupadas = df_inscritos[df_inscritos["Espécie"] == especie]["Estaca"].tolist()
                
                if especie in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"]:
                    limite_inicial = 50
                elif especie in ["Canário", "Azulão"]:
                    limite_inicial = 25
                elif especie == "Tiziu":
                    limite_inicial = 5
                
                estacas_livres = [e for e in range(1, limite_inicial + 1) if e not in estacas_ocupadas]
                
                if estacas_livres:
                    estaca_sorteada = random.choice(estacas_livres)
                else:
                    if estacas_ocupadas:
                        estaca_sorteada = max(estacas_ocupadas) + 1
                    else:
                        estaca_sorteada = limite_inicial + 1
                
                nova_inscricao = pd.DataFrame([{
                    "Proprietário": proprietario.strip(),
                    "Nome da Ave": nome_ave.strip(),
                    "Espécie": especie,
                    "Anilha": anilha.strip(),
                    "Estaca": int(estaca_sorteada)
                }])
                
                st.session_state["torneio_inscricoes_aro"] = pd.concat([df_inscritos, nova_inscricao], ignore_index=True)
                st.success(f"Sucesso! Ave '{nome_ave}' inscrita na Espécie {especie} | Estaca Selecionada: {estaca_sorteada}")
                st.rerun()
    st.write("---")

# --- 4. EXIBIÇÃO DE PLANILHAS SEPARADAS DENTRO DAS ESPÉCIES ---
st.markdown("### 🏆 Competidores por Categoria")

abas_especies = st.tabs([icones_especies[esp] for esp in especies_validas])

for i, esp in enumerate(especies_validas):
    with abas_especies[i]:
        df_filtrado = df_inscritos[df_inscritos["Espécie"] == esp]
        
        if df_filtrado.empty:
            st.info(f"Nenhum pássaro cadastrado na categoria {esp} até o momento.")
        else:
            df_ordenado = df_filtrado.sort_values(by="Estaca").reset_index(drop=True)
            
            st.dataframe(
                df_ordenado[["Estaca", "Nome da Ave", "Proprietário", "Anilha"]],
                hide_index=True,
                column_config={
                    "Estaca": st.column_config.NumberColumn("Estaca / Gaiola", format="%d"),
                    "Nome da Ave": "Nome do Pássaro",
                    "Proprietário": "Proprietário / Criador",
                    "Anilha": "Nº da Anilha"
                },
                use_container_width=True
            )
