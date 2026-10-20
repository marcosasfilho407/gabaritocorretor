import io
import json
import os
import base64
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

# ---------------------------------------------------------
# CONSTANTES E ARQUIVOS DE PERSISTÊNCIA EM DISCO
# ---------------------------------------------------------
ARQUIVO_GABARITOS_JSON = "gabaritos_oficiais.json"
ARQUIVO_HISTORICO_JSON = "historico_correcoes.json"
ARQUIVO_ALUNOS_TXT = "todososalunosporturma.txt"

# ---------------------------------------------------------
# MATRIZ DE COORDENADAS EXATAS (X, Y) PARA AS 40 QUESTÕES
# (Calibrado para o cartão padronizado em 1200 x 800 px)
# ---------------------------------------------------------
def gerar_mapa_coordenadas_exatas():
    coords = {}

    # Coluna 0: Filosofia (Q01-05) e História (Q06-10)
    xs_col0 = [84.0, 127.0, 170.0, 213.0, 256.0]
    for i, q in enumerate(range(1, 6)):
        coords[q] = [(x, 281.0 + i * 42.0) for x in xs_col0]
    for i, q in enumerate(range(6, 11)):
        coords[q] = [(x, 548.0 + i * 42.0) for x in xs_col0]

    # Coluna 1: Geografia (Q11-15) e Sociologia (Q16-20)
    xs_col1 = [384.0, 427.0, 470.0, 513.0, 556.0]
    for i, q in enumerate(range(11, 16)):
        coords[q] = [(x, 281.0 + i * 42.0) for x in xs_col1]
    for i, q in enumerate(range(16, 21)):
        coords[q] = [(x, 548.0 + i * 42.0) for x in xs_col1]

    # Coluna 2: Educação Física (Q21-24) e Inglês (Q25-30)
    xs_col2 = [684.0, 727.0, 770.0, 813.0, 856.0]
    for i, q in enumerate(range(21, 25)):
        coords[q] = [(x, 281.0 + i * 42.0) for x in xs_col2]
    for i, q in enumerate(range(25, 31)):
        coords[q] = [(x, 548.0 + i * 42.0) for x in xs_col2]

    # Coluna 3: Português (Q31-40)
    xs_col3 = [933.0, 980.0, 1027.0, 1074.0, 1121.0]
    for i, q in enumerate(range(31, 41)):
        coords[q] = [(x, 281.0 + i * 47.0) for x in xs_col3]

    return coords

MAPA_COORDENADAS = gerar_mapa_coordenadas_exatas()

# ---------------------------------------------------------
# FUNÇÃO DE OBTENÇÃO DA IMAGEM DE FUNDO (BASE64)
# ---------------------------------------------------------
def obter_imagem_fundo_base64():
    candidatos = [
        "Gemini_Generated_Image_vktbzrvktbzrvktb.jfif",
        "background.jfif",
        "background.jpg",
        "background.png",
        "jt_background.jfif",
        "input_file_8.png"
    ]
    for c in candidatos:
        if os.path.exists(c):
            try:
                with open(c, "rb") as f:
                    data = f.read()
                    b64 = base64.b64encode(data).decode("utf-8")
                    ext = "jpeg" if c.endswith((".jpg", ".jpeg", ".jfif")) else "png"
                    return f"data:image/{ext};base64,{b64}"
            except Exception:
                pass
    return None

def carregar_imagem_com_exif(file_input):
    file_bytes = file_input.read()
    image_pil = Image.open(io.BytesIO(file_bytes))
    image_pil = ImageOps.exif_transpose(image_pil)
    image_np = np.array(image_pil.convert("RGB"))
    return cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------
# ESTILIZAÇÃO CSS COM TEMAS JT
# ---------------------------------------------------------
def aplicar_estilo_jt():
    bg_base64 = obter_imagem_fundo_base64()
    bg_css = f"""
        background: linear-gradient(rgba(5, 9, 20, 0.88), rgba(8, 15, 32, 0.94)), url('{bg_base64}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """ if bg_base64 else "background: linear-gradient(135deg, #050811 0%, #0a1122 50%, #0d1830 100%);"

    st.markdown(f"""
        <style>
        .stApp {{ {bg_css} color: #E2E8F0; font-family: 'Segoe UI', Roboto, sans-serif; }}
        header[data-testid="stHeader"] {{ background: rgba(0, 0, 0, 0); }}
        .jt-header-container {{
            background: linear-gradient(135deg, rgba(16, 26, 50, 0.85) 0%, rgba(8, 14, 28, 0.95) 100%);
            border: 2px solid #FFB800;
            box-shadow: 0 0 25px rgba(30, 80, 255, 0.4);
            border-radius: 18px;
            padding: 20px 28px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 22px;
        }}
        .jt-logo-emblem {{
            background: linear-gradient(145deg, #1E50FF, #0B2580);
            border: 3px solid #FFB800;
            border-radius: 14px;
            width: 72px; height: 72px; min-width: 72px;
            display: flex; align-items: center; justify-content: center;
            font-size: 38px; font-weight: 900; color: #FFB800;
        }}
        .jt-header-title {{
            font-size: 28px; font-weight: 800;
            background: linear-gradient(90deg, #FFFFFF 0%, #60A5FA 50%, #FFB800 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .jt-header-subtitle {{
            font-size: 13px; color: #FF2A4B; font-weight: 700; letter-spacing: 2px;
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #1E50FF 0%, #0B2580 100%) !important;
            color: #FFB800 !important; border: 1px solid #FFB800 !important;
        }}
        .stButton > button {{
            background: linear-gradient(90deg, #1E50FF 0%, #2B60FF 100%) !important;
            color: #FFFFFF !important; border: 1px solid #FFB800 !important; font-weight: 700 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# BANCO DE DADOS E GABARITOS
# ---------------------------------------------------------
DADOS_ALUNOS_EMBUTIDOS = """Turma,Número,Matrícula,Nome
1º A,1,3256964,ADRIAN VINICIUS GONÇALVES OLIVEIRA
1º A,2,3976582,ANA ALICE TRINDADE SALES DE LIMA
1º A,3,3989573,ARTHUR GUSMAO SILVA CAMPELO
1º A,4,3987728,CAMILA SOARES RODRIGUES DA SILVA
1º A,5,3866482,DANIEL HOPPER SILVA"""

GABARITO_1ANO_BASE = {q: "ABCDE"[(q - 1) % 5] for q in range(1, 41)}
GABARITO_2ANO_BASE = {q: "BCDEA"[(q - 1) % 5] for q in range(1, 41)}
GABARITO_3ANO_BASE = {q: "CDEAB"[(q - 1) % 5] for q in range(1, 41)}

GABARITOS_MULTI_ANO_DEFAULT = {
    "1º Ano": GABARITO_1ANO_BASE.copy(),
    "2º Ano": GABARITO_2ANO_BASE.copy(),
    "3º Ano": GABARITO_3ANO_BASE.copy(),
}

DISCIPLINAS_MAP = {
    "Filosofia (01-05)": range(1, 6),
    "História (06-10)": range(6, 11),
    "Geografia (11-15)": range(11, 16),
    "Sociologia (16-20)": range(16, 21),
    "Educação Física (21-24)": range(21, 25),
    "Inglês (25-30)": range(25, 31),
    "Português (31-40)": range(31, 41),
}

def salvar_gabaritos_em_disco(gabaritos_dict):
    try:
        with open(ARQUIVO_GABARITOS_JSON, "w", encoding="utf-8") as f:
            json.dump(gabaritos_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar gabaritos: {e}")

def carregar_gabaritos_do_disco():
    if os.path.exists(ARQUIVO_GABARITOS_JSON):
        try:
            with open(ARQUIVO_GABARITOS_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return {ano: {int(q): str(r) for q, r in gab.items()} for ano, gab in dados.items()}
        except Exception:
            pass
    salvar_gabaritos_em_disco(GABARITOS_MULTI_ANO_DEFAULT)
    return GABARITOS_MULTI_ANO_DEFAULT.copy()

def salvar_historico_em_disco(historico_list):
    try:
        with open(ARQUIVO_HISTORICO_JSON, "w", encoding="utf-8") as f:
            json.dump(historico_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {e}")

def carregar_historico_do_disco():
    if os.path.exists(ARQUIVO_HISTORICO_JSON):
        try:
            with open(ARQUIVO_HISTORICO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def carregar_estudantes():
    if os.path.exists(ARQUIVO_ALUNOS_TXT):
        try:
            df = pd.read_csv(ARQUIVO_ALUNOS_TXT)
        except Exception:
            df = pd.read_csv(io.StringIO(DADOS_ALUNOS_EMBUTIDOS))
    else:
        df = pd.read_csv(io.StringIO(DADOS_ALUNOS_EMBUTIDOS))

    turmas = {}
    for turma, group in df.groupby("Turma", sort=False):
        alunos = []
        for _, row in group.iterrows():
            num = str(int(row["Número"])) if pd.notna(row["Número"]) and str(row["Número"]).strip() != "" else ""
            mat = str(int(row["Matrícula"])) if pd.notna(row["Matrícula"]) and str(row["Matrícula"]).strip() != "" else ""
            nome = str(row["Nome"]).strip()
            alunos.append({"numero": num, "matricula": mat, "nome": nome})
        turmas[str(turma).strip()] = alunos
    return turmas

def obter_ano_da_turma(turma):
    if "1º" in turma or "1" in turma: return "1º Ano"
    if "2º" in turma or "2" in turma: return "2º Ano"
    if "3º" in turma or "3" in turma: return "3º Ano"
    return "1º Ano"

def obter_disciplina(q):
    for disc, q_range in DISCIPLINAS_MAP.items():
        if q in q_range: return disc
    return "Desconhecida"

# ---------------------------------------------------------
# CONFIGURAÇÃO INICIAL E ESTILO
# ---------------------------------------------------------
st.set_page_config(page_title="EREM Joaquim Távora - Corretor OMR", layout="wide", page_icon="📌")
aplicar_estilo_jt()

if "gabaritos_oficiais" not in st.session_state:
    st.session_state["gabaritos_oficiais"] = carregar_gabaritos_do_disco()
if "historico" not in st.session_state:
    st.session_state["historico"] = carregar_historico_do_disco()
if "dados_turmas" not in st.session_state:
    st.session_state["dados_turmas"] = carregar_estudantes()

st.markdown("""
    <div class="jt-header-container">
        <div class="jt-logo-emblem">JT</div>
        <div>
            <div class="jt-header-title">Corretor de Cartão-Resposta OMR</div>
            <div class="jt-header-subtitle">EREM JOAQUIM TÁVORA • SIMULADO TRIMESTRAL</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ALINHAMENTO PERSPECTIVO COM RETIFICAÇÃO EXATA
# ---------------------------------------------------------
def auto_orientar_e_retificar_completo(imagem, largura=1200, altura=800):
    h_img, w_img = imagem.shape[:2]
    if h_img > w_img:
        imagem = cv2.rotate(imagem, cv2.ROTATE_90_CLOCKWISE)
        h_img, w_img = imagem.shape[:2]

    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray_enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray_enhanced, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 8
    )

    cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    candidatos = []
    for c in cnts:
        area = cv2.contourArea(c)
        if 20 < area < (w_img * h_img * 0.04):
            x, y, w, h = cv2.boundingRect(c)
            aspect = float(w) / h
            extent = area / float(w * h)
            if 0.55 <= aspect <= 1.45 and extent > 0.40:
                cx = int(x + w / 2.0)
                cy = int(y + h / 2.0)
                candidatos.append((cx, cy, area))

    q_tl = [c for c in candidatos if c[0] < w_img * 0.30 and c[1] < h_img * 0.30]
    q_tr = [c for c in candidatos if c[0] > w_img * 0.70 and c[1] < h_img * 0.30]
    q_br = [c for c in candidatos if c[0] > w_img * 0.70 and c[1] > h_img * 0.70]
    q_bl = [c for c in candidatos if c[0] < w_img * 0.30 and c[1] > h_img * 0.70]

    m_x, m_y = 35.0, 35.0
    pts_destino = np.array([
        [m_x, m_y], [largura - m_x, m_y], [largura - m_x, altura - m_y], [m_x, altura - m_y]
    ], dtype="float32")

    if q_tl and q_tr and q_br and q_bl:
        tl = min(q_tl, key=lambda c: c[0] + c[1])
        tr = max(q_tr, key=lambda c: c[0] - c[1])
        br = max(q_br, key=lambda c: c[0] + c[1])
        bl = min(q_bl, key=lambda c: c[0] - c[1])

        pts_origem = np.array([[tl[0], tl[1]], [tr[0], tr[1]], [br[0], br[1]], [bl[0], bl[1]]], dtype="float32")
        M = cv2.getPerspectiveTransform(pts_origem, pts_destino)
        warped = cv2.warpPerspective(imagem, M, (largura, altura))
    else:
        warped = cv2.resize(imagem, (largura, altura))

    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    top_region = warped_gray[10:120, 100:1100]
    bot_region = warped_gray[680:790, 100:1100]

    if np.sum(cv2.Canny(top_region, 50, 150)) > np.sum(cv2.Canny(bot_region, 50, 150)) * 1.25:
        warped = cv2.rotate(warped, cv2.ROTATE_180)

    return warped

# ---------------------------------------------------------
# ALGORITMO OMR DE PRECISÃO MATRICIAL
# ---------------------------------------------------------
def ler_respostas_40_questoes(img_warped, gabarito_oficial=None, limiar_preenchimento=35.0, questoes_filtro=None):
    gray = cv2.cvtColor(img_warped, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray_proc = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray_proc, (3, 3), 0)

    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    img_annotated = img_warped.copy()
    opcoes = ["A", "B", "C", "D", "E"]
    respostas_aluno = {}

    questoes_para_ler = questoes_filtro if questoes_filtro else range(1, 41)

    for q in questoes_para_ler:
        coords_opts = MAPA_COORDENADAS.get(q, [])
        taxas_preenchimento = []

        for (bx, by) in coords_opts:
            ix, iy = int(round(bx)), int(round(by))
            
            mask = np.zeros_like(thresh, dtype=np.uint8)
            cv2.circle(mask, (ix, iy), 8, 255, -1)

            pix_marcados = cv2.countNonZero(cv2.bitwise_and(thresh, mask))
            total_pix = cv2.countNonZero(mask)

            ratio = (pix_marcados / float(total_pix)) * 100.0 if total_pix > 0 else 0.0
            taxas_preenchimento.append(ratio)

        max_idx = int(np.argmax(taxas_preenchimento))
        max_val = taxas_preenchimento[max_idx]

        outras = [t for i, t in enumerate(taxas_preenchimento) if i != max_idx]
        segunda_maior = max(outras) if outras else 0.0

        if max_val >= limiar_preenchimento and (max_val - segunda_maior) >= 12.0:
            resp_detectada = opcoes[max_idx]
            idx_marcado = max_idx
        else:
            resp_detectada = "Branco/Nulo"
            idx_marcado = -1

        respostas_aluno[q] = resp_detectada
        gab_correto = gabarito_oficial.get(q) if gabarito_oficial else None

        for opt_idx, (bx, by) in enumerate(coords_opts):
            ix, iy = int(round(bx)), int(round(by))
            opcao_letra = opcoes[opt_idx]

            # Desenha anel ciano guia na posição calculada
            cv2.circle(img_annotated, (ix, iy), 12, (255, 255, 0), 1)

            if opt_idx == idx_marcado:
                if gab_correto and opcao_letra == gab_correto:
                    cor = (0, 255, 0) # Verde se acertou
                elif gab_correto and opcao_letra != gab_correto:
                    cor = (0, 0, 255) # Vermelho se errou
                else:
                    cor = (0, 255, 255)
                cv2.circle(img_annotated, (ix, iy), 10, cor, -1)
            elif gab_correto and opcao_letra == gab_correto and resp_detectada != gab_correto:
                cv2.circle(img_annotated, (ix, iy), 11, (255, 0, 0), 2)

    return respostas_aluno, img_annotated

# ---------------------------------------------------------
# ABAS DE NAVEGAÇÃO
# ---------------------------------------------------------
tab_correcao, tab_gabarito, tab_estudantes, tab_relatorio = st.tabs([
    "📷 Corrigir Prova", "📝 Gabaritos Oficiais", "👥 Estudantes por Turma", "📊 Resultados da Turma"
])

# ABA 1: CORRIGIR PROVA
with tab_correcao:
    st.header("Captura ou Upload do Cartão de Respostas")
    col_info, col_cam = st.columns([1, 2])

    with col_info:
        st.subheader("Identificação do Estudante")
        dados_turmas = st.session_state["dados_turmas"]
        lista_turmas = list(dados_turmas.keys())

        turma_selecionada = st.selectbox("Selecione a Turma:", options=lista_turmas, index=0)
        ano_estudante = obter_ano_da_turma(turma_selecionada)
        alunos_da_turma = dados_turmas.get(turma_selecionada, [])

        opcoes_alunos = [f"Nº {a['numero']} - {a['nome']}" if a["numero"] else a["nome"] for a in alunos_da_turma]

        if opcoes_alunos:
            aluno_idx = st.selectbox("Selecione o Aluno:", range(len(opcoes_alunos)), format_func=lambda i: opcoes_alunos[i])
            aluno_obj = alunos_da_turma[aluno_idx]
            nome_aluno, num_aluno, mat_aluno = aluno_obj["nome"], aluno_obj["numero"], aluno_obj["matricula"]
        else:
            nome_aluno, num_aluno, mat_aluno = st.text_input("Nome do Aluno:"), "", ""

        with st.expander("📄 Ficha do Aluno e Gabarito Vinculado", expanded=True):
            st.markdown(f"**Nome:** {nome_aluno}")
            st.markdown(f"**Turma:** {turma_selecionada} | **Nº Chamada:** {num_aluno if num_aluno else 'N/A'}")
            st.info(f"🎯 **Gabarito Oficial Aplicado:** {ano_estudante}")

        sensibilidade_omr = st.slider("Limiar de Preenchimento (% Mínima de Tinta)", 15.0, 60.0, 35.0, 1.0)

    with col_cam:
        modo_fotos = st.radio("Modo de Captura:", ["📸 Foto Única (Cartão Completo)", "📸 Duas Fotos Complementares"], horizontal=True)
        origem = st.radio("Fonte da Imagem:", ["Câmera", "Enviar Arquivo (Upload)"], horizontal=True)

        img_input_1, img_input_2 = None, None

        if modo_fotos == "📸 Foto Única (Cartão Completo)":
            img_input_1 = st.camera_input("Foto do Cartão") if origem == "Câmera" else st.file_uploader("Upload do Cartão Completo", type=["png", "jpg", "jpeg"])
        else:
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                img_input_1 = st.camera_input("Metade 1 (Q01-20)", key="c1") if origem == "Câmera" else st.file_uploader("Metade 1", type=["png", "jpg", "jpeg"], key="u1")
            with c_f2:
                img_input_2 = st.camera_input("Metade 2 (Q21-40)", key="c2") if origem == "Câmera" else st.file_uploader("Metade 2", type=["png", "jpg", "jpeg"], key="u2")

    if (modo_fotos == "📸 Foto Única (Cartão Completo)" and img_input_1) or (modo_fotos != "📸 Foto Única (Cartão Completo)" and img_input_1 and img_input_2):
        if not nome_aluno:
            st.warning("⚠️ Por favor, selecione o aluno.")
        else:
            gabarito = st.session_state["gabaritos_oficiais"].get(ano_estudante, {})

            if modo_fotos == "📸 Foto Única (Cartão Completo)":
                img = carregar_imagem_com_exif(img_input_1)
                img_warped = auto_orientar_e_retificar_completo(img)
                respostas_aluno, img_annotated_1 = ler_respostas_40_questoes(img_warped, gabarito, sensibilidade_omr)
                img_annotated_2 = None
            else:
                img1 = carregar_imagem_com_exif(img_input_1)
                warped1 = auto_orientar_e_retificar_completo(img1)
                resp1, img_annotated_1 = ler_respostas_40_questoes(warped1, gabarito, sensibilidade_omr, range(1, 21))

                img2 = carregar_imagem_com_exif(img_input_2)
                warped2 = auto_orientar_e_retificar_completo(img2)
                resp2, img_annotated_2 = ler_respostas_40_questoes(warped2, gabarito, sensibilidade_omr, range(21, 41))

                respostas_aluno = {**resp1, **resp2}

            acertos_por_disc = {}
            total_por_disc = {"Filosofia (01-05)": 5, "História (06-10)": 5, "Geografia (11-15)": 5, "Sociologia (16-20)": 5, "Educação Física (21-24)": 4, "Inglês (25-30)": 6, "Português (31-40)": 10}

            detalhes, total_acertos = [], 0
            for q in range(1, 41):
                resp, gab = respostas_aluno.get(q, "Branco/Nulo"), gabarito.get(q, "-")
                correto = (resp == gab)
                disc = obter_disciplina(q)

                acertos_por_disc[disc] = acertos_por_disc.get(disc, 0) + (1 if correto else 0)
                if correto: total_acertos += 1

                detalhes.append({"Questão": q, "Disciplina": disc, "Resposta Aluno": resp, "Gabarito": gab, "Status": "✅ Acertou" if correto else "❌ Errou"})

            nota = (total_acertos / 40.0) * 10.0

            st.divider()
            st.subheader("Resumo do Desempenho")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Acertos", f"{total_acertos} / 40")
            m2.metric("Nota Final", f"{nota:.2f} / 10.0")
            m3.metric("Estudante / Turma", f"{nome_aluno} ({turma_selecionada})")

            cols_disc = st.columns(len(acertos_por_disc))
            for i, (d_nome, d_acertos) in enumerate(acertos_por_disc.items()):
                cols_disc[i].metric(d_nome.split(" ")[0], f"{d_acertos}/{total_por_disc.get(d_nome, 5)}")

            if st.button("💾 Salvar Resultado no Histórico", type="primary"):
                registro = {"Série": ano_estudante, "Turma": turma_selecionada, "Nº": num_aluno, "Matrícula": mat_aluno, "Aluno": nome_aluno, "Total Acertos": total_acertos, "Nota Final": round(nota, 2)}
                for d_nome, d_acertos in acertos_por_disc.items():
                    registro[d_nome.split(" ")[0]] = f"{d_acertos}/{total_por_disc.get(d_nome, 5)}"
                st.session_state["historico"].append(registro)
                salvar_historico_em_disco(st.session_state["historico"])
                st.success(f"Resultado de {nome_aluno} salvo com sucesso!")

            col_img, col_det = st.columns(2)
            with col_img:
                st.subheader("Imagens Processadas (Overlay OMR)")
                if img_annotated_2 is None:
                    st.image(img_annotated_1, channels="BGR", use_container_width=True)
                else:
                    c1, c2 = st.columns(2)
                    c1.image(img_annotated_1, channels="BGR", use_container_width=True)
                    c2.image(img_annotated_2, channels="BGR", use_container_width=True)
                st.caption("🟡 Círculo Ciano = Gabarito | 🟢 Verde = Acerto | 🔴 Vermelho = Erro")

            with col_det:
                st.subheader("Detalhamento por Questão")
                st.dataframe(pd.DataFrame(detalhes), height=380, use_container_width=True)

# ABA 2: GABARITOS OFICIAIS
with tab_gabarito:
    st.header("Cadastrar e Gerenciar Gabaritos Oficiais")
    ano_gab_sel = st.selectbox("Selecione o Ano / Série para Editar:", ["1º Ano", "2º Ano", "3º Ano"])
    disc_filtro = st.selectbox("Filtrar por Disciplina:", ["Todas as Disciplinas"] + list(DISCIPLINAS_MAP.keys()))

    gabarito_ano_atual = st.session_state["gabaritos_oficiais"].get(ano_gab_sel, {})
    questoes_exibidas = range(1, 41) if disc_filtro == "Todas as Disciplinas" else DISCIPLINAS_MAP[disc_filtro]

    df_gab_editor = pd.DataFrame([{"Questão": q, "Disciplina": obter_disciplina(q), "Gabarito": gabarito_ano_atual.get(q, "A")} for q in questoes_exibidas])

    df_gab_modificado = st.data_editor(df_gab_editor, column_config={"Gabarito": st.column_config.SelectboxColumn("Resposta Correta", options=["A", "B", "C", "D", "E"], required=True)}, hide_index=True, use_container_width=True)

    if st.button("💾 Salvar Alterações na Tabela", type="primary"):
        for _, row_g in df_gab_modificado.iterrows():
            st.session_state["gabaritos_oficiais"][ano_gab_sel][int(row_g["Questão"])] = str(row_g["Gabarito"])
        salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"])
        st.success(f"Gabarito do {ano_gab_sel} salvo permanentemente!")

# ABA 3: ESTUDANTES
with tab_estudantes:
    st.header("Lista de Estudantes Cadastrados por Turma")
    turmas_map = st.session_state["dados_turmas"]
    t_sel = st.selectbox("Visualizar Turma:", list(turmas_map.keys()))
    st.dataframe(pd.DataFrame(turmas_map.get(t_sel, [])), use_container_width=True)

# ABA 4: RELATÓRIO
with tab_relatorio:
    st.header("Relatório Geral das Correções")
    if st.session_state["historico"]:
        df_h = pd.DataFrame(st.session_state["historico"])
        st.dataframe(df_h, use_container_width=True)
        st.download_button("📥 Baixar Planilha de Notas (CSV)", df_h.to_csv(index=False).encode("utf-8"), "resultados.csv", "text/csv")
    else:
        st.info("Nenhum cartão corrigido e salvo ainda.")