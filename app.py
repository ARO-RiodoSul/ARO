import streamlit as st
import pandas as pd
import pickle
import os

st.set_page_config(page_title="Painel - ARO Rio do Sul", page_icon="logo.png" if os.path.exists("logo.png") else "📊", layout="wide")

PATH_USUARIOS = os.path.abspath("backup_usuarios.pkl")
PATH_SOCIOS = os.path.abspath("backup_socios.csv")

# Sincronização forçada entre múltiplos dispositivos
if "banco_usuarios_dinamicos" not in st.session_state or st.sidebar.button("🔄 Sincronizar Sistema"):
    if os.path.exists(PATH_USUARIOS):
        try:
            with open(PATH_USUARIOS, "rb") as f:
                st.session_state["banco_usuarios_dinamicos"] = pickle.load(f)
        except:
            st.session_state["banco_usuarios_dinamicos"] = {}
    else:
        st.session_state["banco_usuarios_dinamicos"] = {
            "socio": {"senha": "aro123", "role": "socio", "socio_vinculado": "Nenhum"},
            "visitante": {"senha": "aro999", "role": "visitante", "socio_vinculado": "Nenhum"}
        }

usuarios_cadastrados = st.session_state["banco_usuarios_dinamicos"]

if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "user_role": "visitante", "username": ""})

if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>ARO - Rio do Sul</h1>", unsafe_allow_html=True)
    
    with st.form("t_login"):
        u_input = st.text_input("Usuário").strip()
        s_input = st.text_input("Senha", type="password").strip()
        
        if st.form_submit_button("Entrar"):
            u_f = u_input.lower()
            
            if u_input == "Junior Rebelo" and s_input == "270688":
                st.session_state.update({"autenticado": True, "user_role": "master", "username": "Junior Rebelo"})
                st.rerun()
            elif u_f in ["kleven", "valter", "peterson", "mauro"] and s_input == {"kleven": "12345678", "valter": "021277", "peterson": "100693", "mauro": "120660"}[u_f]:
                st.session_state.update({"autenticado": True, "user_role": "diretoria", "username": u_f.capitalize()})
                st.rerun()
            elif u_f == "vanderlei" and s_input == "251073":
                st.session_state.update({"autenticado": True, "user_role": "diretoria", "username": "Vanderlei"})
                st.rerun()
            elif u_f in [k.lower() for k in usuarios_cadastrados.keys()]:
                chave_original = [k for k in usuarios_cadastrados.keys() if k.lower() == u_f][0]
                if str(usuarios_cadastrados[chave_original]["senha"]).strip() == s_input:
                    st.session_state.update({
                        "autenticado": True, 
                        "user_role": usuarios_cadastrados[chave_original]["role"], 
                        "username": chave_original
                    })
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")
            else: st.error("Usuário ou senha incorretos.")
                
    if st.button("🌐 Entrar como Convidado / Visitante", use_container_width=True):
        st.session_state.update({"autenticado": True, "user_role": "visitante", "username": "Visitante Convidado"})
        st.rerun()
    st.stop()

if "dados_socios_internos" not in st.session_state:
    st.session_state["dados_socios_internos"] = pd.read_csv(PATH_SOCIOS) if os.path.exists(PATH_SOCIOS) else pd.DataFrame(columns=["Número", "ID", "Nome", "Telefone", "CPF", "CTF", "Status"])

df_socios_global = st.session_state["dados_socios_internos"]
c_l, c_t, c_o = st.columns(3)
c_t.markdown("<h1 style='margin: 0; color: #1E3A8A;'>Painel ARO</h1>", unsafe_allow_html=True)
if c_o.button("🔒 Sair do Painel", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

role = st.session_state["user_role"]
st.markdown(f"### 🦅 Bem-vindo, {st.session_state['username']}!")

if role == "master":
    st.write("---")
    st.markdown("### 🔑 Central de Gerenciamento de Acessos Compartilhados")
    col_cad_1, col_cad_2 = st.columns(2)
    
    with col_cad_1:
        with st.form("form_cadastrar_usuario", clear_on_submit=True):
            st.markdown("**Cadastrar Novo Usuário**")
            novo_u = st.text_input("Nome de Usuário (Login):")
            novo_s = st.text_input("Senha de Acesso:")
            tipo_role = st.selectbox("Categoria/Nível:", ["Sócio", "Visitante"])
            
            socio_vinc = "Nenhum"
            if tipo_role == "Sócio":
                lista_nomes = ["Selecione o Sócio..."]
                if not df_socios_global.empty and "Nome" in df_socios_global.columns:
                    lista_nomes.extend(df_socios_global["Nome"].dropna().str.strip().tolist())
                socio_vinc = st.selectbox("Vincular Sócio Oficial:", [x for x in lista_nomes if x != ""])
                
            if st.form_submit_button("Salvar Usuário Compartilhado", use_container_width=True):
                if novo_u.strip() and novo_s.strip():
                    st.session_state["banco_usuarios_dinamicos"][novo_u.strip()] = {"senha": novo_s.strip(), "role": "socio" if tipo_role == "Sócio" else "visitante", "socio_vinculado": socio_vinc}
                    with open(PATH_USUARIOS, "wb") as f:
                        pickle.dump(st.session_state["banco_usuarios_dinamicos"], f)
                    st.success("Salvo com sucesso! Use o botão abaixo para baixar o backup caso mude de aparelho.")
                    st.rerun()
                    
    with col_cad_2:
        st.markdown("**Usuários Ativos**")
        if usuarios_cadastrados:
            lista_exibicao = [{"Usuário": k, "Senha": v["senha"], "Nível": str(v["role"]).upper(), "Vínculo": v.get("socio_vinculado", "Nenhum")} for k, v in usuarios_cadastrados.items()]
            st.dataframe(pd.DataFrame(lista_exibicao), use_container_width=True, hide_index=True)
            
            u_del = st.selectbox("Conta para apagar:", list(usuarios_cadastrados.keys()))
            if st.button("❌ Deletar Usuário Selecionado", use_container_width=True):
                del st.session_state["banco_usuarios_dinamicos"][u_del]
                with open(PATH_USUARIOS, "wb") as f: pickle.dump(st.session_state["banco_usuarios_dinamicos"], f)
                st.success("Excluído!"); st.rerun()

