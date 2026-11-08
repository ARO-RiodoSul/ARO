def gerar_relatorio_texto():
    txt = "=== RELATÓRIO FINANCEIRO GERAL - ARO ===\n\n"
    # Garante que o dicionário de meses existe no session_state
    if "financas_data" in st.session_state and "meses" in st.session_state["financas_data"]:
        for mes, df_at in st.session_state["financas_data"]["meses"].items():
            if df_at is not None and not df_at.empty:
                txt += f"\n--- Mês: {mes} ---\n"
                for _, r in df_at.iterrows():
                    # CORREÇÃO: Ignora a linha se o Dia ou o Motivo estiverem em branco/nulos
                    if pd.isna(r['Dia']) or str(r['Dia']).strip() == "" or pd.isna(r['Motivo']):
                        continue
                    
                    try:
                        dia_int = int(float(r['Dia']))
                        entrada_val = float(r['Entradas']) if pd.notna(r['Entradas']) else 0.0
                        saida_val = float(r['Saídas']) if pd.notna(r['Saídas']) else 0.0
                        motivo_txt = r['Motivo']
                        
                        txt += f"Dia {dia_int:02d} | Entrada: R$ {entrada_val:.2f} | Saída: R$ {saida_val:.2f} | Motivo: {motivo_txt}\n"
                    except (ValueError, TypeError):
                        # Se houver algum erro de conversão na linha incompleta, apenas pula ela
                        continue
    return txt
