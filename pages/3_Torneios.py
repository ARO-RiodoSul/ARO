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

# Sincronização automática com a data definida na página inicial (app.py)
if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)

# Inicializar banco de inscrições no session_state se não existir
if "torneio_inscricoes_aro" not in st.session_state:
    st.session_state["torneio_inscricoes_aro"] = pd.DataFrame(
        columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca"]
    )

df_inscritos = st.session_state["torneio_inscricoes_aro"]

# --- 1. CABEÇALHO COM DATA ---
st.markdown(f"### 📅 Torneio Dia: **{st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}**")
st.caption("A data do torneio acima é alterada exclusivamente na página inicial (app.py) pelo usuário Master.")

st.write("---")

# --- 2. ÍCONES E CONTADORES POR ESPÉCIE ---
st.markdown("### 📊 Inscrições por Espécie")

# Lista oficial de espécies suportadas
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
icones_especies = {
    "Trinca Ferro": "🪵 Trinca Ferro",
    "Coleiro": "🌾 Coleiro",
    "Bico de Pimenta": "🌶️ Bico de Pimenta",
    "Canário": "🟡 Canário",
    "Azulão": "🔷 Azulão",
    "Tiziu": "🕶️ Tiziu"
}

# Calcular quantidades atuais
contagem = {esp: 0 for esp in especies_validas}
if not df_inscritos.empty:
    for esp in especies_validas:
        contagem[esp] = len(df_inscritos[df_inscritos["Espécie"] == esp])

# Exibir os contadores em colunas amigáveis
cols_contador = st.columns(6)
for i, esp in enumerate(especies_validas):
    with cols_contador[i]:
        st.metric(label=icones_especies[esp], value=f"{contagem[esp]} inscritos")

st.write("---")

# --- 3. FORMULÁRIO DE INSCRIÇÃO (EXCLUSIVO MASTER) ---
if is_master:
    st.markdown("### 📝 Nova Inscrição de Ave")
    
    # Criando o formulário com os 4 campos solicitados
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
                # Filtrar estacas já ocupadas pela mesma espécie para evitar duplicados
                estacas_ocupadas = df_inscritos[df_inscritos["Espécie"] == especie]["Estaca"].tolist()
                
                # Definir limites de sorteio conforme a regra de cada espécie
                if especie in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"]:
                    limite_inicial = 50
                elif especie in ["Canário", "Azulão"]:
                    limite_inicial = 25
                elif especie == "Tiziu":
                    limite_inicial = 5
                
                # Gerar lista de estacas livres dentro do range padrão
                estacas_livres = [e for e in range(1, limite_inicial + 1) if e not in estacas_ocupadas]
                
                # Se ainda houver vaga no sorteio inicial, sorteia. Se não, pega o próximo número sequencial livre
                if estacas_livres:
                    estaca_sorteada = random.choice(estacas_livres)
                else:
                    # Se estourar os números aleatórios, pega o maior número existente da espécie + 1
                    if estacas_ocupadas:
                        estaca_sorteada = max(estacas_ocupadas) + 1
                    else:
                        estaca_sorteada = limite_inicial + 1
                
                # Nova linha de registro
                nova_inscricao = pd.DataFrame([{
                    "Proprietário": proprietario.strip(),
                    "Nome da Ave": nome_ave.strip(),
                    "Espécie": especie,
                    "Anilha": anilha.strip(),
                    "Estaca": int(estaca_sorteada)
                }])
                
                # Salvar no session_state global
                st.session_state["torneio_inscricoes_aro"] = pd.concat([df_inscritos, nova_inscricao], ignore_index=True)
                st.success(f"Sucesso! Ave '{nome_ave}' inscrita na Espécie {especie} | Estaca Definida: {estaca_sorteada}")
                st.rerun()
    st.write("---")

# --- 4. EXIBIÇÃO DE PLANILHAS SEPARADAS DENTRO DAS ESPÉCIES ---
st.markdown("### 🏆 Competidores por Categoria")

# Abas interativas para separar os pássaros de forma limpa
abas_especies = st.tabs([icones_especies[esp] for esp in especies_validas])

for i, esp in enumerate(especies_validas):
    with abas_especies[i]:
        # Filtrar apenas as aves pertencentes a esta espécie específica
        df_filtrado = df_inscritos[df_inscritos["Espécie"] == esp]
        
        if df_filtrado.empty:
            st.info(f"Nenhum pássaro cadastrado na categoria {esp} até o momento.")
        else:
            # Ordenar automaticamente pela coluna Estaca para facilitar a leitura física
            df_ordenado = df_filtrado.sort_values(by="Estaca").reset_index(drop=True)
            
            # Formatação de exibição da planilha final com a coluna de estacas gerada pelo app
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

