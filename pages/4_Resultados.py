import streamlit as st
import pandas as pd
import datetime, io, pickle, os, base64, json
import urllib.request, urllib.error
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Resultados - ARO", page_icon="🏆", layout="wide")

if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Faça Login antes de acessar")
    st.stop()

st.title("🏆 Resultados e Classificação Geral - ARO")

role_atual = str(st.session_state.get("user_role", "")).strip().lower()
is_admin = role_atual in ["master", "diretoria", "admin"]
is_master = role_atual == "master"
especies_validas = ["Trinca Ferro", "Coleiro", "Bico de Pimenta", "Canário", "Azulão", "Tiziu"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
ARQUIVO_RESULTADOS = "backup_resultados_oficial.pkl"

# =========================================================================================
# ☁️ SISTEMA DE BACKUP DUPLO (LOCAL + ENVIO AUTOMÁTICO PARA O GITHUB)
# =========================================================================================
def enviar_backup_github(conteudo_bytes):
    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
        repo = st.secrets.get("GITHUB_REPO", "")
        if not token or not repo:
            return False, "Token não configurado nos Secrets"

        url = f"https://github.com{repo}/contents/{ARQUIVO_RESULTADOS}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ARO-App-Backup"
        }

        sha_atual = None
        try:
            req_get = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req_get, timeout=10) as resp:
                dados_arq = json.loads(resp.read().decode("utf-8"))
                sha_atual = dados_arq.get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                return False, f"Erro HTTP {e.code}"

        payload = {
            "message": f"Backup automático resultados ARO - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "content": base64.b64encode(conteudo_bytes).decode("utf-8")
        }
        if sha_atual:
            payload["sha"] = sha_atual

        req_put = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT"
        )
        with urllib.request.urlopen(req_put, timeout=15) as resp_put:
             return resp_put.status in (200, 201), "Salvo na nuvem GitHub"

    except Exception as ex:
        return False, str(ex)

def estrutura_vazia_temporada():
    return {
        "historico_etapas": pd.DataFrame(columns=["Data", "Espécie", "Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]),
        "campeonato_geral": pd.DataFrame(columns=["Proprietário", "Nome da Ave", "Espécie", "Anilha", "Pontuação Acumulada"])
    }

def carregar_resultados_fisicos():
    ano_padrao = str(datetime.date.today().year)
    if os.path.exists(ARQUIVO_RESULTADOS):
        with open(ARQUIVO_RESULTADOS, "rb") as f:
            dados = pickle.load(f)
        # Migração automática caso o arquivo ainda esteja no formato antigo (sem divisão por ano)
        if "temporadas" not in dados:
            dados_migrados = {
                "temporada_atual": ano_padrao,
                "temporadas": {
                    ano_padrao: {
                        "historico_etapas": dados.get("historico_etapas", estrutura_vazia_temporada()["historico_etapas"]),
                        "campeonato_geral": dados.get("campeonato_geral", estrutura_vazia_temporada()["campeonato_geral"])
                    }
                }
            }
            salvar_resultados_fisicos(dados_migrados)
            return dados_migrados
        return dados
    else:
        return {
            "temporada_atual": ano_padrao,
            "temporadas": {
                ano_padrao: estrutura_vazia_temporada()
            }
        }

def salvar_resultados_fisicos(dados):
    bytes_pkl = pickle.dumps(dados)
    with open(ARQUIVO_RESULTADOS, "wb") as f:
        f.write(bytes_pkl)
    sucesso_gh, msg_gh = enviar_backup_github(bytes_pkl)
    st.session_state["ultimo_status_backup"] = (sucesso_gh, msg_gh)
# =========================================================================================
# 🎨 FUNÇÃO GERADORA DE IMAGEM PROFISSIONAL (PÓDIO + LOGO ARO + FONTES GRANDES)
# =========================================================================================
def gerar_imagem_oficial_aro(titulo_banner, subtitulo_info, especie, df_dados, modo="etapa"):
    import reportlab
    LARGURA = 1200
    qtd_itens = len(df_dados)
    ALTURA = max(1450, 560 + (qtd_itens * 144) + 120)

    if modo == "geral":
        COR_TOPO = (15, 23, 42)
        COR_BASE = (30, 41, 59)
        COR_DESTAQUE = (234, 179, 8)
        COR_TEXTO_FAIXA = (15, 23, 42)
    else:
        COR_TOPO = (12, 26, 62)
        COR_BASE = (23, 48, 108)
        COR_DESTAQUE = (56, 189, 248)
        COR_TEXTO_FAIXA = (12, 26, 62)

    COR_BRANCO = (255, 255, 255)
    COR_SUAVE = (226, 232, 240)
    COR_CARD_NORMAL = (28, 56, 115) if modo == "etapa" else (38, 52, 78)

    ESTILO_PODIO = {
        1: {"card": (218, 178, 50), "texto": (20, 15, 5), "sub": (45, 35, 10), "badge": (255, 255, 255), "num": (175, 125, 10)},
        2: {"card": (208, 218, 230), "texto": (15, 23, 42), "sub": (40, 50, 68), "badge": (255, 255, 255), "num": (65, 80, 100)},
        3: {"card": (208, 130, 55), "texto": (25, 12, 5), "sub": (55, 30, 10), "badge": (255, 255, 255), "num": (150, 80, 20)},
    }

    img = Image.new("RGB", (LARGURA, ALTURA), COR_TOPO)
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = COR_TOPO
    r2, g2, b2 = COR_BASE
    for y in range(ALTURA):
        fator = y / ALTURA
        r = int(r1 + (r2 - r1) * fator)
        g = int(g1 + (g2 - g1) * fator)
        b = int(b1 + (b2 - b1) * fator)
        draw.line([(0, y), (LARGURA, y)], fill=(r, g, b))

    draw.rectangle([24, 24, LARGURA - 24, ALTURA - 24], outline=COR_DESTAQUE, width=5)
    draw.rectangle([36, 36, LARGURA - 36, ALTURA - 36], outline=(255, 255, 255), width=1)

    def carregar_fonte_segura(tamanho, negrito=True):
        rl_dir = os.path.dirname(reportlab.__file__)
        candidatos = [
            os.path.join(rl_dir, "fonts", "VeraBd.ttf" if negrito else "Vera.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "arialbd.ttf" if negrito else "arial.ttf",
        ]
        if os.path.exists("/usr/share/fonts"):
            for raiz, _, arquivos in os.walk("/usr/share/fonts"):
                for arq in arquivos:
                    if arq.lower().endswith(".ttf"):
                        if negrito and ("bold" in arq.lower() or "bd" in arq.lower()):
                            candidatos.append(os.path.join(raiz, arq))
                        elif not negrito:
                            candidatos.append(os.path.join(raiz, arq))

        for caminho in candidatos:
            if os.path.exists(caminho):
                try:
                    return ImageFont.truetype(caminho, tamanho)
                except Exception:
                    continue
        return ImageFont.load_default(size=tamanho)

    f_clube = carregar_fonte_segura(26, negrito=True)
    f_titulo = carregar_fonte_segura(54, negrito=True)
    f_subtitulo = carregar_fonte_segura(30, negrito=True)
    f_especie = carregar_fonte_segura(36, negrito=True)
    f_pos = carregar_fonte_segura(38, negrito=True)
    f_ave = carregar_fonte_segura(35, negrito=True)
    f_detalhe = carregar_fonte_segura(26, negrito=True)
    f_pontos = carregar_fonte_segura(40, negrito=True)
    f_rodape = carregar_fonte_segura(22, negrito=True)

    y_cursor = 60

    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            altura_logo = 160
            proporcao = altura_logo / logo.height
            largura_logo = int(logo.width * proporcao)
            logo = logo.resize((largura_logo, altura_logo), Image.Resampling.LANCZOS)
            img.paste(logo, ((LARGURA - largura_logo) // 2, y_cursor), logo)
            y_cursor += altura_logo + 28
        except Exception:
            y_cursor += 20
    else:
        y_cursor += 20

    draw.text((LARGURA // 2, y_cursor), "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA", font=f_clube, fill=COR_DESTAQUE, anchor="mm")
    y_cursor += 50
    draw.text((LARGURA // 2, y_cursor), titulo_banner.upper(), font=f_titulo, fill=COR_BRANCO, anchor="mm")
    y_cursor += 50
    draw.text((LARGURA // 2, y_cursor), subtitulo_info, font=f_subtitulo, fill=COR_SUAVE, anchor="mm")
    y_cursor += 64

    draw.rounded_rectangle([110, y_cursor - 32, LARGURA - 110, y_cursor + 34], radius=18, fill=COR_DESTAQUE)
    draw.text((LARGURA // 2, y_cursor), f"MODALIDADE: {especie.upper()}", font=f_especie, fill=COR_TEXTO_FAIXA, anchor="mm")
    y_cursor += 82

    margem_x = 60
    largura_card = LARGURA - (margem_x * 2)
    altura_card = 124

    for idx, row in df_dados.iterrows():
        pos_num = idx + 1
        if "Ordem_Col" in row:
            pos_num = int(row["Ordem_Col"])

        if pos_num in ESTILO_PODIO:
            st_p = ESTILO_PODIO[pos_num]
            c_card, c_txt, c_sub, c_badge, c_num = st_p["card"], st_p["texto"], st_p["sub"], st_p["badge"], st_p["num"]
        else:
            c_card, c_txt, c_sub, c_badge, c_num = COR_CARD_NORMAL, COR_BRANCO, COR_SUAVE, COR_DESTAQUE, COR_TEXTO_FAIXA

        draw.rounded_rectangle([margem_x, y_cursor, margem_x + largura_card, y_cursor + altura_card], radius=18, fill=c_card)

        cy = y_cursor + (altura_card // 2)
        draw.ellipse([margem_x + 20, cy - 36, margem_x + 92, cy + 36], fill=c_badge)
        draw.text((margem_x + 56, cy), f"{pos_num}º", font=f_pos, fill=c_num, anchor="mm")

        nome_ave = str(row["Nome da Ave"]).upper()
        proprietario = str(row["Proprietário"]).upper()
        anilha = str(row["Anilha"]).upper()

        linha_1 = f"{nome_ave[:20]} • {proprietario[:22]}"
        if modo == "etapa":
            cantos_val = int(row["Cantos"])
            linha_2 = f"ANILHA: {anilha}   |   CANTOS: {cantos_val}"
            pts_val = int(row["Pontos"])
        else:
            linha_2 = f"ANILHA: {anilha}"
            pts_val = int(row["Pontuação Acumulada"])

        draw.text((margem_x + 115, y_cursor + 38), linha_1, font=f_ave, fill=c_txt, anchor="lm")
        draw.text((margem_x + 115, y_cursor + 88), linha_2, font=f_detalhe, fill=c_sub, anchor="lm")
        draw.text((margem_x + largura_card - 28, cy), f"{pts_val} PTS", font=f_pontos, fill=c_txt, anchor="rm")

        y_cursor += altura_card + 18

    draw.text(
        (LARGURA // 2, ALTURA - 52),
        f"RESULTADO OFICIAL ARO • EMITIDO EM {datetime.date.today().strftime('%d/%m/%Y')}",
        font=f_rodape,
        fill=COR_SUAVE,
        anchor="mm"
    )

    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG", quality=95)
    img_buffer.seek(0)
    return img_buffer
if "banco_resultados_viva" not in st.session_state or "temporadas" not in st.session_state["banco_resultados_viva"]:
    st.session_state["banco_resultados_viva"] = carregar_resultados_fisicos()

banco_geral = st.session_state["banco_resultados_viva"]

temporada_ativa = str(banco_geral.get("temporada_atual", str(datetime.date.today().year)))
todas_temporadas = sorted(list(banco_geral["temporadas"].keys()), reverse=True)

if "lista_lote_resultados" not in st.session_state:
    st.session_state["lista_lote_resultados"] = []

# =========================================================================================
# 📅 SELETOR DE TEMPORADA (ANO) E MENU PRINCIPAL
# =========================================================================================
col_temp, col_vis = st.columns((1, 2))

with col_temp:
    ano_selecionado = st.selectbox(
        "📅 Temporada / Ano:",
        todas_temporadas,
        index=todas_temporadas.index(temporada_ativa) if temporada_ativa in todas_temporadas else 0,
        format_func=lambda a: f"🏆 {a} (Temporada Atual)" if a == temporada_ativa else f"📁 {a} (Encerrada)"
    )

eh_temporada_ativa = (ano_selecionado == temporada_ativa)
df_etapas = banco_geral["temporadas"][ano_selecionado]["historico_etapas"]

with col_vis:
    opcao_tela = st.radio(
        "Selecione a visualização desejada:",
        ["📅 Resultados por Etapa", "📊 Classificação Geral do Campeonato"],
        horizontal=True
    )

if not eh_temporada_ativa:
    st.info(f"📁 **Modo Histórico ({ano_selecionado}):** Esta temporada já foi encerrada. Os resultados e rankings estão disponíveis para consulta, PDF e imagem.")

# =========================================================================================
# ⚙️ PAINÉIS ADMINISTRATIVOS (LANÇAMENTO, EXCLUSÃO, BACKUP E ENCERRAR TEMPORADA)
# =========================================================================================
if is_admin:
    st.write("---")
    
    # 1. LANÇAMENTO EM LOTE (APENAS NA TEMPORADA ATIVA)
    if eh_temporada_ativa:
        exp_cadastro = st.expander(f"📝 Painel de Lançamento de Resultados em Lote - Temporada {temporada_ativa}")
        with exp_cadastro:
            st.markdown("##### 1. Configurações Iniciais da Etapa")
            c_conf1, c_conf2, c_conf3 = st.columns(3)
            l_data = c_conf1.date_input("Data da Etapa:", datetime.date.today(), key="l_data_input")
            l_especie = c_conf2.selectbox("Espécie da Rodada:", especies_validas, key="l_especie_select")
            pt_maxima = c_conf3.number_input("Pontuação do 1º Colocado:", min_value=1, value=10, step=1)
            
            st.write("---")
            st.markdown("##### 2. Adicionar Aves Classificadas (Sem limite de posições)")
            
            with st.form("form_lote_individual_ajustado", clear_on_submit=True):
                col_r1, col_r2, col_r3 = st.columns(3)
                num_colocacao = col_r1.number_input("Colocação (Nº):", min_value=1, step=1, value=1)
                r_proprietario = col_r2.text_input("Proprietário:")
                r_ave = col_r3.text_input("Nome da Ave:")
                
                col_r4, col_r5 = st.columns(2)
                r_anilha = col_r4.text_input("Anilha:")
                r_cantos = col_r5.number_input("Quantidade de Cantos:", min_value=0, step=1, value=0)
                
                r_pontos = max(0, pt_maxima - (num_colocacao - 1))
                st.caption(f"💡 Esta colocação ({num_colocacao}º Lugar) receberá automaticamente: **{r_pontos} pontos**")
                
                if st.form_submit_button("➕ Adicionar à Lista Temporária", use_container_width=True):
                    if not r_proprietario.strip() or not r_ave.strip() or not r_anilha.strip():
                        st.error("❌ Preencha todos os campos da ave antes de adicionar.")
                    else:
                        nova_ave_temp = {
                            "Data": l_data.strftime("%d/%m/%Y"),
                            "Espécie": l_especie,
                            "Colocação": f"{num_colocacao}º Lugar",
                            "Proprietário": r_proprietario.strip().upper(),
                            "Nome da Ave": r_ave.strip().upper(),
                            "Anilha": r_anilha.strip().upper(),
                            "Cantos": int(r_cantos),
                            "Pontos": int(r_pontos)
                        }
                        st.session_state["lista_lote_resultados"].append(nova_ave_temp)
                        st.success(f"Ave '{r_ave.upper()}' adicionada temporariamente em {num_colocacao}º Lugar!")
                        st.rerun()

            if st.session_state["lista_lote_resultados"]:
                st.write("")
                st.markdown(f"**📋 Aves Preparadas para Salvar ({l_especie} - {l_data.strftime('%d/%m/%Y')})**")
                df_lote_temp = pd.DataFrame(st.session_state["lista_lote_resultados"])
                st.dataframe(df_lote_temp[["Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]], hide_index=True, use_container_width=True)
                
                cb_lote1, cb_lote2 = st.columns(2)
                if cb_lote1.button("🗑️ Limpar Lista Temporária", use_container_width=True):
                    st.session_state["lista_lote_resultados"] = []
                    st.rerun()
                    
                if cb_lote2.button("💾 CONFIRMAR E SALVAR ETAPA COMPLETA", use_container_width=True, type="primary"):
                    st.session_state["banco_resultados_viva"]["temporadas"][temporada_ativa]["historico_etapas"] = pd.concat([df_etapas, df_lote_temp], ignore_index=True)
                    salvar_resultados_fisicos(st.session_state["banco_resultados_viva"])
                    st.session_state["lista_lote_resultados"] = []
                    st.success("🎯 Resultados salvos localmente e enviados para o backup!")
                    st.rerun()
        # 2. EXCLUSÃO DE RESULTADOS (TEMPORADA ATIVA)
        exp_excluir = st.expander(f"🗑️ Excluir Resultados Lançados - Temporada {temporada_ativa}")
        with exp_excluir:
            if df_etapas.empty:
                st.caption("Nenhum resultado salvo nesta temporada para excluir.")
            else:
                st.markdown("##### 1. Excluir uma Ave Específica")
                datas_disp_exc = sorted(df_etapas["Data"].unique(), key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"), reverse=True)
                data_exc_sel = st.selectbox("Selecione a Data da Etapa:", datas_disp_exc, key="sel_data_exc")
                df_na_data = df_etapas[df_etapas["Data"] == data_exc_sel]
                
                opcoes_aves_exc = [
                    f"[{row['Espécie']}] {row['Colocação']} - {row['Nome da Ave']} (Prop: {row['Proprietário']} | Anilha: {row['Anilha']})"
                    for _, row in df_na_data.iterrows()
                ]
                indices_reais_exc = df_na_data.index.tolist()
                item_exc_escolhido = st.selectbox("Selecione o resultado que deseja apagar:", opcoes_aves_exc, key="sel_ave_exc")
                
                if st.button("🗑️ Excluir Resultado Individual Selecionado", use_container_width=True):
                    idx_para_apagar = indices_reais_exc[opcoes_aves_exc.index(item_exc_escolhido)]
                    st.session_state["banco_resultados_viva"]["temporadas"][temporada_ativa]["historico_etapas"] = df_etapas.drop(idx_para_apagar).reset_index(drop=True)
                    salvar_resultados_fisicos(st.session_state["banco_resultados_viva"])
                    st.warning("✅ Resultado individual removido! Classificação atualizada.")
                    st.rerun()

                st.write("---")
                st.markdown("##### 2. Excluir Rodada / Espécie Inteira da Data")
                especies_na_data = sorted(df_na_data["Espécie"].unique().tolist())
                esp_exc_lote = st.selectbox("Selecione a Espécie que deseja apagar desta data:", ["TODAS AS ESPÉCIES DESTA DATA"] + especies_na_data, key="sel_esp_exc_lote")
                
                if st.checkbox(f"Confirmar exclusão definitiva dos registros de {data_exc_sel}", key="chk_confirma_exc_lote"):
                    if st.button("💥 APAGAR RESULTADOS EM LOTE", use_container_width=True, type="primary"):
                        if esp_exc_lote == "TODAS AS ESPÉCIES DESTA DATA":
                            novo_df = df_etapas[df_etapas["Data"] != data_exc_sel].reset_index(drop=True)
                        else:
                            novo_df = df_etapas[~((df_etapas["Data"] == data_exc_sel) & (df_etapas["Espécie"] == esp_exc_lote))].reset_index(drop=True)
                        st.session_state["banco_resultados_viva"]["temporadas"][temporada_ativa]["historico_etapas"] = novo_df
                        salvar_resultados_fisicos(st.session_state["banco_resultados_viva"])
                        st.success("🗑️ Registros excluídos com sucesso!")
                        st.rerun()

    # 3. COFRE DE SEGURANÇA (BACKUP MANUAL + ENCERRAR TEMPORADA - EXCLUSIVO MASTER)
    if is_master:
        exp_cofre = st.expander("🛡️ Cofre de Backup e Gestão de Temporada Anual (Exclusivo Master)")
        with exp_cofre:
            if "ultimo_status_backup" in st.session_state:
                ok_gh, msg_gh = st.session_state["ultimo_status_backup"]
                if ok_gh:
                    st.success(f"☁️ Backup Nuvem GitHub: Ativo ({msg_gh})")
                else:
                    st.warning(f"⚠️ Backup Nuvem GitHub: {msg_gh} (Usando cópia local + download manual)")

            cb_bkp1, cb_bkp2 = st.columns(2)
            with cb_bkp1:
                st.markdown("##### 📥 Baixar Cópia de Segurança")
                bytes_atuais = pickle.dumps(st.session_state["banco_resultados_viva"])
                st.download_button(
                    label="💾 Baixar Arquivo de Backup Completo (.pkl)",
                    data=bytes_atuais,
                    file_name=f"backup_resultados_aro_{datetime.date.today().strftime('%d_%m_%Y')}.pkl",
                    mime="application/octet-stream",
                    use_container_width=True
                )
            with cb_bkp2:
                st.markdown("##### 📤 Restaurar Backup Salvo")
                arq_subido = st.file_uploader("Enviar arquivo .pkl salvo anteriormente:", type=["pkl"], key="up_bkp_res")
                if arq_subido is not None:
                    if st.button("🔄 Restaurar Dados deste Arquivo", use_container_width=True, type="primary"):
                        try:
                            dados_restaurados = pickle.loads(arq_subido.read())
                            st.session_state["banco_resultados_viva"] = dados_restaurados
                            salvar_resultados_fisicos(dados_restaurados)
                            st.success("✅ Backup restaurado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Arquivo inválido: {e}")

            st.write("---")
            st.markdown(f"##### 🏁 Encerrar Temporada {temporada_ativa} e Iniciar Novo Ano")
            st.caption("Ao encerrar, todos os dados da temporada atual ficam salvos no histórico para consulta por ano, e uma nova temporada zerada é aberta.")
            proximo_ano_sugerido = str(int(temporada_ativa) + 1) if temporada_ativa.isdigit() else str(datetime.date.today().year + 1)
            novo_ano_input = st.text_input("Nome / Ano da Nova Temporada:", value=proximo_ano_sugerido, key="input_novo_ano")
            
            if st.checkbox(f"Confirmo que desejo encerrar a temporada {temporada_ativa} e abrir {novo_ano_input}", key="chk_encerrar_temp"):
                if st.button("🚀 ENCERRAR TEMPORADA ATUAL E ABRIR NOVA", use_container_width=True, type="primary"):
                    novo_ano_limpo = novo_ano_input.strip()
                    if not novo_ano_limpo:
                        st.error("Digite o ano da nova temporada.")
                    else:
                        if novo_ano_limpo not in st.session_state["banco_resultados_viva"]["temporadas"]:
                            st.session_state["banco_resultados_viva"]["temporadas"][novo_ano_limpo] = estrutura_vazia_temporada()
                        st.session_state["banco_resultados_viva"]["temporada_atual"] = novo_ano_limpo
                        salvar_resultados_fisicos(st.session_state["banco_resultados_viva"])
                        st.success(f"🎉 Temporada {temporada_ativa} arquivada no histórico e Temporada {novo_ano_limpo} iniciada!")
                        st.rerun()
# =========================================================================================
# 📊 EXIBIÇÃO DOS DADOS: VISÍVEL PARA MASTER, DIRETORIA, SÓCIOS E VISITANTES
# =========================================================================================
st.write("")

# --- TELA 1: RESULTADOS POR ETAPA (FILTRADO POR DATA E COM EMISSÃO DE PDF E IMAGEM) ---
if opcao_tela == "📅 Resultados por Etapa":
    st.markdown(f"### 📅 Histórico de Etapas Realizadas ({ano_selecionado})")
    
    if df_etapas.empty:
        st.info(f"💡 Nenhuma etapa ou resultado foi lançado na temporada {ano_selecionado} ainda.")
    else:
        lista_datas = sorted(df_etapas["Data"].unique(), key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"), reverse=True)
        data_sel = st.selectbox("Selecione a data da etapa que deseja consultar:", lista_datas)
        
        df_filtrado_data = df_etapas[df_etapas["Data"] == data_sel].copy()
        
        abas_resultados = st.tabs(especies_validas)
        for i, esp_nome in enumerate(especies_validas):
            with abas_resultados[i]:
                df_res_esp = df_filtrado_data[df_filtrado_data["Espécie"] == esp_nome].copy()
                
                if df_res_esp.empty:
                    st.caption(f"Nenhum resultado registrado para {esp_nome} nesta etapa.")
                else:
                    df_res_esp["Ordem_Col"] = df_res_esp["Colocação"].str.extract(r'(\d+)').astype(int)
                    df_res_esp = df_res_esp.sort_values(by="Ordem_Col").reset_index(drop=True)
                    
                    st.dataframe(
                        df_res_esp[["Colocação", "Proprietário", "Nome da Ave", "Anilha", "Cantos", "Pontos"]],
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.write("")
                    col_btn_pdf, col_btn_img = st.columns(2)
                    
                    with col_btn_pdf:
                        if st.button(f"📄 Salvar Relatório Oficial em PDF", key=f"pdf_{ano_selecionado}_{esp_nome}_{data_sel}", use_container_width=True):
                            pdf_buffer = io.BytesIO()
                            p = canvas.Canvas(pdf_buffer, pagesize=A4)
                            largura_f, altura_f = A4
                            margem_x = 1.5 * cm
                            y_pos = altura_f - 1.5 * cm
                            
                            p.setFillColor(colors.HexColor("#1E3A8A"))
                            p.rect(margem_x, y_pos - 1.8*cm, largura_f - 2*margem_x, 1.8*cm, fill=True, stroke=False)
                            
                            if os.path.exists(LOGO_PATH):
                                try:
                                    p.drawImage(LOGO_PATH, margem_x + 0.3*cm, y_pos - 1.6*cm, width=1.4*cm, height=1.4*cm, mask='auto')
                                    texto_offset_x = 2.0 * cm
                                except:
                                    texto_offset_x = 0.4 * cm
                            else:
                                texto_offset_x = 0.4 * cm
                                
                            p.setFillColor(colors.white)
                            p.setFont("Helvetica-Bold", 13)
                            p.drawString(margem_x + texto_offset_x, y_pos - 0.7*cm, "ARO - ASSOCIAÇÃO RIO DO SUL DE ORNITOLOGIA")
                            p.setFont("Helvetica", 9)
                            p.drawString(margem_x + texto_offset_x, y_pos - 1.3*cm, f"TEMPORADA {ano_selecionado}  |  ETAPA: {data_sel}  |  CATEGORIA: {esp_nome.upper()}")
                            
                            y_pos -= 2.6 * cm
                            
                            p.setFillColor(colors.HexColor("#374151"))
                            p.rect(margem_x, y_pos - 0.6*cm, largura_f - 2*margem_x, 0.6*cm, fill=True, stroke=False)
                            
                            p.setFillColor(colors.white)
                            p.setFont("Helvetica-Bold", 9)
                            p.drawString(margem_x + 0.2*cm, y_pos - 0.4*cm, "COLOCAÇÃO")
                            p.drawString(margem_x + 2.8*cm, y_pos - 0.4*cm, "PROPRIETÁRIO")
                            p.drawString(margem_x + 8.2*cm, y_pos - 0.4*cm, "NOME DA AVE")
                            p.drawString(margem_x + 12.2*cm, y_pos - 0.4*cm, "ANILHA")
                            p.drawString(margem_x + 15.2*cm, y_pos - 0.4*cm, "CANTOS")
                            p.drawString(margem_x + 16.9*cm, y_pos - 0.4*cm, "PONTOS")
                            
                            y_pos -= 0.6 * cm
                            cor_alternada = False
                            p.setFont("Helvetica", 9)
                            
                            for _, row in df_res_esp.iterrows():
                                if y_pos < 2.0 * cm:
                                    p.showPage()
                                    y_pos = altura_f - 2.0 * cm
                                if cor_alternada:
                                    p.setFillColor(colors.HexColor("#F9FAFB"))
                                    p.rect(margem_x, y_pos - 0.55*cm, largura_f - 2*margem_x, 0.55*cm, fill=True, stroke=False)
                                p.setFillColor(colors.HexColor("#1F2937"))
                                p.drawString(margem_x + 0.2*cm, y_pos - 0.4*cm, str(row["Colocação"]))
                                p.drawString(margem_x + 2.8*cm, y_pos - 0.4*cm, str(row["Proprietário"])[:28])
                                p.drawString(margem_x + 8.2*cm, y_pos - 0.4*cm, str(row["Nome da Ave"])[:18])
                                p.drawString(margem_x + 12.2*cm, y_pos - 0.4*cm, str(row["Anilha"])[:14])
                                p.drawString(margem_x + 15.2*cm, y_pos - 0.4*cm, str(int(row["Cantos"])))
                                p.setFont("Helvetica-Bold", 9)
                                pontos_valor = int(row['Pontos'])
                                if pontos_valor > 0:
                                    p.setFillColor(colors.HexColor("#1E3A8A"))
                                    p.drawString(margem_x + 16.9*cm, y_pos - 0.4*cm, f"{pontos_valor} pts")
                                else:
                                    p.setFillColor(colors.HexColor("#9CA3AF"))
                                    p.drawString(margem_x + 16.9*cm, y_pos - 0.4*cm, "0 pts")
                                p.setFont("Helvetica", 9)
                                p.setLineWidth(0.3)
                                p.setStrokeColor(colors.HexColor("#E5E7EB"))
                                p.line(margem_x, y_pos - 0.55*cm, largura_f - margem_x, y_pos - 0.55*cm)
                                y_pos -= 0.55 * cm
                                cor_alternada = not cor_alternada
                            
                            p.setFont("Helvetica-Oblique", 8)
                            p.setFillColor(colors.HexColor("#6B7280"))
                            p.drawString(margem_x, 1.0*cm, f"Documento oficial emitido pelo sistema ARO em {datetime.date.today().strftime('%d/%m/%Y')} - Temporada {ano_selecionado}")
                            p.save()
                            pdf_buffer.seek(0)
                            
                            st.download_button(
                                label=f"📥 Baixar Relatório PDF - {esp_nome}",
                                data=pdf_buffer,
                                file_name=f"resultado_{ano_selecionado}_{esp_nome.lower().replace(' ', '_')}_{data_sel.replace('/', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"dl_btn_pdf_{ano_selecionado}_{esp_nome}_{data_sel}"
                            )
                    with col_btn_img:
                        if st.button(f"🖼️ Gerar Imagem Oficial (WhatsApp/Insta)", key=f"img_etapa_{ano_selecionado}_{esp_nome}_{data_sel}", use_container_width=True):
                            img_etapa_buf = gerar_imagem_oficial_aro(
                                titulo_banner="RESULTADO OFICIAL DA ETAPA",
                                subtitulo_info=f"Temporada {ano_selecionado} • Data: {data_sel}",
                                especie=esp_nome,
                                df_dados=df_res_esp,
                                modo="etapa"
                            )
                            st.image(img_etapa_buf, caption=f"Arte Oficial - {esp_nome} ({data_sel})", use_container_width=True)
                            st.download_button(
                                label=f"📥 Baixar Imagem PNG - {esp_nome}",
                                data=img_etapa_buf,
                                file_name=f"arte_resultado_{ano_selecionado}_{esp_nome.lower().replace(' ', '_')}_{data_sel.replace('/', '_')}.png",
                                mime="image/png",
                                use_container_width=True,
                                key=f"dl_btn_img_{ano_selecionado}_{esp_nome}_{data_sel}"
                            )

# --- TELA 2: CLASSIFICAÇÃO GERAL ACUMULADA DO CAMPEONATO ---
else:
    st.markdown(f"### 📊 Classificação Geral do Campeonato ({ano_selecionado})")
    st.caption("🏆 O ranking abaixo calcula e soma automaticamente todos os pontos conquistados pelas aves na temporada selecionada.")
    
    if df_etapas.empty:
        st.info(f"💡 A classificação geral de {ano_selecionado} aparecerá assim que os primeiros resultados forem lançados.")
    else:
        df_ranking = df_etapas.groupby(["Anilha", "Nome da Ave", "Proprietário", "Espécie"])["Pontos"].sum().reset_index()
        df_ranking = df_ranking.rename(columns={"Pontos": "Pontuação Acumulada"})
        
        abas_campeonato = st.tabs(especies_validas)
        for i, esp_nome in enumerate(especies_validas):
            with abas_campeonato[i]:
                df_rank_esp = df_ranking[df_ranking["Espécie"] == esp_nome].copy()
                
                if df_rank_esp.empty:
                    st.caption(f"Nenhuma ave da espécie {esp_nome} pontuou nesta temporada.")
                else:
                    df_rank_esp = df_rank_esp.sort_values(by="Pontuação Acumulada", ascending=False).reset_index(drop=True)
                    df_rank_esp.insert(0, "Posição", [f"{idx + 1}º Lugar" for idx in range(len(df_rank_esp))])
                    
                    st.dataframe(
                        df_rank_esp[["Posição", "Proprietário", "Nome da Ave", "Anilha", "Pontuação Acumulada"]],
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.write("")
                    if st.button(f"🏆 Gerar Imagem da Classificação Geral ({esp_nome})", key=f"img_geral_{ano_selecionado}_{esp_nome}", use_container_width=True):
                        img_geral_buf = gerar_imagem_oficial_aro(
                            titulo_banner="CLASSIFICAÇÃO GERAL",
                            subtitulo_info=f"Ranking Oficial Acumulado • Temporada {ano_selecionado}",
                            especie=esp_nome,
                            df_dados=df_rank_esp,
                            modo="geral"
                        )
                        st.image(img_geral_buf, caption=f"Ranking Geral Oficial - {esp_nome} ({ano_selecionado})", use_container_width=True)
                        st.download_button(
                            label=f"📥 Baixar Imagem Ranking Geral - {esp_nome}",
                            data=img_geral_buf,
                            file_name=f"classificacao_geral_{ano_selecionado}_{esp_nome.lower().replace(' ', '_')}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"dl_btn_geral_{ano_selecionado}_{esp_nome}"
                        )
