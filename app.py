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

# Coordenadas calibradas para o cartão em modo Paisagem (1200x800)
def gerar_mapa_coordenadas_exatas():
    coords = {}
    # Coluna 0: Filosofia (Q01-05) e História (Q06-10)
    xs_col0 = [84.0, 127.0, 170.0, 213.0, 256.0]
    for i, q in enumerate(range(1, 6)): coords[q] = [(x, 281.0 + i * 42.0) for x in xs_col0]
    for i, q in enumerate(range(6, 11)): coords[q] = [(x, 548.0 + i * 42.0) for x in xs_col0]
    # Coluna 1: Geografia (Q11-15) e Sociologia (Q16-20)
    xs_col1 = [384.0, 427.0, 470.0, 513.0, 556.0]
    for i, q in enumerate(range(11, 16)): coords[q] = [(x, 281.0 + i * 42.0) for x in xs_col1]
    for i, q in enumerate(range(16, 21)): coords[q] = [(x, 548.0 + i * 42.0) for x in xs_col1]
    # Coluna 2: Educação Física (Q21-24) e Inglês (Q25-30)
    xs_col2 = [684.0, 727.0, 770.0, 813.0, 856.0]
    for i, q in enumerate(range(21, 25)): coords[q] = [(x, 281.0 + i * 42.0) for x in xs_col2]
    for i, q in enumerate(range(25, 31)): coords[q] = [(x, 548.0 + i * 42.0) for x in xs_col2]
    # Coluna 3: Português (Q31-40)
    xs_col3 = [933.0, 980.0, 1027.0, 1074.0, 1121.0]
    for i, q in enumerate(range(31, 41)): coords[q] = [(x, 281.0 + i * 47.0) for x in xs_col3]
    return coords

MAPA_COORDENADAS = gerar_mapa_coordenadas_exatas()

DISCIPLINAS_MAP = {
    "Filosofia (01-05)": range(1, 6), "História (06-10)": range(6, 11), "Geografia (11-15)": range(11, 16),
    "Sociologia (16-20)": range(16, 21), "Educação Física (21-24)": range(21, 25), "Inglês (25-30)": range(25, 31),
    "Português (31-40)": range(31, 41),
}

# ---------------------------------------------------------
# FUNÇÕES DE PERSISTÊNCIA E AUXILIARES
# ---------------------------------------------------------
def obter_imagem_fundo_base64():
    candidatos = ["input_file_8.png", "background.jpg"]
    for c in candidatos:
        if os.path.exists(c):
            try:
                with open(c, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except Exception: pass
    return None

def carregar_imagem_com_exif(file_input):
    file_bytes = file_input.read()
    image_pil = Image.open(io.BytesIO(file_bytes))
    image_pil = ImageOps.exif_transpose(image_pil)
    return cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)

def aplicar_estilo_jt():
    bg_base64 = obter_imagem_fundo_base64()
    bg_css = f"background: linear-gradient(rgba(5, 9, 20, 0.88), rgba(8, 15, 32, 0.94)), url('{bg_base64}'); background-size: cover; background-position: center; background-attachment: fixed;" if bg_base64 else "background: linear-gradient(135deg, #050811 0%, #0a1122 50%, #0d1830 100%);"
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
        .stTabs [aria-selected="true"] {{ background: linear-gradient(135deg, #1E50FF 0%, #0B2580 100%) !important; color: #FFB800 !important; border: 1px solid #FFB800 !important; }}
        .stButton > button {{ background: linear-gradient(90deg, #1E50FF 0%, #2B60FF 100%) !important; color: #FFFFFF !important; border: 1px solid #FFB800 !important; font-weight: 700 !important; }}
        </style>
    """, unsafe_allow_html=True)

# Banco de dados e Gabaritos (Simplificado para o código)
DADOS_ALUNOS_EMBUTIDOS = """Turma,Número,Matrícula,Nome
1º A,1,3256964,ADRIAN VINICIUS GONÇALVES OLIVEIRA
1º A,2,3976582,ANA ALICE TRINDADE SALES DE LIMA
1º A,3,3989573,ARTHUR GUSMAO SILVA CAMPELO"""

GABARITOS_DEFAULT = {
    "1º Ano": {q: "ABCDE"[(q - 1) % 5] for q in range(1, 41)},
    "2º Ano": {q: "BCDEA"[(q - 1) % 5] for q in range(1, 41)},
    "3º Ano": {q: "CDEAB"[(q - 1) % 5] for q in range(1, 41)},
}

def salvar_gabaritos_em_disco(gabaritos_dict):
    with open(ARQUIVO_GABARITOS_JSON, "w", encoding="utf-8") as f: json.dump(gabaritos_dict, f, ensure_ascii=False, indent=2)

def carregar_gabaritos_do_disco():
    if os.path.exists(ARQUIVO_GABARITOS_JSON):
        with open(ARQUIVO_GABARITOS_JSON, "r", encoding="utf-8") as f: dados = json.load(f)
        return {ano: {int(q): str(r) for q, r in gab.items()} for ano, gab in dados.items()}
    return GABARITOS_DEFAULT.copy()

def salvar_historico_em_disco(historico_list):
    with open(ARQUIVO_HISTORICO_JSON, "w", encoding="utf-8") as f: json.dump(historico_list, f, ensure_ascii=False, indent=2)

def carregar_historico_do_disco():
    if os.path.exists(ARQUIVO_HISTORICO_JSON):
        with open(ARQUIVO_HISTORICO_JSON, "r", encoding="utf-8") as f: return json.load(f)
    return []

def carregar_estudantes():
    if os.path.exists(ARQUIVO_ALUNOS_TXT): df = pd.read_csv(ARQUIVO_ALUNOS_TXT)
    else: df = pd.read_csv(io.StringIO(DADOS_ALUNOS_EMBUTIDOS))
    turmas = {}
    for turma, group in df.groupby("Turma", sort=False):
        turmas[str(turma).strip()] = [{"numero": str(int(r["Número"])), "matricula": str(int(r["Matrícula"])), "nome": str(r["Nome"]).strip()} for _, r in group.iterrows()]
    return turmas

def obter_ano_da_turma(turma): return "1º Ano" if "1º" in turma else "2º Ano" if "2º" in turma else "3º Ano"
def obter_disciplina(q):
    for disc, q_range in DISCIPLINAS_MAP.items():
        if q in q_range: return disc
    return "Desconhecida"

# ---------------------------------------------------------
# NOVO MÓDULO: JT PRECISION SCANNER
# ---------------------------------------------------------
def escanear_e_retificar_cartao_jt(img, largura_alvo=1200, altura_alvo=800):
    """
    Módulo para escanear, detectar e posicionar automaticamente o cartão.
    Garante orientação horizontal ideal (1200x800).
    Retorna: img_retificada (horizontal), img_debug (com contorno).
    """
    h_img, w_img = img.shape[:2]
    
    # 1. Pré-processamento Dinâmico
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_enhanced = clahe.apply(gray)
    
    # Binarização adaptativa para encontrar o contorno principal da folha
    gray_blurred = cv2.medianBlur(gray_enhanced, 5)
    thresh = cv2.adaptiveThreshold(gray_blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 11, 2)
    
    # 2. Encontrar o Maior Polígono de 4 Lados
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    
    img_debug = img.copy()
    cartao_contour = None
    
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # Se polígono de 4 lados, é o cartão
        if len(approx) == 4 and cv2.contourArea(c) > (w_img * h_img * 0.1):
            cartao_contour = approx
            cv2.drawContours(img_debug, [approx], -1, (0, 255, 0), 4) # Debug
            break
            
    if cartao_contour is not None:
        # 3. Perspective Warp para Retificação Total
        # Ordenar cantos: Top-Left, Top-Right, Bottom-Right, Bottom-Left
        pts = cartao_contour.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1); rect[0] = pts[np.argmin(s)]; rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1); rect[1] = pts[np.argmin(diff)]; rect[3] = pts[np.argmax(diff)]
        
        # Coordenadas de destino (horizontal fixa)
        pts_dst = np.array([[0, 0], [largura_alvo-1, 0], [largura_alvo-1, altura_alvo-1], [0, altura_alvo-1]], dtype="float32")
        
        # Transformação
        M = cv2.getPerspectiveTransform(rect, pts_dst)
        img_retificada = cv2.warpPerspective(img, M, (largura_alvo, altura_alvo))
        
        # 4. Rotação Automática (se o cartão foi capturado verticalmente)
        h_warped, w_warped = img_retificada.shape[:2]
        if h_warped > w_warped:
            img_retificada = cv2.rotate(img_retificada, cv2.ROTATE_90_CLOCKWISE)
    else:
        # Se não detectar, redimensiona sem retificar (pode causar erros de leitura)
        img_retificada = cv2.resize(img, (largura_alvo, altura_alvo))
        if img_retificada.shape[0] > img_retificada.shape[1]: # se for vertical
             img_retificada = cv2.resize(img_retificada, (largura_alvo, altura_alvo)) # redimensiona direto

    return img_retificada, img_debug

# ---------------------------------------------------------
# MÓDULO OMR ROBUST (Para leitura de bolinhas)
# ---------------------------------------------------------
def ler_respostas_40_questoes(img_warped, gabarito_oficial=None, limiar_preenchimento=35.0):
    """
    Lê a imagem já retificada e posicionada automaticamente pelo módulo Scanner.
    Usa OMR Robust com calibração contextual para alta precisão.
    """
    gray = cv2.cvtColor(img_warped, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_enhanced = clahe.apply(gray)
    
    # Binarização local GAUSSIAN é vital para identificar o sinal de preenchimento
    blurred_local = cv2.GaussianBlur(gray_enhanced, (3, 3), 0)
    thresh_local = cv2.adaptiveThreshold(blurred_local, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV, 15, 5)

    img_annotated = img_warped.copy()
    opcoes = ["A", "B", "C", "D", "E"]
    respostas_aluno = {}

    for q in range(1, 41):
        coords_opts = MAPA_COORDENADAS.get(q, [])
        taxas_preenchimento = []

        for (bx, by) in coords_opts:
            ix, iy = int(round(bx)), int(round(by))
            mask = np.zeros_like(thresh_local, dtype=np.uint8)
            cv2.circle(mask, (ix, iy), 8, 255, -1) # Foco no núcleo da bolinha

            # Cálculo de densidade contextual (Sinal Robust)
            pix_marcados = cv2.countNonZero(cv2.bitwise_and(thresh_local, mask))
            total_pix = cv2.countNonZero(mask)
            
            taxas_preenchimento.append((pix_marcados / float(total_pix)) * 100.0 if total_pix > 0 else 0.0)

        # Decisão Contextual: Maior sinal no grupo da questão
        max_idx = int(np.argmax(taxas_preenchimento)); max_val = taxas_preenchimento[max_idx]
        outras = [t for i, t in enumerate(taxas_preenchimento) if i != max_idx]
        segunda_maior = max(outras) if outras else 0.0

        if max_val >= limiar_preenchimento and (max_val - segunda_maior) >= 12.0: # Margem de contraste
            resp_detectada = opcoes[max_idx]; idx_marcado = max_idx
        else:
            resp_detectada = "Branco/Nulo"; idx_marcado = -1

        respostas_aluno[q] = resp_detectada
        gab_correto = gabarito_oficial.get(q) if gabarito_oficial else None

        # Overlay visual de alta precisão
        for opt_idx, (bx, by) in enumerate(coords_opts):
            ix, iy = int(round(bx)), int(round(by)); opcao_letra = opcoes[opt_idx]
            cv2.circle(img_annotated, (ix, iy), 12, (255, 255, 0), 1) # Guia OMR

            if opt_idx == idx_marcado:
                # Corresponde ao Gabarito Oficial?
                if gab_correto and opcao_letra == gab_correto: cor = (0, 255, 0) # Verde: Acerto
                elif gab_correto and opcao_letra != gab_correto: cor = (0, 0, 255) # Vermelho: Erro
                else: cor = (0, 255, 255) # Amarelo: Sem Gabarito
                cv2.circle(img_annotated, (ix, iy), 10, cor, -1) # Pinta bolinha lida
            elif gab_correto and opcao_letra == gab_correto and resp_detectada != gab_correto:
                # Destaque Azul para a correta omitida
                cv2.circle(img_annotated, (ix, iy), 11, (255, 0, 0), 2)

    return respostas_aluno, img_annotated

# ---------------------------------------------------------
# INTERFACE STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="EREM Joaquim Távora - Corretor OMR", layout="wide", page_icon="📌")
aplicar_estilo_jt()

if "gabaritos_oficiais" not in st.session_state: st.session_state["gabaritos_oficiais"] = carregar_gabaritos_do_disco()
if "historico" not in st.session_state: st.session_state["historico"] = carregar_historico_do_disco()
if "dados_turmas" not in st.session_state: st.session_state["dados_turmas"] = carregar_estudantes()

st.markdown("""
    <div class="jt-header-container">
        <div class="jt-logo-emblem">JT</div>
        <div>
            <div class="jt-header-title">Corretor de Cartão-Resposta OMR</div>
            <div class="jt-header-subtitle">EREM JOAQUIM TÁVORA • SIMULADO TRIMESTRAL</div>
        </div>
    </div>
""", unsafe_allow_html=True)

tab_correcao, tab_gabarito, tab_estudantes, tab_relatorio = st.tabs([
    "📷 Corrigir Prova", "📝 Gabaritos Oficiais", "👥 Estudantes por Turma", "📊 Resultados da Turma"
])

# ---------------------------------------------------------
# ABA 1: CORRIGIR PROVA (Scanner -> Leitura)
# ---------------------------------------------------------
with tab_correcao:
    st.header("Módulo de Escaneamento e Leitura Robust")

    # Passo 1: Captura e Posicionamento Automático
    if "cartao_escanerizado" not in st.session_state:
        st.subheader("1. Escaneamento e Posicionamento Automático")
        img_input = st.camera_input("Posicione o cartão-resposta para escanear")
        
        if img_input:
            img_original = carregar_imagem_com_exif(img_input)
            
            # --- CHAMA O MÓDULO SCANNER ---
            with st.spinner("Scanner JT em ação: Detectando e alinhando o cartão..."):
                img_warped, img_debug = escanear_e_retificar_cartao_jt(img_original)
            
            st.session_state["cartao_escanerizado"] = img_warped
            
            st.divider()
            st.markdown("### 📋 Fluxo do JT Precision Scanner")
            c_debug1, c_debug2 = st.columns(2)
            c_debug1.image(img_debug, channels="BGR", caption="Detecção de Contorno do Cartão JT", use_container_width=True)
            c_debug2.image(img_warped, channels="BGR", caption="Resultado do Posicionamento Automático (Pronto para Leitura)", use_container_width=True)
            
            if st.button("Confirmar e Avançar para Identificação do Aluno", type="primary"):
                 st.rerun()

    # Passo 2: Identificação do Aluno e Leitura OMR
    else:
        st.subheader("2. Identificação do Aluno e Leitura OMR Robust")
        img_warped = st.session_state["cartao_escanerizado"]
        
        col_id, col_img_final = st.columns([1, 2])
        
        with col_id:
            dados_turmas = st.session_state["dados_turmas"]
            turma_selecionada = st.selectbox("Selecione a Turma:", options=list(dados_turmas.keys()), index=0)
            alunos_da_turma = dados_turmas.get(turma_selecionada, [])
            opcoes_alunos = [f"Nº {a['numero']} - {a['nome']}" for a in alunos_da_turma]
            
            if opcoes_alunos:
                aluno_idx = st.selectbox("Selecione o Aluno:", range(len(opcoes_alunos)), format_func=lambda i: opcoes_alunos[i])
                aluno_obj = alunos_da_turma[aluno_idx]; nome_aluno = aluno_obj["nome"]
            else:
                nome_aluno = st.text_input("Nome do Aluno:"); nome_aluno = ""
                
            sensibilidade_omr = st.slider("Sensibilidade OMR (% Mínima de Tinta)", 15.0, 60.0, 35.0, 1.0)
            ano_estudante = obter_ano_da_turma(turma_selecionada)
            
            with st.expander("📄 Ficha do Aluno e Gabarito Ativo", expanded=True):
                 st.markdown(f"**Nome:** {nome_aluno} | **Turma:** {turma_selecionada}")
                 st.info(f"🎯 **Gabarito Ativo:** {ano_estudante}")

            if st.button("💾 Ler Prova e Exibir Resultado", type="primary"):
                # --- CHAMA O MÓDULO OMR ROBUST ---
                gabarito_oficial = st.session_state["gabaritos_oficiais"].get(ano_estudante, {})
                
                respostas_aluno, img_annotated = ler_respostas_40_questoes(
                    img_warped, gabarito_oficial, sensibilidade_omr
                )
                st.session_state["correcao_finalizada"] = (respostas_aluno, img_annotated, nome_aluno, turma_selecionada, ano_estudante)

        # Exibição do Resultado e Histórico
        if "correcao_finalizada" in st.session_state:
            respostas_aluno, img_annotated, nome_aluno, turma_selecionada, ano_estudante = st.session_state["correcao_finalizada"]
            gabarito_oficial = st.session_state["gabaritos_oficiais"].get(ano_estudante, {})
            
            # Análise de Desempenho
            total_acertos = sum(1 for q, r in respostas_aluno.items() if r == gabarito_oficial.get(q))
            nota = (total_acertos / 40.0) * 10.0
            
            with col_img_final:
                st.image(img_annotated, channels="BGR", use_container_width=True)
                st.caption("🟢 Acerto | 🔴 Erro | 🔵 Correta Omitida | 🟡 Ciano: Guia OMR")
                
            st.divider()
            m1, m2, m3 = st.columns(3); m1.metric("Total de Acertos", f"{total_acertos} / 40"); m2.metric("Nota Final", f"{nota:.2f}"); m3.metric("Estudante", nome_aluno)
            
            col_det, col_disc = st.columns(2)
            # Detalhamento por Questão
            detalhes = [{"Questão": q, "Disciplina": obter_disciplina(q), "Resposta Aluno": r, "Gabarito Oficial": gabarito_oficial.get(q), "Resultado": "✅ Acertou" if r == gabarito_oficial.get(q) else "❌ Errou"} for q, r in respostas_aluno.items()]
            col_det.dataframe(pd.DataFrame(detalhes), height=380, use_container_width=True)
            
            # Acertos por Disciplina
            acertos_por_disc = {obtener_disciplina(q): 0 for q in range(1, 41)}
            total_por_disc = {"Filosofia (01-05)": 5, "História (06-10)": 5, "Geografia (11-15)": 5, "Sociologia (16-20)": 5, "Educação Física (21-24)": 4, "Inglês (25-30)": 6, "Português (31-40)": 10}
            for q, r in respostas_aluno.items(): 
                if r == gabarito_oficial.get(q): acertos_por_disc[obter_disciplina(q)] += 1
            col_disc.dataframe(pd.DataFrame([{"Disciplina": d.split(" ")[0], "Acertos": f"{a}/{total_por_disc.get(d)}"} for d, a in acertos_por_disc.items()]), hide_index=True, use_container_width=True)

            c_salv1, c_salv2 = st.columns(2)
            if c_salv1.button("💾 Salvar Resultado no Histórico", type="primary"):
                st.session_state["historico"].append({"Série": ano_estudante, "Turma": turma_selecionada, "Aluno": nome_aluno, "Nota": round(nota, 2)})
                salvar_historico_em_disco(st.session_state["historico"]); st.success("Salvo com sucesso!"); st.rerun()
            if c_salv2.button("🗑️ Cancelar e Escanear Outro", type="secondary"):
                del st.session_state["cartao_escanerizado"]; del st.session_state["correcao_finalizada"]; st.rerun()

# --- ABA 2: GABARITOS OFICIAIS ---
with tab_gabarito:
    st.header("Cadastrar e Gerenciar Gabaritos Oficiais")
    ano_gab_sel = st.selectbox("Selecione o Ano / Série:", ["1º Ano", "2º Ano", "3º Ano"])
    disc_filtro = st.selectbox("Filtrar por Disciplina:", ["Todas"] + list(DISCIPLINAS_MAP.keys()))
    gabarito_ano_atual = st.session_state["gabaritos_oficiais"].get(ano_gab_sel, {})
    questoes_exibidas = range(1, 41) if disc_filtro == "Todas" else DISCIPLINAS_MAP[disc_filtro]
    df_gab_editor = pd.DataFrame([{"Questão": q, "Disciplina": obter_disciplina(q), "Gabarito": gabarito_ano_atual.get(q, "A")} for q in questoes_exibidas])
    df_gab_modificado = st.data_editor(df_gab_editor, column_config={"Gabarito": st.column_config.SelectboxColumn("Resposta", options=["A", "B", "C", "D", "E"], required=True)}, hide_index=True, use_container_width=True)
    if st.button("💾 Salvar Gabarito do " + ano_gab_sel, type="primary"):
        for _, r_g in df_gab_modificado.iterrows(): st.session_state["gabaritos_oficiais"][ano_gab_sel][int(r_g["Questão"])] = str(r_g["Gabarito"])
        salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"]); st.success("Gabarito salvo!")

# --- ABA 3: ESTUDANTES ---
with tab_estudantes:
    st.header("Lista de Estudantes por Turma")
    st.dataframe(pd.DataFrame(st.session_state["dados_turmas"].get(st.selectbox("Visualizar Turma:", list(st.session_state["dados_turmas"].keys())), [])), use_container_width=True)

# --- ABA 4: RELATÓRIO ---
with tab_relatorio:
    st.header("Relatório Geral das Correções")
    if st.session_state["historico"]: st.dataframe(pd.DataFrame(st.session_state["historico"]), use_container_width=True); st.download_button("📥 Baixar Planilha (CSV)", pd.DataFrame(st.session_state["historico"]).to_csv(index=False).encode("utf-8"), "resultados.csv", "text/csv")
    else: st.info("Nenhum cartão corrigido e salvo ainda.")