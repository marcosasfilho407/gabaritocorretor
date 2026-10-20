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

DISCIPLINAS_MAP = {
    "Filosofia (01-05)": range(1, 6),
    "História (06-10)": range(6, 11),
    "Geografia (11-15)": range(11, 16),
    "Sociologia (16-20)": range(16, 21),
    "Educação Física (21-24)": range(21, 25),
    "Inglês (25-30)": range(25, 31),
    "Português (31-40)": range(31, 41),
}

# ---------------------------------------------------------
# FUNÇÕES DE ESTILO, PERSISTÊNCIA E DADOS EMBUTIDOS
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
                    return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except Exception: pass
    return None

def aplicar_estilo_jt():
    bg_base64 = obter_imagem_fundo_base64()
    bg_css = f"""
        background: linear-gradient(rgba(5, 9, 20, 0.88), rgba(8, 15, 32, 0.94)), url('{bg_base64}');
        background-size: cover; background-position: center; background-attachment: fixed;
    """ if bg_base64 else "background: linear-gradient(135deg, #050811 0%, #0a1122 50%, #0d1830 100%);"

    st.markdown(f"""
        <style>
        .stApp {{ {bg_css} color: #E2E8F0; font-family: 'Segoe UI', Roboto, sans-serif; }}
        header[data-testid="stHeader"] {{ background: rgba(0, 0, 0, 0); }}
        .jt-header-container {{
            background: linear-gradient(135deg, rgba(16, 26, 50, 0.85) 0%, rgba(8, 14, 28, 0.95) 100%);
            border: 2px solid #FFB800; border-radius: 18px; padding: 20px 28px; margin-bottom: 25px;
            display: flex; align-items: center; gap: 22px;
        }}
        .jt-logo-emblem {{
            background: linear-gradient(145deg, #1E50FF, #0B2580); border: 3px solid #FFB800;
            border-radius: 14px; width: 72px; height: 72px; min-width: 72px;
            display: flex; align-items: center; justify-content: center;
            font-size: 38px; font-weight: 900; color: #FFB800;
        }}
        .jt-header-title {{
            font-size: 28px; font-weight: 800;
            background: linear-gradient(90deg, #FFFFFF 0%, #60A5FA 50%, #FFB800 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .jt-header-subtitle {{ font-size: 13px; color: #FF2A4B; font-weight: 700; letter-spacing: 2px; }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #1E50FF 0%, #0B2580 100%) !important;
            color: #FFB800 !important; border: 1px solid #FFB800 !important;
        }}
        .stButton > button {{
            background: linear-gradient(90deg, #1E50FF 0%, #2B60FF 100%) !important;
            color: #FFFFFF !important; border: 1px solid #FFB800 !important; font-weight: 700 !important;
        }}
        [data-testid="stExpander"] {{
            background: rgba(15, 23, 42, 0.75) !important;
            border: 1px solid rgba(30, 80, 255, 0.4) !important;
            border-radius: 12px !important; backdrop-filter: blur(10px);
        }}
        [data-testid="stMetricValue"] {{ color: #FFB800 !important; font-weight: 800 !important; }}
        [data-testid="stMetricLabel"] {{ color: #94A3B8 !important; font-weight: 600 !important; }}
        </style>
    """, unsafe_allow_html=True)

def carregar_imagem_com_exif(file_input):
    file_bytes = file_input.read()
    image_pil = Image.open(io.BytesIO(file_bytes))
    image_pil = ImageOps.exif_transpose(image_pil)
    return cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)

# GABARITOS E DADOS ESTUDANTES EMBUTIDOS (Fallback)
DADOS_ALUNOS_EMBUTIDOS = """Turma,Número,Matrícula,Nome
1º A,1,3256964,ADRIAN VINICIUS GONÇALVES OLIVEIRA
1º A,2,3976582,ANA ALICE TRINDADE SALES DE LIMA
1º A,3,3989573,ARTHUR GUSMAO SILVA CAMPELO
1º A,4,3987728,CAMILA SOARES RODRIGUES DA SILVA
1º B,1,,ANA BEATRIZ MOREIRA GOMES
2º A,1,,ALICE VITORIA DA SILVA BARROS
3º A,1,,ALICIA ELLEN MARQUES DA SILVA"""

GABARITOS_DEFAULT = {
    "1º Ano": {q: "ABCDE"[(q - 1) % 5] for q in range(1, 41)},
    "2º Ano": {q: "BCDEA"[(q - 1) % 5] for q in range(1, 41)},
    "3º Ano": {q: "CDEAB"[(q - 1) % 5] for q in range(1, 41)},
}

def salvar_gabaritos_em_disco(gabaritos_dict):
    try:
        with open(ARQUIVO_GABARITOS_JSON, "w", encoding="utf-8") as f:
            json.dump(gabaritos_dict, f, ensure_ascii=False, indent=2)
    except Exception as e: st.error(f"Erro ao salvar gabaritos: {e}")

def carregar_gabaritos_do_disco():
    if os.path.exists(ARQUIVO_GABARITOS_JSON):
        try:
            with open(ARQUIVO_GABARITOS_JSON, "r", encoding="utf-8") as f: dados = json.load(f)
            return {ano: {int(q): str(r) for q, r in gab.items()} for ano, gab in dados.items()}
        except Exception: pass
    salvar_gabaritos_em_disco(GABARITOS_DEFAULT)
    return GABARITOS_DEFAULT.copy()

def salvar_historico_em_disco(historico_list):
    try:
        with open(ARQUIVO_HISTORICO_JSON, "w", encoding="utf-8") as f:
            json.dump(historico_list, f, ensure_ascii=False, indent=2)
    except Exception as e: st.error(f"Erro ao salvar histórico: {e}")

def carregar_historico_do_disco():
    if os.path.exists(ARQUIVO_HISTORICO_JSON):
        try:
            with open(ARQUIVO_HISTORICO_JSON, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return []

def carregar_estudantes():
    if os.path.exists(ARQUIVO_ALUNOS_TXT):
        try: df = pd.read_csv(ARQUIVO_ALUNOS_TXT)
        except Exception: df = pd.read_csv(io.StringIO(DADOS_ALUNOS_EMBUTIDOS))
    else: df = pd.read_csv(io.StringIO(DADOS_ALUNOS_EMBUTIDOS))
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
# ETAPA 1: ENQUADRAMENTO EM MODO PAISAGEM (1200x800)
# E CLAREAMENTO LAB (SOFTWARE FLASH) Opcional
# ---------------------------------------------------------
def simular_flash_clarear(img_bgr, fator=1.4):
    """
    Simula o efeito de flash clareando a imagem no espaço LAB,
    que manipula a luminosidade separadamente das cores[cite: 14].
    Fator > 1.0 clareia, Fator < 1.0 escurece.
    """
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_processado = np.array(np.clip(l.astype(float) * fator, 0, 255), dtype=np.uint8)
    lab_processado = cv2.merge((l_processado, a, b))
    return cv2.cvtColor(lab_processado, cv2.COLOR_LAB2BGR)

def processar_e_retificar_paisagem(imagem, largura=1200, altura=800):
    """
    Garante orientação Paisagem e faz a projeção perspectiva baseada nas âncoras.
    Utiliza segmentação por quadrantes para ignorar bolinhas preenchidas[cite: 10, 11].
    """
    h_img, w_img = imagem.shape[:2]
    # Força orientação para modo Paisagem
    if h_img > w_img: imagem = cv2.rotate(imagem, cv2.ROTATE_90_CLOCKWISE); h_img, w_img = imagem.shape[:2]

    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray_enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray_enhanced, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 8)
    cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    candidatos = []
    for c in cnts:
        area = cv2.contourArea(c)
        if 20 < area < (w_img * h_img * 0.04):
            x, y, w, h = cv2.boundingRect(c); aspect = float(w) / h; extent = area / float(w * h)
            if 0.55 <= aspect <= 1.45 and extent > 0.40: candidatos.append((int(x + w / 2.0), int(y + h / 2.0), area))

    # Âncoras isoladas pelos 4 quadrantes externos
    q_tl = [c for c in candidatos if c[0] < w_img * 0.30 and c[1] < h_img * 0.30]
    q_tr = [c for c in candidatos if c[0] > w_img * 0.70 and c[1] < h_img * 0.30]
    q_br = [c for c in candidatos if c[0] > w_img * 0.70 and c[1] > h_img * 0.70]
    q_bl = [c for c in candidatos if c[0] < w_img * 0.30 and c[1] > h_img * 0.70]

    m_x, m_y = 35.0, 35.0
    pts_destino = np.array([[m_x, m_y], [largura - m_x, m_y], [largura - m_x, altura - m_y], [m_x, altura - m_y]], dtype="float32")

    if q_tl and q_tr and q_br and q_bl:
        tl = min(q_tl, key=lambda c: c[0] + c[1]); tr = max(q_tr, key=lambda c: c[0] - c[1]); br = max(q_br, key=lambda c: c[0] + c[1]); bl = min(q_bl, key=lambda c: c[0] - c[1])
        pts_origem = np.array([[tl[0], tl[1]], [tr[0], tr[1]], [br[0], br[1]], [bl[0], bl[1]]], dtype="float32")
        M = cv2.getPerspectiveTransform(pts_origem, pts_destino)
        warped = cv2.warpPerspective(imagem, M, (largura, altura))
    else: warped = cv2.resize(imagem, (largura, altura))

    # Verifica se a imagem está de ponta-cabeça (180°)
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    if np.sum(cv2.Canny(warped_gray[10:120, 100:1100], 50, 150)) > np.sum(cv2.Canny(warped_gray[680:790, 100:1100], 50, 150)) * 1.25: warped = cv2.rotate(warped, cv2.ROTATE_180)
    return warped

# ---------------------------------------------------------
# ETAPA 2: EXTRAÇÃO DA LISTA DE RESPOSTAS DO ALUNO (OMR)
# ---------------------------------------------------------
def extrair_respostas_aluno(img_warped, limiar_preenchimento=35.0):
    """
    Lê a imagem retificada e extrai unicamente a lista de respostas
    assinaladas pelo aluno (Questões 1 a 40), sem compará-las.
    Retorna: respostas_aluno (dict), img_marcacoes (image)
    """
    gray = cv2.cvtColor(img_warped, cv2.COLOR_BGR2GRAY)
    gray_proc = cv2.createCLAHE(clipLimit=2.5).apply(gray)
    blurred = cv2.GaussianBlur(gray_proc, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    img_marcacoes = img_warped.copy(); opcoes = ["A", "B", "C", "D", "E"]
    respostas_aluno = {}

    for q in range(1, 41):
        coords_opts = MAPA_COORDENADAS.get(q, []); taxas_preenchimento = []
        for (bx, by) in coords_opts:
            ix, iy = int(round(bx)), int(round(by))
            mask = np.zeros_like(thresh, dtype=np.uint8); cv2.circle(mask, (ix, iy), 8, 255, -1)
            taxas_preenchimento.append((cv2.countNonZero(cv2.bitwise_and(thresh, mask)) / float(cv2.countNonZero(mask))) * 100.0)

        max_idx = int(np.argmax(taxas_preenchimento)); max_val = taxas_preenchimento[max_idx]
        outras = [t for i, t in enumerate(taxas_preenchimento) if i != max_idx]; segunda_maior = max(outras) if outras else 0.0

        idx_marcado = max_idx if max_val >= limiar_preenchimento and (max_val - segunda_maior) >= 12.0 else -1
        respostas_aluno[q] = opcoes[idx_marcado] if idx_marcado != -1 else "Branco/Nulo"

        # Destaque visual das bolinhas lidas
        for opt_idx, (bx, by) in enumerate(coords_opts):
            cv2.circle(img_marcacoes, (int(round(bx)), int(round(by))), 11, (255, 255, 0), 1)
            if opt_idx == idx_marcado: cv2.circle(img_marcacoes, (int(round(bx)), int(round(by))), 9, (0, 255, 255), -1)
    return respostas_aluno, img_marcacoes

# ---------------------------------------------------------
# ETAPA 3: COMPARAÇÃO DA LISTA DE RESPOSTAS COM O GABARITO
# ---------------------------------------------------------
def comparar_respostas_com_gabarito(respostas_aluno, gabarito_oficial, img_warped):
    """
    Compara a lista de respostas extraída contra o Gabarito Oficial.
    Retorna: acertos, nota, acertos_por_disc, detalhes (dataframe), img_resultado
    """
    img_resultado = img_warped.copy(); opcoes = ["A", "B", "C", "D", "E"]
    total_por_disc = {"Filosofia (01-05)": 5, "História (06-10)": 5, "Geografia (11-15)": 5, "Sociologia (16-20)": 5, "Educação Física (21-24)": 4, "Inglês (25-30)": 6, "Português (31-40)": 10}
    acertos_por_disc = {disc: 0 for disc in total_por_disc.keys()}; detalhes = []; total_acertos = 0

    for q in range(1, 41):
        resp_aluno = respostas_aluno.get(q, "Branco/Nulo"); gab_correto = gabarito_oficial.get(q, "-"); correto = (resp_aluno == gab_correto); disc = obter_disciplina(q)
        if correto: acertos_por_disc[disc] += 1; total_acertos += 1
        detalhes.append({"Questão": q, "Disciplina": disc, "Resposta Aluno": resp_aluno, "Gabarito Oficial": gab_correto, "Resultado": "✅ Acertou" if correto else "❌ Errou"})

        # Desenha marcadores de correção sobre a imagem
        coords_opts = MAPA_COORDENADAS.get(q, [])
        for opt_idx, (bx, by) in enumerate(coords_opts):
            cv2.circle(img_resultado, (int(round(bx)), int(round(by))), 12, (255, 255, 0), 1)
            if opcoes[opt_idx] == resp_aluno: cv2.circle(img_resultado, (int(round(bx)), int(round(by))), 10, ((0, 255, 0) if correto else (0, 0, 255)), -1)
            elif opcoes[opt_idx] == gab_correto and not correto: cv2.circle(img_resultado, (int(round(bx)), int(round(by))), 11, (255, 0, 0), 2)
    return total_acertos, (total_acertos / 40.0) * 10.0, acertos_por_disc, detalhes, img_resultado

# ---------------------------------------------------------
# INTERFACE STREAMLIT E FLUXO PRINCIPAL
# ---------------------------------------------------------
st.set_page_config(page_title="EREM Joaquim Távora - Corretor OMR", layout="wide", page_icon="📌")
aplicar_estilo_jt()

if "gabaritos_oficiais" not in st.session_state: st.session_state["gabaritos_oficiais"] = carregar_gabaritos_do_disco()
if "historico" not in st.session_state: st.session_state["historico"] = carregar_historico_do_disco()
if "dados_turmas" not in st.session_state: st.session_state["dados_turmas"] = carregar_estudantes()

# Barra lateral com ajustes de câmera (Flash/Clareamento)
st.sidebar.markdown("---")
st.sidebar.subheader("Ajustes da Câmera")
ativar_flash_software = st.sidebar.toggle("Ativar Flash LAB (Clarear Foto)", value=True, help="Útil em ambientes com pouca luz[cite: 14].")
fator_flash = st.sidebar.slider("Intensidade do Flash", 1.1, 2.0, 1.4, 0.05, disabled=not ativar_flash_software)

st.markdown("""<div class="jt-header-container"><div class="jt-logo-emblem">JT</div><div><div class="jt-header-title">Corretor de Cartão-Resposta OMR</div><div class="jt-header-subtitle">EREM JOAQUIM TÁVORA • SIMULADO TRIMESTRAL</div></div></div>""", unsafe_allow_html=True)

tab_correcao, tab_gabarito, tab_estudantes, tab_relatorio = st.tabs(["📸 Corrigir Prova", "📝 Gabaritos Oficial", "👥 Estudantes por Turma", "📊 Resultados da Turma"])

# ABA 1: CORRIGIR PROVA (Captura e Extração -> Comparação)
with tab_correcao:
    st.header("Captura em Modo Paisagem & Extração de Respostas")
    col_info, col_cam = st.columns([1, 2])
    with col_info:
        st.subheader("1. Identificação do Estudante")
        dados_turmas = st.session_state["dados_turmas"]; lista_turmas = list(dados_turmas.keys())
        turma_selecionada = st.selectbox("Selecione a Turma:", options=lista_turmas, index=0)
        ano_estudante = obter_ano_da_turma(turma_selecionada); alunos_da_turma = dados_turmas.get(turma_selecionada, [])
        opcoes_alunos = [f"Nº {a['numero']} - {a['nome']}" if a["numero"] else a["nome"] for a in alunos_da_turma]
        if opcoes_alunos:
            aluno_idx = st.selectbox("Selecione o Aluno:", range(len(opcoes_alunos)), format_func=lambda i: opcoes_alunos[i]); aluno_obj = alunos_da_turma[aluno_idx]
            nome_aluno, num_aluno, mat_aluno = aluno_obj["nome"], aluno_obj["numero"], aluno_obj["matricula"]
        else: nome_aluno, num_aluno, mat_aluno = st.text_input("Nome do Aluno:"), "", ""
        with st.expander("📄 Ficha", expanded=True): st.markdown(f"**Nome:** {nome_aluno}"); st.markdown(f"**Turma:** {turma_selecionada} | **Nº Chamada:** {num_aluno}"); st.info(f"🎯 **Gabarito:** {ano_estudante}")
        st.divider(); sensibilidade_omr = st.slider("Sensibilidade OMR (% Tinta)", 15.0, 60.0, 35.0, 1.0)
    with col_cam:
        st.subheader("2. Foto do Cartão-Resposta (Modo Paisagem)")
        origem = st.radio("Fonte da Imagem:", ["Câmera", "Enviar Arquivo (Upload)"], horizontal=True); img_input = st.camera_input("Foto") if origem == "Câmera" else st.file_uploader("Upload", type=["png", "jpg", "jpeg"])

    if img_input:
        if not nome_aluno: st.warning("⚠️ Selecione o aluno antes de prosseguir.")
        else:
            # -----------------------------------------------------
            # PASSO A: Retificação Paisagem (Clareamento se ativado)
            # -----------------------------------------------------
            img_raw = carregar_imagem_com_exif(img_input)
            if ativar_flash_software: img_raw = simular_flash_clarear(img_raw, fator_flash)
            img_warped = processar_e_retificar_paisagem(img_raw)
            # PASSO B: Extração OMR pura das respostas do aluno
            respostas_aluno, img_marcacoes = extrair_respostas_aluno(img_warped, sensibilidade_omr)
            # PASSO C: Comparação com Gabarito Oficial
            gabarito_oficial = st.session_state["gabaritos_oficiais"].get(ano_estudante, {})
            total_acertos, nota, acertos_por_disc, detalhes, img_resultado = comparar_respostas_com_gabarito(respostas_aluno, gabarito_oficial, img_warped)

            st.divider(); st.subheader("📋 Resumo da Correção"); m1, m2, m3 = st.columns(3); m1.metric("Total Acertos", f"{total_acertos}/40"); m2.metric("Nota Final", f"{nota:.2f}/10"); m3.metric("Estudante", f"{nome_aluno} ({turma_selecionada})")
            total_por_disc = {"Filosofia (01-05)": 5, "História (06-10)": 5, "Geografia (11-15)": 5, "Sociologia (16-20)": 5, "Educação Física (21-24)": 4, "Inglês (25-30)": 6, "Português (31-40)": 10}
            cols_disc = st.columns(len(acertos_por_disc))
            for i, (d_nome, d_acertos) in enumerate(acertos_por_disc.items()): cols_disc[i].metric(d_nome.split(" ")[0], f"{d_acertos}/{total_por_disc.get(d_nome, 5)}")

            if st.button("💾 Salvar Resultado", type="primary"):
                registro = {"Série": ano_estudante, "Turma": turma_selecionada, "Nº": num_aluno, "Matrícula": mat_aluno, "Aluno": nome_aluno, "Total Acertos": total_acertos, "Nota Final": round(nota, 2)}
                for d_nome, d_acertos in acertos_por_disc.items(): registro[d_nome.split(" ")[0]] = f"{d_acertos}/{total_por_disc.get(d_nome, 5)}"
                st.session_state["historico"].append(registro); salvar_historico_em_disco(st.session_state["historico"]); st.success(f"Resultado salvo!")

            st.divider(); c_res1, c_res2 = st.columns(2)
            with c_res1:
                st.subheader("Análise OMR e Gabarito Sobreposto")
                s1, s2 = st.tabs(["Gabarito Sobreposto (Correção)", "Mapa OMR (Extração)"])
                s1.image(img_resultado, channels="BGR", use_container_width=True, caption="🟢 Acerto | 🔴 Erro | 🔵 Correta Omitida")
                s2.image(img_marcacoes, channels="BGR", use_container_width=True, caption="🟡 Alternativas detectadas pelo OMR.")
            with c_res2: st.subheader("Detalhamento por Questão"); st.dataframe(pd.DataFrame(detalhes), height=380, use_container_width=True)

# ABA 2: GABARITOS OFICIAIS
with tab_gabarito:
    st.header("Cadastrar e Gerenciar Gabaritos Oficiais")
    ano_gab_sel = st.selectbox("Selecione Ano para Editar:", ["1º Ano", "2º Ano", "3º Ano"])
    disc_filtro = st.selectbox("Filtrar Disciplina:", ["Todas as Disciplinas"] + list(DISCIPLINAS_MAP.keys()))
    gabarito_ano_atual = st.session_state["gabaritos_oficiais"].get(ano_gab_sel, {})
    df_gab_editor = pd.DataFrame([{"Questão": q, "Disciplina": obter_disciplina(q), "Gabarito Oficial": gabarito_ano_atual.get(q, "A")} for q in (range(1, 41) if disc_filtro == "Todas as Disciplinas" else DISCIPLINAS_MAP[disc_filtro])])
    df_gab_modificado = st.data_editor(df_gab_editor, column_config={"Gabarito Oficial": st.column_config.SelectboxColumn("Resposta Correta", options=["A", "B", "C", "D", "E"], required=True)}, hide_index=True, use_container_width=True)
    if st.button("💾 Salvar Gabarito", type="primary"):
        for _, row_g in df_gab_modificado.iterrows(): st.session_state["gabaritos_oficiais"][ano_gab_sel][int(row_g["Questão"])] = str(row_g["Gabarito Oficial"])
        salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"]); st.success(f"Gabarito salvo permanentemente!")

# ABA 3: ESTUDANTES
with tab_estudantes:
    st.header("Estudantes Cadastrados por Turma")
    st.dataframe(pd.DataFrame(st.session_state["dados_turmas"].get(st.selectbox("Visualizar Turma:", list(st.session_state["dados_turmas"].keys())), [])), use_container_width=True)

# ABA 4: RELATÓRIO TURMA
with tab_relatorio:
    st.header("Relatório Geral"); df_h = pd.DataFrame(st.session_state["historico"]); st.dataframe(df_h, use_container_width=True) if st.session_state["historico"] else st.info("Nenhum resultado salvo.")