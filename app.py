import streamlit as st
import pandas as pd
import os, pickle

st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="logo.png" if os.path.exists("logo.png") else "📊", layout="wide")
st.markdown("""<head><title>ARO</title><link rel="apple-touch-icon" href="app/static/logo.png"><link rel="icon" type="image/png" href="app/static/logo.png"></head>""", unsafe_allow_html=True)

if "banco_usuarios_dinamicos" not in st.session_state:
    if os.path.exists("./backup_usuarios.pkl"):
        try: st.session_state["banco_usuarios_dinamicos"] = pickle.load(open("./backup_usuarios.pkl", "rb"))
        except: st.session_state["banco_usuarios_dinamicos"] = {}
    else:
        st.session_state["banco_usuarios_dinamicos"] = {
            "Socio": {"senha": "aro123", "role": "socio", "socio_vinculado": "Nenhum"},
            "Visitante": {"senha": "aro999", "role": "visitante", "socio_vinculado": "Nenhum"}
        }

usuarios_cadastrados = st.session_state["banco_usuarios_dinamicos"]

if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "visitante", "tela_atual": "menu"})

if not st.session_state["autenticado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        _, col_img, _ = st.columns(3)
        col_img.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #6B7280;'>ARO - Rio do Sul</h3>", unsafe_allow_html=True)
    
    with st.form("t_login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == "Junior Rebelo" and s == "270688":
                st.session_state.update({"autenticado": True, "user_role": "master"})
                st.rerun()
            elif u in ["Kleven", "Valter", "Peterson", "Mauro"] and s == {"Kleven": "12345678", "Valter": "021277", "Peterson": "100693", "Mauro": "120660"}[u]:
                st.session_state.update({"autenticado": True, "user_role": "diretoria"})
                st.rerun()
            elif u == "Vanderlei" and s == "251073": # Senha do Vanderlei alterada para 251073
                st.session_state.update({"autenticado": True, "user_role": "diretoria"})
                st.rerun()
            elif u in usuarios_cadastrados and usuarios_cadastrados[u]["senha"] == s:
                st.session_state.update({"autenticado": True, "user_role": usuarios_cadastrados[u]["role"]})
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# --- SE ESTIVER AUTENTICADO ---
lista_meses = ["Dezembro 2026"] + [f"{m} {a}" for a in ["2027", "2028"] for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]]

if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv("backup_socios.csv") if os.path.exists("backup_socios.csv") else pd.DataFrame([{"Número": i, "ID": "", "Nome": "", "Telefone": "", "CPF": "", "CTF": "", "Status": "Ativo"} for i in range(1, 21)])

df_socios_global = st.session_state["dados_socios_internos"]

if "saldo_anterior_master" not in st.session_state:
    if os.path.exists("backup_saldo_ant.txt"):
        with open("backup_saldo_ant.txt", "r") as f: st.session_state["saldo_anterior_master"] = float(f.read())
    else: st.session_state["saldo_anterior_master"] = 0.0

if "dados_meses_financeiros" not in st.session_state:
    st.session_state["dados_meses_financeiros"] = pickle.load(open("backup_financas.pkl", "rb")) if os.path.exists("backup_financas.pkl") else {m: pd.DataFrame([{"Dia": i, "Entradas": 0.0, "Saídas": 0.0, "Motivo": ""} for i in range(1, 32)]) for m in lista_meses}

if "dados_torneios_internos" not in st.session_state:
    st.session_state["dados_torneios_internos"] = pickle.load(open("backup_torneios_v2.pkl", "rb")) if os.path.exists("backup_torneios_v2.pkl") else pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Estaca", "Valor", "Clube"])

if "data_torneio_aro" not in st.session_state:
    try: st.session_state["data_torneio_aro"] = open("backup_data_torneio.txt", "r").read() if os.path.exists("backup_data_torneio.txt") else "08/11/2026"
    except: st.session_state["data_torneio_aro"] = "08/11/2026"

c_l, c_t, c_o = st.columns(3)
try:
    if os.path.exists("logo.png"): c_l.image("logo.png", width=80)
except: pass

c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
if c_o.button("🔒 Sair do Panel", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

st.markdown("---")
role = st.session_state["user_role"]
if role == "master": st.info("⭐ Modo Administrador: Acesso Master Ativado")
elif role == "diretoria": st.info("🛡️ Modo Diretoria: Acesso Administrativo Parcial Ativado")
elif role == "socio": st.info("👥 Modo Sócio: Acesso de Consulta a Torneios Ativado")
else: st.info("ℹ️ Modo Visitante: Acesso Limitado Ativado")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🦅 Bem-vindo ao Sistema Oficial ARO</h2>", unsafe_allow_html=True)

if role in ["master", "diretoria"]:
    st.markdown("<p style='text-align: center; color: #6B7280;'>Utilize o menu lateral à esquerda para navegar entre as planilhas de Sócios, Finanças e Torneios.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align: center; color: #6B7280;'>Utilize o menu lateral à esquerda para visualizar a página de **Torneios**.</p>", unsafe_allow_html=True)

# --- CENTRAL DE CADASTRO E EXCLUSÃO DINÂMICA DE LOGINS (EXCLUSIVO MASTER) ---
if role == "master":
    st.write("---")
    st.markdown("### 🔑 Central de Gerenciamento de Acessos")
    col_cad_1, col_cad_2 = st.columns(2)
    
    with col_cad_1:
        with st.form("form_cadastrar_usuario", clear_on_submit=True):
            st.markdown("**Cadastrar / Atualizar Usuário**")
            novo_u = st.text_input("Nome de Usuário (Login):")
            novo_s = st.text_input("Senha de Acesso:", type="password")
            tipo_role = st.selectbox("Categoria/Nível:", ["Sócio", "Visitante"])
            
            socio_vinc = "Nenhum"
            if tipo_role == "Sócio":
                lista_nomes = ["Selecione o Sócio..."]
                if not df_socios_global.empty and "Nome" in df_socios_global.columns:
                    lista_nomes.extend(df_socios_global["Nome"].dropna().str.strip().tolist())
                socio_vinc = st.selectbox("Vincular Sócio Oficial:", [x for x in lista_nomes if x != ""])
                
            if st.form_submit_button("Salvar Usuário", use_container_width=True):
                if novo_u.strip() and novo_s.strip():
                    if novo_u.strip() in ["Junior Rebelo", "Kleven", "Valter", "Peterson", "Mauro", "Vanderlei"]:
                        st.error("Nome de usuário reservado para a administração fixa!")
                    elif tipo_role == "Sócio" and socio_vinc == "Selecione o Sócio...":
                        st.error("Selecione qual sócio oficial será vinculado a este login!")
                    else:
                        st.session_state["banco_usuarios_dinamicos"][novo_u.strip()] = {"senha": novo_s.strip(), "role": "socio" if tipo_role == "Sócio" else "visitante", "socio_vinculado": socio_vinc}
                        try:
                            with open("./backup_usuarios.pkl", "wb") as f: pickle.dump(st.session_state["banco_usuarios_dinamicos"], f)
                            st.success("Usuário salvo com sucesso!")
                            st.rerun()
                        except: st.error("Erro ao gravar arquivo físico de backup.")
                else: st.error("Preencha todos os campos do formulário!")
                    
    with col_cad_2:
        st.markdown("**Usuários Cadastrados Ativos**")
        if usuarios_cadastrados:
            lista_exibicao = [{"Usuário": k, "Senha": v["senha"], "Nível": str(v["role"]).upper(), "Vínculo": v.get("socio_vinculado", "Nenhum")} for k, v in usuarios_cadastrados.items()]
            st.dataframe(pd.DataFrame(lista_exibicao), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("🗑️ **Excluir Usuário do Sistema**")
            u_para_deletar = st.selectbox("Selecione a conta para apagar:", list(usuarios_cadastrados.keys()))
            confirmar_del = st.checkbox("💥 Confirmo que desejo apagar permanentemente este acesso")
            
            if st.button("❌ Deletar Usuário Selecionado", use_container_width=True):
                if confirmar_del:
                    del st.session_state["banco_usuarios_dinamicos"][u_para_deletar]
                    try:
                        with open("./backup_usuarios.pkl", "wb") as f: pickle.dump(st.session_state["banco_usuarios_dinamicos"], f)
                        st.success("Usuário excluído!")
                        st.rerun()
                    except: st.error("Erro ao atualizar o backup.")
                else: st.error("Marque o quadrado de confirmação antes de deletar!")
        else:
            st.caption("Nenhum usuário dinâmico ativo no momento.")
