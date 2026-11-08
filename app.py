import streamlit as st
import pandas as pd
import pickle

# CONFIGURAÇÃO DO APP E ÍCONE DO NAVEGADOR
st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="logo.png", layout="wide")

# --- INICIALIZAÇÃO DO BANCO DE LOGINS NA MEMÓRIA ---
if "banco_usuarios_dinamicos" not in st.session_state:
    st.session_state["banco_usuarios_dinamicos"] = {
        "Socio": {"senha": "aro123", "role": "socio", "socio_vinculado": "Nenhum"},
        "Visitante": {"senha": "aro999", "role": "visitante", "socio_vinculado": "Nenhum"}
    }

usuarios_cadastrados = st.session_state["banco_usuarios_dinamicos"]

# --- SISTEMA DE LOGIN SEGURO ---
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "visitante"})

if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    
    with st.form("t_login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == "Junior Rebelo" and s == "270688":
                st.session_state.update({"autenticado": True, "user_role": "master", "username": "Junior Rebelo"})
                st.rerun()
            elif u in ["Kleven", "Valter", "Peterson", "Mauro"] and s == {"Kleven": "12345678", "Valter": "021277", "Peterson": "100693", "Mauro": "120660"}[u]:
                st.session_state.update({"autenticado": True, "user_role": "diretoria", "username": u})
                st.rerun()
            elif u == "Vanderlei" and s == "251073":
                st.session_state.update({"autenticado": True, "user_role": "diretoria", "username": "Vanderlei"})
                st.rerun()
            elif u in usuarios_cadastrados and usuarios_cadastrados[u]["senha"] == s:
                st.session_state.update({"autenticado": True, "user_role": usuarios_cadastrados[u]["role"], "username": u})
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                
    st.write("<p style='text-align: center; color: gray; margin: 5px 0;'>Ou se você é apenas um visitante do evento:</p>", unsafe_allow_html=True)
    if st.button("🌐 Entrar como Convidado / Visitante", use_container_width=True):
        st.session_state.update({"autenticado": True, "user_role": "visitante", "username": "Visitante Convidado"})
        st.rerun()
    st.stop()

# --- SE ESTIVER AUTENTICADO ---
if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])

df_socios_global = st.session_state["dados_socios_internos"]

c_l, c_t, c_o = st.columns(3)
c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO - Rio do Sul</h1>", unsafe_allow_html=True)
if c_o.button("🔒 Sair do Painel", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

st.markdown("---")
role = st.session_state["user_role"]

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🦅 Bem-vindo ao Sistema Oficial ARO</h2>", unsafe_allow_html=True)

# --- CENTRAL DE CADASTRO DINÂMICO DE LOGINS (EXCLUSIVO MASTER) ---
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
                        st.error("Nome de usuário reservado!")
                    elif tipo_role == "Sócio" and socio_vinc == "Selecione o Sócio...":
                        st.error("Selecione qual sócio oficial será vinculado!")
                    else:
                        st.session_state["banco_usuarios_dinamicos"][novo_u.strip()] = {"senha": novo_s.strip(), "role": "socio" if tipo_role == "Sócio" else "visitante", "socio_vinculado": socio_vinc}
                        st.success("Usuário salvo na memória viva com sucesso!")
                        st.rerun()
                else: st.error("Preencha todos os campos!")
                    
    with col_cad_2:
        st.markdown("**Usuários Cadastrados Ativos**")
        if usuarios_cadastrados:
            lista_exibicao = [{"Usuário": k, "Senha": v["senha"], "Nível": str(v["role"]).upper(), "Vínculo": v.get("socio_vinculado", "Nenhum")} for k, v in usuarios_cadastrados.items()]
            st.dataframe(pd.DataFrame(lista_exibicao), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("🗑️ **Excluir Usuário**")
            u_para_deletar = st.selectbox("Conta para apagar:", list(usuarios_cadastrados.keys()))
            confirmar_del = st.checkbox("💥 Confirmo a exclusão permanente")
            
            if st.button("❌ Deletar Usuário Selecionado", use_container_width=True):
                if confirmar_del:
                    del st.session_state["banco_usuarios_dinamicos"][u_para_deletar]
                    st.success("Usuário excluído de forma imediata!")
                    st.rerun()
                else: st.error("Marque o quadrado de confirmação antes de deletar!")
