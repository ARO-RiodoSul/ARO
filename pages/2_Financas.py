if is_master:
    # Mudança aqui: ativamos o num_rows="dynamic" para liberar o botão de adicionar linhas
    df_editado = st.data_editor(
        df_atual,
        hide_index=True,
        num_rows="dynamic",  # <-- LIBERA A ADIÇÃO DE QUANTAS LINHAS QUISER
        column_config={
            "Dia": st.column_config.NumberColumn("Dia", min_value=1, max_value=31, step=1, format="%d"),
            "Entradas": st.column_config.NumberColumn("Entradas (R$)", min_value=0.0, format="%.2f"),
            "Saídas": st.column_config.NumberColumn("Saídas (R$)", min_value=0.0, format="%.2f"),
            "Motivo": st.column_config.TextColumn("Motivo/Descrição")
        },
        disabled=False,
        key=f"editor_{mes_selecionado}"
    )
    
    # Se houver mudanças, salva automaticamente
    if not df_editado.equals(df_atual):
        st.session_state["financas_data"]["meses"][mes_selecionado] = df_editado
        st.rerun()
