def gerar_relatorio_texto():
    txt = "=== RELATÓRIO FINANCEIRO GERAL - ARO ===\n\n"
    if "financas_data" in st.session_state and "meses" in st.session_state["financas_data"]:
        for mes, df_at in st.session_state["financas_data"]["meses"].items():
            if df_at is not None and not df_at.empty:
                txt += f"\n--- Mês: {mes} ---\n"
                for _, r in df_at.iterrows():
                    # Ignorar linhas em branco ou nulas adicionadas dinamicamente
                    if pd.isna(r.get('Dia')) or str(r.get('Dia')).strip() == "" or pd.isna(r.get('Motivo')):
                        continue
                    try:
                        dia_int = int(float(r['Dia']))
                        ent = float(r['Entradas']) if pd.notna(r['Entradas']) else 0.0
                        sai = float(r['Saídas']) if pd.notna(r['Saídas']) else 0.0
                        mot = r['Motivo']
                        txt += f"Dia {dia_int:02d} | Entrada: R$ {ent:.2f} | Saída: R$ {sai:.2f} | Motivo: {mot}\n"
                    except:
                        continue
    return txt
