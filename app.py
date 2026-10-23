import io
import json
import os
import base64
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps
import google.generativeai as genai

# ---------------------------------------------------------
# CONSTANTES E CONFIGURAÇÕES DE PERSISTÊNCIA
# ---------------------------------------------------------
ARQUIVO_GABARITOS_JSON = "gabaritos_oficiais.json"
ARQUIVO_HISTORICO_JSON = "historico_correcoes.json"
ARQUIVO_ALUNOS_TXT = "todososalunosporturma.txt"

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
# FUNÇÕES DE PERSISTÊNCIA E DADOS
# ---------------------------------------------------------
def obter_imagem_fundo_base64():
    candidatos = ["background.jpg", "background.png", "input_file_8.png"]
    for c in candidatos:
        if os.path.exists(c):
            try:
                with open(c, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except Exception:
                pass
    return None

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
    with open(ARQUIVO_GABARITOS_JSON, "w", encoding="utf-8") as f:
        json.dump(gabaritos_dict, f, ensure_ascii=False, indent=2)

def carregar_gabaritos_do_disco():
    if os.path.exists(ARQUIVO_GABARITOS_JSON):
        try:
            with open(ARQUIVO_GABARITOS_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return {ano: {int(q): str(r) for q, r in gab.items()} for ano, gab in dados.items()}
        except Exception:
            pass
    return GABARITOS_DEFAULT.copy()

def salvar_historico_em_disco(historico_list):
    with open(ARQUIVO_HISTORICO_JSON, "w", encoding="utf-8") as f:
        json.dump(historico_list, f, ensure_ascii=False, indent=2)

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
        turmas[str(turma).strip()] = [
            {"numero": str(int(r["Número"])) if pd.notna(r.get("Número")) else "",
             "matricula": str(int(r["Matrícula"])) if pd.notna(r.get("Matrícula")) else "",
             "nome": str(r["Nome"]).strip()}
            for _, r in group.iterrows()
        ]
    return turmas

def obter_ano_da_turma(turma):
    return "1º Ano" if "1º" in turma else "2º Ano" if "2º" in turma else "3º Ano"

def obter_disciplina(q):
    for disc, q_range in DISCIPLINAS_MAP.items():
        if q in q_range:
            return disc
    return "Desconhecida"

# ---------------------------------------------------------
# MÓDULO VISUAL GEMINI PARA EXTRAÇÃO DE RESPOSTAS
# ---------------------------------------------------------
def extrair_respostas_com_gemini(pil_image, api_key):
    """
    Envia a foto do cartão de respostas para a API do Gemini Vision
    e retorna um dicionário Python {1: 'A', 2: 'B', ..., 40: 'D'}.
    """
    genai.configure(api_key=api_key)
    
    # Utiliza o modelo multimodal Gemini
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = """
    Você é um sistema especialista em Leitura Óptica de Cartão-Resposta (OMR).
    Analise esta imagem do 'CARTÃO-RESPOSTA - Simulado Trimestral' e extraia a opção preenchida/marcada pelo estudante para cada uma das 40 questões.

    Instruções de Análise:
    - O cartão contém 40 questões numeradas de 01 a 40 divididas em disciplinas (Filosofia 01-05, História 06-10, Geografia 11-15, Sociologia 16-20, Educação Física 21-24, Inglês 25-30, Português 31-40).
    - Para cada questão de 1 a 40, identifique qual das opções (A, B, C, D ou E) está pintada/preenchida.
    - Se uma questão não tiver nenhuma bolinha pintada ou apresentar múltiplas marcas/rasuras, defina o valor como "Branco/Nulo".

    Formato de Saída OBRIGATÓRIO:
    Retorne ESTRITAMENTE um objeto JSON válido onde as chaves sejam as questões como strings de "1" a "40" e os valores sejam a letra maiúscula correspondente ("A", "B", "C", "D", "E" ou "Branco/Nulo"). Não adicione marcações markdown nem explicações.

    Exemplo do formato esperado:
    {
      "1": "B",
      "2": "C",
      "3": "A",
      ...
      "40": "D"
    }
    """

    response = model.generate_content([pil_image, prompt])
    raw_text = response.text.strip()
    
    # Limpeza de formato Markdown no JSON caso a API devolva ```json ... ```
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    try:
        json_data = json.loads(raw_text)
        respostas_aluno = {int(k): str(v).upper() for k, v in json_data.items()}
        return respostas_aluno
    except Exception as e:
        raise ValueError(f"Erro ao interpretar resposta do Gemini: {e}\nTexto bruto recebido: {raw_text}")

# ---------------------------------------------------------
# INTERFACE PRINCIPAL STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="EREM Joaquim Távora - Corretor OMR Gemini", layout="wide", page_icon="📌")
aplicar_estilo_jt()

if "gabaritos_oficiais" not in st.session_state:
    st.session_state["gabaritos_oficiais"] = carregar_gabaritos_do_disco()
if "historico" not in st.session_state:
    st.session_state["historico"] = carregar_historico_do_disco()
if "dados_turmas" not in st.session_state:
    st.session_state["dados_turmas"] = carregar_estudantes()

# Barra Lateral - Configuração da Chave da API
with st.sidebar:
    st.subheader("🔑 Configuração Gemini")
    gemini_key = st.text_input("Cole sua Gemini API Key:", type="password", help="Obtenha uma chave em aistudio.google.com")
    if not gemini_key and "GEMINI_API_KEY" in os.environ:
        gemini_key = os.environ["GEMINI_API_KEY"]

st.markdown("""
    <div class="jt-header-container">
        <div class="jt-logo-emblem">JT</div>
        <div>
            <div class="jt-header-title">Corretor OMR com Visão Computacional Gemini</div>
            <div class="jt-header-subtitle">EREM JOAQUIM TÁVORA • SIMULADO TRIMESTRAL</div>
        </div>
    </div>
""", unsafe_allow_html=True)

tab_correcao, tab_gabarito, tab_estudantes, tab_relatorio = st.tabs([
    "📷 Corrigir Prova com Gemini", "📝 Gabaritos Oficiais", "👥 Estudantes por Turma", "📊 Resultados da Turma"
])

# ---------------------------------------------------------
# ABA 1: CORRIGIR PROVA VIA GEMINI
# ---------------------------------------------------------
with tab_correcao:
    st.header("Captura da Foto e Extração Inteligente de Respostas")

    col_info, col_cam = st.columns([1, 2])

    with col_info:
        st.subheader("1. Identificação do Estudante")
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

        with st.expander("📄 Ficha do Aluno e Gabarito Ativo", expanded=True):
            st.markdown(f"**Nome:** {nome_aluno}")
            st.markdown(f"**Turma:** {turma_selecionada} | **Nº Chamada:** {num_aluno if num_aluno else 'N/A'}")
            st.info(f"🎯 **Gabarito Oficial Vinculado:** {ano_estudante}")

    with col_cam:
        st.subheader("2. Foto do Cartão-Resposta")
        origem = st.radio("Fonte da Imagem:", ["Câmera", "Enviar Arquivo (Upload)"], horizontal=True)

        file_input = None
        if origem == "Câmera":
            file_input = st.camera_input("Fotografe o cartão-resposta")
        else:
            file_input = st.file_uploader("Upload do Cartão-Resposta", type=["png", "jpg", "jpeg"])

        if file_input:
            pil_image = Image.open(file_input)
            pil_image = ImageOps.exif_transpose(pil_image)
            st.image(pil_image, caption="Imagem Carregada para Processamento", use_container_width=True)

            if st.button("🚀 Processar Cartão com Gemini IA", type="primary"):
                if not gemini_key:
                    st.error("⚠️ Insira sua Gemini API Key na barra lateral para prosseguir.")
                elif not nome_aluno:
                    st.warning("⚠️ Selecione ou informe o nome do aluno.")
                else:
                    with st.spinner("🤖 O Gemini está analisando a imagem e extraindo as respostas..."):
                        try:
                            respostas_aluno = extrair_respostas_com_gemini(pil_image, gemini_key)
                            st.session_state["respostas_extraidas"] = (respostas_aluno, nome_aluno, turma_selecionada, ano_estudante, num_aluno, mat_aluno)
                            st.success("Extração visual concluída com sucesso!")
                        except Exception as err:
                            st.error(f"Erro ao processar imagem com o Gemini: {err}")

    # Exibição dos Resultados da Correção
    if "respostas_extraidas" in st.session_state:
        respostas_aluno, nome_aluno, turma_selecionada, ano_estudante, num_aluno, mat_aluno = st.session_state["respostas_extraidas"]
        gabarito_oficial = st.session_state["gabaritos_oficiais"].get(ano_estudante, {})

        # Comparação das respostas lidas com o gabarito oficial
        detalhes = []
        total_acertos = 0
        total_por_disc = {
            "Filosofia (01-05)": 5, "História (06-10)": 5, "Geografia (11-15)": 5,
            "Sociologia (16-20)": 5, "Educação Física (21-24)": 4,
            "Inglês (25-30)": 6, "Português (31-40)": 10
        }
        acertos_por_disc = {disc: 0 for disc in total_por_disc.keys()}

        for q in range(1, 41):
            resp = respostas_aluno.get(q, "Branco/Nulo")
            gab = gabarito_oficial.get(q, "-")
            correto = (resp == gab)
            disc = obter_disciplina(q)

            if correto:
                total_acertos += 1
                acertos_por_disc[disc] += 1

            detalhes.append({
                "Questão": q,
                "Disciplina": disc,
                "Resposta do Aluno (Gemini)": resp,
                "Gabarito Oficial": gab,
                "Status": "✅ Acertou" if correto else "❌ Errou",
            })

        nota = (total_acertos / 40.0) * 10.0

        st.divider()
        st.subheader("🎯 Resultado da Avaliação")

        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Acertos", f"{total_acertos} / 40")
        m2.metric("Nota Final", f"{nota:.2f} / 10.0")
        m3.metric("Estudante / Turma", f"{nome_aluno} ({turma_selecionada})")

        # Exibição de desempenho por disciplina
        cols_disc = st.columns(len(acertos_por_disc))
        for i, (d_nome, d_acertos) in enumerate(acertos_por_disc.items()):
            cols_disc[i].metric(d_nome.split(" ")[0], f"{d_acertos}/{total_por_disc.get(d_nome, 5)}")

        c_salvar, c_cancelar = st.columns(2)
        if c_salvar.button("💾 Salvar Resultado no Histórico", type="primary"):
            registro = {
                "Série": ano_estudante, "Turma": turma_selecionada, "Nº": num_aluno,
                "Matrícula": mat_aluno, "Aluno": nome_aluno, "Total Acertos": total_acertos,
                "Nota Final": round(nota, 2)
            }
            for d_nome, d_acertos in acertos_por_disc.items():
                registro[d_nome.split(" ")[0]] = f"{d_acertos}/{total_por_disc.get(d_nome, 5)}"

            st.session_state["historico"].append(registro)
            salvar_historico_em_disco(st.session_state["historico"])
            st.success(f"Resultado de {nome_aluno} salvo com sucesso!")

        if c_cancelar.button("🗑️ Limpar Resultado"):
            del st.session_state["respostas_extraidas"]
            st.rerun()

        st.subheader("📋 Tabela Comparativa Detalhada")
        st.dataframe(pd.DataFrame(detalhes), height=400, use_container_width=True)

# ---------------------------------------------------------
# ABA 2: GABARITOS OFICIAIS
# ---------------------------------------------------------
with tab_gabarito:
    st.header("Cadastrar e Gerenciar Gabaritos Oficiais")
    ano_gab_sel = st.selectbox("Selecione o Ano / Série:", ["1º Ano", "2º Ano", "3º Ano"])
    disc_filtro = st.selectbox("Filtrar por Disciplina:", ["Todas as Disciplinas"] + list(DISCIPLINAS_MAP.keys()))

    gabarito_ano_atual = st.session_state["gabaritos_oficiais"].get(ano_gab_sel, {})
    questoes_exibidas = range(1, 41) if disc_filtro == "Todas as Disciplinas" else DISCIPLINAS_MAP[disc_filtro]

    df_gab_editor = pd.DataFrame([
        {"Questão": q, "Disciplina": obter_disciplina(q), "Gabarito Oficial": gabarito_ano_atual.get(q, "A")}
        for q in questoes_exibidas
    ])

    df_gab_modificado = st.data_editor(
        df_gab_editor,
        column_config={"Gabarito Oficial": st.column_config.SelectboxColumn("Resposta Correta", options=["A", "B", "C", "D", "E"], required=True)},
        hide_index=True, use_container_width=True
    )

    if st.button("💾 Salvar Gabarito do " + ano_gab_sel, type="primary"):
        for _, row_g in df_gab_modificado.iterrows():
            st.session_state["gabaritos_oficiais"][ano_gab_sel][int(row_g["Questão"])] = str(row_g["Gabarito Oficial"])
        salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"])
        st.success(f"Gabarito do {ano_gab_sel} salvo com sucesso!")

# ---------------------------------------------------------
# ABA 3: ESTUDANTES
# ---------------------------------------------------------
with tab_estudantes:
    st.header("Lista de Estudantes Cadastrados por Turma")
    turmas_map = st.session_state["dados_turmas"]
    t_sel = st.selectbox("Visualizar Turma:", list(turmas_map.keys()))
    st.dataframe(pd.DataFrame(turmas_map.get(t_sel, [])), use_container_width=True)

# ---------------------------------------------------------
# ABA 4: RELATÓRIO
# ---------------------------------------------------------
with tab_relatorio:
    st.header("Relatório Geral das Correções")
    if st.session_state["historico"]:
        df_h = pd.DataFrame(st.session_state["historico"])
        st.dataframe(df_h, use_container_width=True)
        st.download_button("📥 Baixar Planilha de Notas (CSV)", df_h.to_csv(index=False).encode("utf-8"), "resultados.csv", "text/csv")
    else:
        st.info("Nenhum cartão corrigido e salvo ainda.")
