import streamlit as st
import pandas as pd
import os, pickle, random
from datetime import datetime

# CONFIGURAÇÃO DO APP E ÍCONE DO NAVEGADOR
st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="logo.png" if os.path.exists("logo.png") else "📊", layout="wide")

# FORÇAR CONFIGURAÇÃO DE LOGO NO CELULAR
st.markdown("""<head><title>ARO</title><link rel="apple-touch-icon" href="app/static/logo.png"><link rel="icon" type="image/png" href="app/static/logo.png"></head>""", unsafe_allow_html=True)

if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "user", "tela_atual": "menu"})

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        _, col_img, _ = st.columns(3)
        col_img.image("logo.png", use_container_width=True)
    else: st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    with st.form("t_login"):
        u, s = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == "Junior Rebelo" and s == "270688": st.session_state.update({"autenticado": True, "user_role": "master"}); st.rerun()
            elif u == "Kleven" and s == "12345678": st.session_state.update({"autenticado": True, "user_role": "leitor"}); st.rerun()
            else: st.error("Incorreto.")
    st.stop()

# --- CARREGAMENTO DE BANCOS DE DADOS ---
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv("backup_socios.csv") if os.path.exists("backup_socios.csv") else pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])

lista_meses = ["Dezembro 2026"] + [f"{m} {a}" for a in ["2027", "2028"] for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]]

if "saldo_anterior_master" not in st.session_state:
    if os.path.exists("backup_saldo_ant.txt"):
        with open("backup_saldo_ant.txt", "r") as f: st.session_state["saldo_anterior_master"] = float(f.read())
    else: st.session_state["saldo_anterior_master"] = 0.0

if "dados_meses_financeiros" not in st.session_state:
    st.session_state["dados_meses_financeiros"] = pickle.load(open("backup_financas.pkl", "rb")) if os.path.exists("backup_financas.pkl") else {m: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m in lista_meses}

if "data_torneio_aro" not in st.session_state:
    if os.path.exists("backup_data_torneio.txt"):
        with open("backup_data_torneio.txt", "r") as f: st.session_state["data_torneio_aro"] = f.read()
    else: st.session_state["data_torneio_aro"] = datetime.now().strftime("%d/%m/%Y")

if "dados_torneios_internos" not in st.session_state:
    st.session_state["dados_torneios_internos"] = pickle.load(open("backup_torneios_v2.pkl", "rb")) if os.path.exists("backup_torneios_v2.pkl") else pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca"])

t_ent = sum(pd.to_numeric(st.session_state["dados_meses_financeiros"][m]["Entradas"], errors='coerce').sum() for m in lista_meses)
t_sai = sum(pd.to_numeric(st.session_state["dados_meses_financeiros"][m]["Saídas"], errors='coerce').sum() for m in lista_meses)
s_ges, s_tot = t_ent - t_sai, t_ent + st.session_state["saldo_anterior_master"] - t_sai

# --- LÓGICA DE SORTEIO DE ESTACAS AUTOMÁTICA ---
def sortear_estaca(esp, df_t):
    ocupadas = df_t[df_t["Espécie"] == esp]["Estaca"].tolist()
    lim, prox = (50, 51) if esp in ["Trinca Ferro", "Coleiro", "Bico de Pimenta"] else ((25, 26) if esp in ["Canário", "Azulão"] else (5, 6))
    livres = [x for x in range(1, lim + 1) if x not in ocupadas]
    if livres: return random.choice(livres)
    while prox in ocupadas: prox += 1
    return prox

# --- TELA 1: MENU PRINCIPAL ---
if st.session_state["tela_atual"] == "menu":
    c_l, c_t, c_o = st.columns(3)
    try:
        if os.path.exists("logo.png"): c_l.image("logo.png", width=80)
    except: pass
    c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    if c_o.button("🔒 Sair"): st.session_state["autenticado"] = False; st.rerun()
    st.markdown("---")
    cb1, cb2, cb3 = st.columns(3)
    if cb1.button("👥 Sócios", use_container_width=True, type="primary"): st.session_state["tela_atual"] = "socios"; st.rerun()
    if cb2.button("🪙 Finanças", use_container_width=True, type="primary"): st.session_state["tela_atual"] = "caixa"; st.rerun()
    if cb3.button("🏆 Torneios", use_container_width=True, type="primary"): st.session_state["tela_atual"] = "torneios"; st.rerun()

# --- TELA 2: SÓCIOS ---
elif st.session_state["tela_atual"] == "socios":
    if st.button("⬅️ Voltar ao Menu"): st.session_state["tela_atual"] = "menu"; st.rerun()
    st.title("👥 Controle de Sócios")
    if st.session_state["user_role"] == "master":
        df_m = st.data_editor(st.session_state["dados_socios_internos"], use_container_width=True, disabled=["Número"], column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo"])}, hide_index=True)
        if not df_m.equals(st.session_state["dados_socios_internos"]): 
            st.session_state["dados_socios_internos"] = df_m
            df_m.to_csv("backup_socios.csv", index=False); st.toast("💾 Salvo!"); st.rerun()
        if st.button("➕ Adicionar Linha para Novo Sócio"):
            p_n = len(st.session_state["dados_socios_internos"]) + 1
            st.session_state["dados_socios_internos"] = pd.concat([st.session_state["dados_socios_internos"], pd.DataFrame([{"Número": p_n, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"}])], ignore_index=True)
            st.session_state["dados_socios_internos"].to_csv("backup_socios.csv", index=False); st.rerun()
    else: st.dataframe(st.session_state["dados_socios_internos"], use_container_width=True, hide_index=True)

# --- TELA 3: FINANÇAS ---
elif st.session_state["tela_atual"] == "caixa":
    if st.button("⬅️ Voltar ao Menu"): st.session_state["tela_atual"] = "menu"; st.rerun()
    st.title("🪙 Controle Financeiro - Finanças")
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
            pickle.dump(st.session_state["dados_meses_financeiros"], open("backup_financas.pkl", "wb"))
            st.toast("💾 Salvo!"); st.rerun()
    else: st.dataframe(df_m_at, use_container_width=True, hide_index=True)

# --- TELA 4: TORNEIOS ---
elif st.session_state["tela_atual"] == "torneios":
    if st.button("⬅️ Voltar ao Menu"): st.session_state["tela_atual"] = "menu"; st.rerun()
    st.title("🏆 Gerenciamento de Torneios & Inscrições")
    st.markdown("---")
    
    _, c_date, _ = st.columns(3)
    with c_date:
        st.markdown("📅 **Data do Torneio:**", unsafe_allow_html=True)
        if st.session_state["user_role"] == "master":
            n_dt = st.text_input("Editar Data", value=st.session_state["data_torneio_aro"], label_visibility="collapsed")
            if n_dt != st.session_state["data_torneio_aro"]:
                st.session_state["data_torneio_aro"] = n_dt
                open("backup_data_torneio.txt", "w").write(n_dt); st.rerun()
        else: st.markdown(f"#### {st.session_state['data_torneio_aro']}", unsafe_allow_html=True)

    df_t = st.session_state["dados_torneios_internos"]
    esp_lista = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("🪵 Trinca Ferro", f"{len(df_t[df_t['Espécie'] == 'Trinca Ferro'])} aves")
    m2.metric("🌱 Coleiro", f"{len(df_t[df_t['Espécie'] == 'Coleiro'])} aves")
    m3.metric("🌶️ Bico de Pimenta", f"{len(df_t[df_t['Espécie'] == 'Bico de Pimenta'])} aves")
    m4.metric("💛 Canário", f"{len(df_t[df_t['Espécie'] == 'Canário'])} aves")
    m5.metric("🔵 Azulão", f"{len(df_t[df_t['Espécie'] == 'Azulão'])} aves")
    m6.metric("🐦 Tiziu", f"{len(df_t[df_t['Espécie'] == 'Tiziu'])} aves")
    st.markdown("---")

    if st.session_state["user_role"] == "master":
        st.subheader("➕ Realizar Nova Inscrição")
