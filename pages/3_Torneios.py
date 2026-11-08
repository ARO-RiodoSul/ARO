import streamlit as st
import pandas as pd
import datetime
import random
from PIL import Image, ImageDraw
import io

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

# Exibir os contadores mostrando apenas o número puro
cols_contador = st.columns(6)
for i, esp in enumerate(especies_validas):
    with cols_contador[i]:
        st.metric(label=icones_especies[esp], value=str(contagem[esp]))

# Totalizador Geral embaixo da lista de espécies
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
                    staca_sorteada = random.choice(estacas_livres)
                else:
                    if estacas_ocupadas:
                        staca_sorteada = max(estacas_ocupadas) + 1
                    else:
                        staca_sorteada = limite_inicial + 1
                
                nova_inscricao = pd.DataFrame([{
                    "Proprietário": proprietario.strip(),
                    "Nome da Ave": nome_ave.strip(),
                    "Espécie": especie,
                    "Anilha": anilha.strip(),
                    "Estaca": int(staca_sorteada)
                }])
                
                st.session_state["torneio_inscricoes_aro"] = pd.concat([df_inscritos, nova_inscricao], ignore_index=True)
                st.success(f"Sucesso! Ave '{nome_ave}' inscrita na Espécie {especie} | Estaca Selecionada: {staca_sorteada}")
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

# --- 5. FUNÇÃO PARA GERAR A IMAGEM DA TABELA SIMPLES DE INFORMAÇÕES ---
def criar_imagem_tabela(data_t, mapa_contagem, total_g):
    W, H = 600, 520
    img = Image.new("RGB", (W, H), "#111625")
    draw = ImageDraw.Draw(img)
    
    # Moldura dourada minimalista
    draw.rectangle([20, 20, W-20, H-20], outline="#D4AF37", width=2)
    
    # Textos do Cabeçalho
    draw.text((W/2, 50), "ARO - RIO DO SUL", fill="#D4AF37", anchor="mm", font_size=26)
    draw.text((W/2, 90), f"TORNEIO DIA: {data_t}", fill="#FFFFFF", anchor="mm", font_size=20)
    
    # Cabeçalho da Tabela
    draw.line([40, 130, W-40, 130], fill="#D4AF37", width=2)
    draw.text((50, 145), "ESPÉCIE", fill="#D4AF37", font_size=16)
    draw.text((W-50, 145), "QUANTIDADE", fill="#D4AF37", anchor="ra", font_size=16)
    draw.line([40, 175, W-40, 175], fill="#D4AF37", width=1)
    
    # Linhas da tabela
    y_pos = 190
    for esp, qtd in mapa_contagem.items():
        draw.text((50, y_pos), esp.upper(), fill="#FFFFFF", font_size=16)
        draw.text((W-50, y_pos), str(qtd), fill="#FFFFFF", anchor="ra", font_size=16)
        draw.line([40, y_pos+25, W-40, y_pos+25], fill="#2D3748", width=1)
        y_pos += 40
        
    # Rodapé da Tabela com Total Acumulado
    draw.line([40, y_pos, W-40, y_pos], fill="#D4AF37", width=2)
    draw.text((50, y_pos+15), "TOTAL GERAL DE GAIOLAS", fill="#D4AF37", font_size=18)
    draw.text((W-50, y_pos+15), str(total_g), fill="#D4AF37", anchor="ra", font_size=18)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 6. CENTRAL DE EXPORTAÇÃO E EXCLUSÃO MANUAL PARA CELULAR (EXCLUSIVO MASTER) ---
if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 📊 Exportação e Compartilhamento")
    
    data_str = st.session_state["data_torneio_aro"].strftime('%d/%m/%Y')
    img_bytes = criar_imagem_tabela(data_str, contagem, total_geral_inscritos)
    
    st.image(img_bytes, width=400, caption="Informativo Oficial de Inscrições")
    
    st.download_button(
        label="📥 Baixar Cartaz para WhatsApp (Imagem PNG)",
        data=img_bytes,
        file_name=f"aro_tabela_inscritos_{st.session_state['data_torneio_aro'].strftime('%Y_%m_%d')}.png",
        mime="image/png",
        use_container_width=True
    )
    
    st.write("---")
    st.markdown("### 🗑️ Cancelar Inscrição (Remover Ave)")
    st.caption("Desenvolvido para exclusão rápida via celular sem depender de teclado físico.")
    
    opcoes_exclusao = []
    for idx, row in df_inscritos.iterrows():
        opcoes_exclusao.append(f"[{row['Espécie']}] Estaca {row['Estaca']} - {row['Nome da Ave']} (Criador: {row['Proprietário']})")
    
    ave_selecionada_txt = st.selectbox("Selecione a ave que deseja remover:", opcoes_exclusao, key="combo_deletar_ave")
    confirmar_check = st.checkbox("⚠️ Marque aqui para confirmar que deseja excluir esta ave", key="check_seguranca_ave")
    
    if st.button("❌ Deletar Ave Selecionada", type="secondary", use_container_width=True):
        if confirmar_check:
            posicao_lista = opcoes_exclusao.index(ave_selecionada_txt)
            indice_original = df_inscritos.index[posicao_lista]
            
            st.session_state["torneio_inscricoes_aro"] = df_inscritos.drop(indice_original).reset_index(drop=True)
            st.success("A ave foi removida do torneio com sucesso!")
            st.rerun()
        else:
            st.error("Por favor, marque a caixa de confirmação de segurança antes de clicar em deletar.")

# --- 7. RECURSO DE ZERAR TORNEIO COMPLETO (EXCLUSIVO MASTER) ---
if is_master:
    st.write("---")
