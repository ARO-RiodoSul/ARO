import streamlit as st
import pandas as pd
import os, pickle

st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="📊", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "user", "tela_atual": "menu"})

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.columns(3)[1].image("logo.png", use_container_width=True)
    else: st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    with st.form("t_login"):
        u, s = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == "Junior Rebelo" and s == "270688": st.session_state.update({"autenticado": True, "user_role": "master"}); st.rerun()
            elif u == "Kleven" and s == "12345678": st.session_state.update({"autenticado": True, "user_role": "leitor"}); st.rerun()
            else: st.error("Incorreto.")
    st.stop()

if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv("backup_socios.csv") if os.path.exists("backup_socios.csv") else pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 101)])

# CRONOLOGIA DOS MESES DECLARADA DIRETAMENTE SEM O LAÇO COM ERRO
lista_meses = ["Dezembro 2026", 
               "Janeiro 2027", "Fevereiro 2027", "Março 2027", "Abril 2027", "Maio 2027", "Junho 2027", "Julho 2027", "Agosto 2027", "Setembro 2027", "Outubro 2027", "Novembro 2027", "Dezembro 2027",
               "Janeiro 2028", "Fevereiro 2028", "Março 2028", "Abril 2028", "Maio 2028", "Junho 2028", "Julho 2028", "Agosto 2028", "Setembro 2028", "Outubro 2028", "Novembro 2028", "Dezembro 2028"]

if "saldo_anterior_master" not in st.session_state:
    if os.path.exists("backup_saldo_ant.txt"):
        with open("backup_saldo_ant.txt", "r") as f: st.session_state["saldo_anterior_master"] = float(f.read())
    else: st.session_state["saldo_anterior_master"] = 0.0

if "dados_meses_financeiros" not in st.session_state:
    if os.path.exists("backup_financas.pkl"):
        with open("backup_financas.pkl", "rb") as f: st.session_state["dados_meses_financeiros"] = pickle.load(f)
    else:
        st.session_state["dados_meses_financeiros"] = {m: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m in lista_meses}

t_ent = sum(pd.to_numeric(st.session_state["dados_meses_financeiros"][m]["Entradas"], errors='coerce').sum() for m in lista_meses)
t_sai = sum(pd.to_numeric(st.session_state["dados_meses_financeiros"][m]["Saídas"], errors='coerce').sum() for m in lista_meses)
s_ges = t_ent - t_sai
s_tot = t_ent + st.session_state["saldo_anterior_master"] - t_sai

def gerar_relatorio_texto():
    txt = "========================================================\n"
    txt += "        RELATÓRIO FINANCEIRO COMPLETO - ARO RIO DO SUL\n"
    txt += "========================================================\n\n"
    for m in lista_meses:
        df_m_p = st.session_state["dados_meses_financeiros"][m]
        df_at = df_m_p[(df_m_p["Entradas"] > 0) | (df_m_p["Saídas"] > 0) | (df_m_p["Motivo"] != "")]
        m_e, m_s = pd.to_numeric(df_m_p["Entradas"], errors='coerce').sum(), pd.to_numeric(df_m_p["Saídas"], errors='coerce').sum()
        txt += f"--------- PERÍODO: {m} ---------\n"
        if not df_at.empty:
            for _, r in df_at.iterrows():
                txt += f"Dia {int(r['Dia'])} | Entrada: R$ {r['Entradas']:.2f} | Saída: R$ {r['Saídas']:.2f} | Motivo: {r['Motivo']}\n"
        else: txt += "Nenhum lançamento ativo neste mês.\n"
        txt += f"TOTAL ENTRADAS: R$ {m_e:.2f} | TOTAL SAÍDAS: R$ {m_s:.2f} | LÍQUIDO: R$ {(m_e - m_s):.2f}\n\n"
    txt += "========================================================\n"
    txt += "               FECHAMENTO CONSOLIDADO\n"
    txt += "========================================================\n"
    txt += f"🏦 Saldo Anterior: R$ {st.session_state['saldo_anterior_master']:.2f}\n"
    txt += f"🟢 Total de Entradas: R$ {t_ent:.2f}\n"
    txt += f"🔴 Total de Saídas: R$ {t_sai:.2f}\n"
    txt += f"📊 Saldo (Gestão Atual): R$ {s_ges:.2f}\n"
    txt += f"💰 Saldo (Total): R$ {s_tot:.2f}\n"
    return txt

if st.session_state["tela_atual"] == "menu":
    c_l, c_t, c_o = st.columns(3)
    if os.path.exists("logo.png"): c_l.image("logo.png", width=80)
    c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    if c_o.button("🔒 Sair"): st.session_state["autenticado"] = False; st.rerun()
    st.markdown("---")
    cb1, cb2 = st.columns(2)
    if cb1.button("👥 Sócios", use_container_width=True, type="primary"): st.session_state["tela_atual"] = "socios"; st.rerun()
    if cb2.button("🪙 Finanças", use_container_width=True, type="primary"): st.session_state["tela_atual"] = "caixa"; st.rerun()

elif st.session_state["tela_atual"] == "socios":
    if st.button("⬅️ Voltar ao Menu"): st.session_state["tela_atual"] = "menu"; st.rerun()
    st.title("👥 Controle de Sócios")
    if st.session_state["user_role"] == "master":
        df_m = st.data_editor(st.session_state["dados_socios_internos"], use_container_width=True, disabled=["Número"], column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo"])}, hide_index=True)
        if not df_m.equals(st.session_state["dados_socios_internos"]): st.session_state["dados_socios_internos"] = df_m; df_m.to_csv("backup_socios.csv", index=False); st.toast("💾 Salvo!"); st.rerun()
    else: st.dataframe(st.session_state["dados_socios_internos"], use_container_width=True, hide_index=True)

elif st.session_state["tela_atual"] == "caixa":
    if st.button("⬅️ Voltar ao Menu"): st.session_state["tela_atual"] = "menu"; st.rerun()
    st.title("🪙 Controle Financeiro - Finanças")
    
    if st.session_state["user_role"] == "master":
        st.download_button(label="📥 Baixar Relatório Financeiro Geral", data=gerar_relatorio_texto(), file_name="relatorio_financeiro_aro.txt", mime="text/plain", use_container_width=True)
            
    _, c_ant, _ = st.columns(3)
    with c_ant:
        st.markdown("<h3 style='text-align: center;'>🏦 Saldo Anterior</h3>", unsafe_allow_html=True)
        if st.session_state["user_role"] == "master":
            n_v = st.number_input("Editar", value=st.session_state["saldo_anterior_master"], format="%.2f", label_visibility="collapsed")
            if n_v != st.session_state["saldo_anterior_master"]: st.session_state["saldo_anterior_master"] = n_v; open("backup_saldo_ant.txt", "w").write(str(n_v)); st.rerun()
        else: st.markdown(f"<h4 style='text-align: center;'>R$ {st.session_state['saldo_anterior_master']:,.2f}</h4>", unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    cm1, cm2 = st.columns(2)
    cm1.metric("🟢 Total de Entradas", f"R$ {t_ent:,.2f}")
    cm2.metric("🔴 Total de Saídas", f"R$ {t_sai:,.2f}")
    st.markdown("<br>", unsafe_allow_html=True)
    cb1, cb2 = st.columns(2)
    cb1.metric("📊 Saldo (Gestão Atual)", f"R$ {s_ges:,.2f}")
    cb2.metric("💰 Saldo (Total)", f"R$ {s_tot:,.2f}")
    st.markdown("---")
    
    m_sel = st.selectbox("📅 Selecione o Mês de Trabalho:", lista_meses)
    df_m_at = st.session_state["dados_meses_financeiros"][m_sel]
    
    if st.session_state["user_role"] == "master":
        df_m_ed = st.data_editor(df_m_at, use_container_width=True, num_rows="dynamic", hide_index=True, column_config={"Dia": st.column_config.NumberColumn("Dia"), "Entradas": st.column_config.NumberColumn("Entradas", min_value=0.0, format="%.2f"), "Saídas": st.column_config.NumberColumn("Saídas", min_value=0.0, format="%.2f")})
        if not df_m_ed.equals(df_m_at):
            st.session_state["dados_meses_financeiros"][m_sel] = df_m_ed
            with open("backup_financas.pkl", "wb") as f: pickle.dump(st.session_state["dados_meses_financeiros"], f)
            st.toast("💾 Salvo!"); st.rerun()
        with st.expander("➕ Criar Linha Dupla para o mesmo Dia"):
            with st.form("f_ex", clear_on_submit=True):
                cd, ce, cs, cm = st.columns(4)
                d_x = cd.number_input("Dia", min_value=1, max_value=31, value=1)
                e_x, s_x, m_x = ce.number_input("Entrada", min_value=0.0, format="%.2f"), cs.number_input("Saída", min_value=0.0, format="%.2f"), cm.text_input("Motivo")
                if st.form_submit_button("Inserir") and (e_x > 0 or s_x > 0):
                    st.session_state["dados_meses_financeiros"][m_sel] = pd.concat([df_m_ed, pd.DataFrame([{"Dia": d_x, "Entradas": e_x, "Saídas": s_x, "Motivo": m_x}])], ignore_index=True)
                    with open("backup_financas.pkl", "wb") as f: pickle.dump(st.session_state["dados_meses_financeiros"], f)
                    st.toast("💾 Salvo!"); st.rerun()
    else: st.dataframe(df_m_at, use_container_width=True, hide_index=True)

    st.markdown("---")
    m_e = pd.to_numeric(df_m_at["Entradas"], errors='coerce').sum()
    m_s = pd.to_numeric(df_m_at["Saídas"], errors='coerce').sum()
    st.write(f"📊 **Mês Atual - Entradas:** R$ {m_e:,.2f} | **Saídas:** R$ {m_s:,.2f} | **Líquido:** R$ {(m_e - m_s):,.2f}")
