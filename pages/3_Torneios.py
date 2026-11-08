import streamlit as st
import pandas as pd
import datetime

# Configuração da página
st.set_page_config(page_title="Torneios - Painel ARO", page_icon="🦅", layout="wide")

# Título do Módulo
st.title("🦅 Gestão de Torneios - ARO Rio do Sul")

# Validar nível de acesso (Apenas o perfil master edita)
is_master = st.session_state.get("user_role") == "master"

# Inicializar dados dos torneios no session_state se não existiren
if "torneios_data" not in st.session_state:
    st.session_state["torneios_data"] = {
        "modalidades": ["Canto Fibra", "Canto Livre", "Canto Clássico"],
        "inscritos": pd.DataFrame(
            columns=["Sócio", "Estaca/Gaiola", "Nome do Canário", "Modalidade", "Pontuação/Tempo", "Status"]
        )
    }

# Sincronização automática com a data definida na página inicial (app.py)
if "data_torneio_aro" not in st.session_state:
    st.session_state["data_torneio_aro"] = datetime.date(2026, 12, 6)

# --- 1. RESUMO E CRONOGRAMA ---
st.markdown("### 📅 Próximo Evento Oficial")

col_info_1, col_info_2 = st.columns(2)
with col_info_1:
    st.metric(
        label="Data do Próximo Torneio ARO",
        value=st.session_state["data_torneio_aro"].strftime('%d/%m/%Y')
    )
with col_info_2:
    total_inscritos = len(st.session_state["torneios_data"]["inscritos"])
    st.metric(label="Total de Canários Inscritos", value=str(total_inscritos))

st.write("---")

# --- 2. PAINEL DE INSCRIÇÕES E ESTACAS ---
st.markdown("### 📝 Inscrições e Marcação de Estacas")

df_inscritos = st.session_state["torneios_data"]["inscritos"]

if is_master:
    st.caption("💡 Use o botão '+' no rodapé da tabela para adicionar competidores. Ao salvar, o sistema ordena as linhas automaticamente pelo número da estaca.")
    
    # Editor dinâmico liberado para o Junior Rebelo
    df_editado = st.data_editor(
        df_inscritos,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Sócio": st.column_config.TextColumn("Nome do Sócio/Criador", required=True),
            "Estaca/Gaiola": st.column_config.NumberColumn("Nº Estaca / Gaiola", min_value=1, step=1, format="%d", required=True),
            "Nome do Canário": st.column_config.TextColumn("Nome do Pássaro", required=True),
            "Modalidade": st.column_config.SelectboxColumn(
                "Modalidade", 
                options=st.session_state["torneios_data"]["modalidades"],
                required=True
            ),
            "Pontuação/Tempo": st.column_config.NumberColumn("Cantos / Segundos", min_value=0, step=1, format="%d", default=0),
            "Status": st.column_config.SelectboxColumn(
                "Status", 
                options=["Inscrito", "Classificado", "Desclassificado"], 
                default="Inscrito",
                required=True
            )
        },
        disabled=False,
        key="editor_torneios_dinamico"
    )
    
    # Ordenação automática numérica por estaca/gaiola após edição
    if not df_editado.equals(df_inscritos):
        df_editado["Estaca/Gaiola"] = pd.to_numeric(df_editado["Estaca/Gaiola"], errors='coerce')
        df_editado = df_editado.dropna(subset=["Estaca/Gaiola"]).sort_values(by="Estaca/Gaiola").reset_index(drop=True)
        st.session_state["torneios_data"]["inscritos"] = df_editado
        st.rerun()

else:
    # Bloqueio total de edição para modo leitura
    if df_inscritos.empty:
        st.info("Nenhum canário cadastrado para o próximo torneio.")
    else:
        st.dataframe(
            df_inscritos,
            hide_index=True,
            column_config={
                "Sócio": "Sócio/Criador",
                "Estaca/Gaiola": "Nº Estaca",
                "Nome do Canário": "Canário",
                "Modalidade": "Modalidade",
                "Pontuação/Tempo": "Resultado (Cantos)",
                "Status": "Status"
            },
            use_container_width=True
        )

# --- 3. RELATÓRIO DE TOQUEIRA IMPRIMÍVEL ---
if is_master and not df_inscritos.empty:
    st.write("---")
    st.markdown("### 🖨️ Prancheta de Mesa (Toqueira)")
    
    if st.button("Gerar Lista de Conferência para Impressão", use_container_width=True):
        st.success("Lista expandida abaixo! Use Ctrl+P para imprimir as planilhas de contagem física.")
        st.write("---")
        
        st.markdown("<h2 style='text-align: center;'>🦅 ARO - LISTA DE CONFERÊNCIA E CLASSIFICAÇÃO</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'><b>Torneio Oficial de:</b> {st.session_state['data_torneio_aro'].strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
        
        # Filtra e divide o relatório por modalidade em páginas separadas
        for mod in st.session_state["torneios_data"]["modalidades"]:
            df_mod = df_inscritos[df_inscritos["Modalidade"] == mod]
            st.markdown(f"#### 🏆 Categoria: {mod}")
            
            if not df_mod.empty:
                st.table(df_mod[["Estaca/Gaiola", "Nome do Canário", "Sócio", "Pontuação/Tempo", "Status"]].rename(
                    columns={"Pontuação/Tempo": "Contagem Final", "Sócio": "Criador"}
                ))
            else:
                st.caption("Sem competidores nesta modalidade.")
            st.markdown("<div style='page-break-after: always;'></div>", unsafe_allow_html=True)

