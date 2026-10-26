import io
import json
import os
import re
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

# Estrutura de disciplinas do 1º e 2º Dia de Simulado
DISCIPLINAS_MAP_DIA1 = {
    "Filosofia (01-05)": range(1, 6),
    "História (06-10)": range(6, 11),
    "Geografia (11-15)": range(11, 16),
    "Sociologia (16-20)": range(16, 21),
    "Educação Física (21-24)": range(21, 25),
    "Inglês (25-30)": range(25, 31),
    "Português (31-40)": range(31, 41),
}

DISCIPLINAS_MAP_DIA2 = {
    "Biologia (01-05)": range(1, 6),
    "Química (06-10)": range(6, 11),
    "Física (11-15)": range(11, 16),
    "Matemática (16-25)": range(16, 26),
    "Arte (26-30)": range(26, 31),
}

DISCIPLINAS_POR_DIA = {
    "1º Dia": DISCIPLINAS_MAP_DIA1,
    "2º Dia": DISCIPLINAS_MAP_DIA2
}

ALUNOS_3D_DEFAULT = [
    {"numero": "1", "matricula": "0", "nome": "ALICE LEON CAMARGO MARTINS DIAS"},
    {"numero": "2", "matricula": "0", "nome": "AMANDA MARIA DA CRUZ COSTA"},
    {"numero": "3", "matricula": "0", "nome": "ANA BEATRIZ LEAL DE PAULA"},
    {"numero": "4", "matricula": "0", "nome": "ANA CLARA LOPES DA SILVA"},
    {"numero": "5", "matricula": "0", "nome": "ANA LARISSA SILVA MARINHO DE CARVALHO"},
    {"numero": "6", "matricula": "0", "nome": "CARLOS VICTOR SANTOS SOUZA GRAMOSA"},
    {"numero": "7", "matricula": "0", "nome": "CAUA JOSE DOS SANTOS"},
    {"numero": "8", "matricula": "0", "nome": "EDUARDA VITORIA DA SILVA DE ALBUQUERQUE"},
    {"numero": "9", "matricula": "0", "nome": "GABRIEL TAVERAS GOMES"},
    {"numero": "10", "matricula": "0", "nome": "HICARO VINICIUS FELICIANO DOS SANTOS"},
    {"numero": "11", "matricula": "0", "nome": "HILDA DANIELLY DA SILVA PEREIRA"},
    {"numero": "12", "matricula": "0", "nome": "ISADORA VALENÇA CORDEIRO DOS SANTOS"},
    {"numero": "13", "matricula": "0", "nome": "JENYPHER SAMARA BERNARDO DA SILVA"},
    {"numero": "14", "matricula": "0", "nome": "JESSICA CRISTINA FERREIRA BARBOZA"},
    {"numero": "15", "matricula": "0", "nome": "JHONATAS CARLOS CAVALCANTE LOPES DE LIMA"},
    {"numero": "16", "matricula": "0", "nome": "JULYA SANTOS ALVES BARROS"},
    {"numero": "17", "matricula": "0", "nome": "KAUANNY LETICIA BARROS QUEIROZ DA SILVA"},
    {"numero": "18", "matricula": "0", "nome": "KAYLANY MARIA SANTANA DE ALMEIDA"},
    {"numero": "19", "matricula": "0", "nome": "LARIANNY DA SILVA OLIVEIRA"},
    {"numero": "20", "matricula": "0", "nome": "MARIA CAROLINA MOURA DE MENEZES FONSECA"},
    {"numero": "21", "matricula": "0", "nome": "MARIA DA CONCEICAO DOS SANTOS GOMES"},
    {"numero": "22", "matricula": "0", "nome": "MARIA HELOISA DA SILVA DO CARMO"},
    {"numero": "23", "matricula": "0", "nome": "MARIA LUIZA LIMA TEIXEIRA"},
    {"numero": "24", "matricula": "0", "nome": "MARIA VITORIA PEREIRA DO NASCIMENTO"},
    {"numero": "25", "matricula": "0", "nome": "NICHOLAS YURI SILVA DE ARAUJO"},
    {"numero": "26", "matricula": "0", "nome": "PAULO VICTOR LIRA CARNEIRO"},
    {"numero": "27", "matricula": "0", "nome": "RAKELLY MARIA DE OLIVEIRA"},
    {"numero": "28", "matricula": "0", "nome": "REBECA GABRIELLY MENDES DA CUNHA"},
    {"numero": "29", "matricula": "0", "nome": "SAMANTHA MARIA DE AZEVEDO SILVA"},
    {"numero": "30", "matricula": "0", "nome": "SAMUELL ANDERSSON SOUZA DA SILVA"},
    {"numero": "31", "matricula": "0", "nome": "TAISA BARBOSA GUSMÃO"},
    {"numero": "32", "matricula": "0", "nome": "THAUAN LOURENCO DA SILVA"},
    {"numero": "33", "matricula": "0", "nome": "VITORIA GABRIELA DA SILVA"},
    {"numero": "34", "matricula": "0", "nome": "PAULO VINICIUS DE AGUIAR BATISTA"},
    {"numero": "35", "matricula": "0", "nome": "GABRYEL ELIAS DIAS MELO"}
]

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
    "1º Ano - 1º Dia": {q: "ABCDE"[(q - 1) % 5] for q in range(1, 41)},
    "2º Ano - 1º Dia": {q: "BCDEA"[(q - 1) % 5] for q in range(1, 41)},
    "3º Ano - 1º Dia": {q: "CDEAB"[(q - 1) % 5] for q in range(1, 41)},
    "1º Ano - 2º Dia": {q: "ABCDE"[(q - 1) % 5] for q in range(1, 31)},
    "2º Ano - 2º Dia": {q: "BCDEA"[(q - 1) % 5] for q in range(1, 31)},
    "3º Ano - 2º Dia": {q: "CDEAB"[(q - 1) % 5] for q in range(1, 31)},
}

def salvar_gabaritos_em_disco(gabaritos_dict):
    with open(ARQUIVO_GABARITOS_JSON, "w", encoding="utf-8") as f:
        json.dump(gabaritos_dict, f, ensure_ascii=False, indent=2)

def carregar_gabaritos_do_disco():
    if os.path.exists(ARQUIVO_GABARITOS_JSON):
        try:
            with open(ARQUIVO_GABARITOS_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            gabaritos_tratados = {}
            for chave, gab in dados.items():
                if " - " not in chave:
                    nova_chave = f"{chave} - 1º Dia"
                else:
                    nova_chave = chave
                gabaritos_tratados[nova_chave] = {int(q): str(r) for q, r in gab.items()}
            
            for k, v in GABARITOS_DEFAULT.items():
                if k not in gabaritos_tratados:
                    gabaritos_tratados[k] = v.copy()
            return gabaritos_tratados
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
                dados = json.load(f)
                for h in dados:
                    if "Dia" not in h:
                        h["Dia"] = "1º Dia"
                return dados
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
    
    if "3º D" not in turmas and "3D" not in turmas:
        turmas["3º D"] = ALUNOS_3D_DEFAULT

    return turmas

def obter_ano_da_turma(turma):
    return "1º Ano" if "1º" in turma else "2º Ano" if "2º" in turma else "3º Ano"

def obter_disciplina(q, dia="1º Dia"):
    disc_map = DISCIPLINAS_POR_DIA.get(dia, DISCIPLINAS_MAP_DIA1)
    for disc, q_range in disc_map.items():
        if q in q_range:
            return disc
    return "Desconhecida"

# ---------------------------------------------------------
# MÓDULO VISUAL GEMINI COM RESPOSTA ESTRUTURADA EM JSON
# ---------------------------------------------------------
def extrair_respostas_com_gemini(pil_image, api_key, dia="1º Dia"):
    genai.configure(api_key=api_key)

    modelos_disponiveis = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nome_limpo = m.name.replace('models/', '')
                modelos_disponiveis.append(nome_limpo)
    except Exception:
        pass

    preferidos = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest"
    ]

    candidatos = []
    for p in preferidos:
        if p not in candidatos:
            candidatos.append(p)
    for d in modelos_disponiveis:
        if d not in candidatos:
            candidatos.append(d)

    if dia == "2º Dia":
        desc_disciplinas = "disciplinas do 2º Dia (Biologia 01-05, Química 06-10, Física 11-15, Matemática 16-25, Arte 26-30)"
        qtd_questoes = 30
    else:
        desc_disciplinas = "disciplinas do 1º Dia (Filosofia 01-05, História 06-10, Geografia 11-15, Sociologia 16-20, Educação Física 21-24, Inglês 25-30, Português 31-40)"
        qtd_questoes = 40

    prompt = f"""
    Você é um sistema especialista em Leitura Óptica de Cartão-Resposta (OMR).
    Analise esta imagem do 'CARTÃO-RESPOSTA - Simulado Trimestral' e extraia a opção preenchida/marcada pelo estudante para cada uma das {qtd_questoes} questões.

    Instruções de Análise:
    - O cartão contém {qtd_questoes} questões numeradas de 01 a {qtd_questoes} divididas nas {desc_disciplinas}.
    - Para cada questão de 1 a {qtd_questoes}, identifique qual das opções (A, B, C, D ou E) está pintada/preenchida.
    - Se uma questão não tiver nenhuma bolinha pintada ou apresentar múltiplas marcas/rasuras, defina o valor como "Branco/Nulo".

    Formato de Saída OBRIGATÓRIO:
    Retorne ESTRITAMENTE um objeto JSON válido onde as chaves sejam as questões como strings de "1" a "{qtd_questoes}" e os valores sejam a letra maiúscula correspondente ("A", "B", "C", "D", "E" ou "Branco/Nulo"). Não adicione nenhuma explicação, introdução ou raciocínio.

    Exemplo de formato:
    {{
      "1": "B",
      "2": "C",
      "3": "A",
      ...
      "{qtd_questoes}": "D"
    }}
    """

    response = None
    ultimo_erro = None

    for nome_modelo in candidatos:
        try:
            model = genai.GenerativeModel(nome_modelo)
            response = model.generate_content(
                [pil_image, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            break
        except Exception:
            try:
                model = genai.GenerativeModel(nome_modelo)
                response = model.generate_content([pil_image, prompt])
                break
            except Exception as e:
                ultimo_erro = e
                continue

    if response is None:
        raise ValueError(f"Não foi possível conectar a nenhum modelo do Gemini. Detalhes: {ultimo_erro}")

    raw_text = response.text.strip()

    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    json_str = match.group(0) if match else raw_text

    try:
        json_data = json.loads(json_str)
        respostas_aluno = {int(k): str(v).upper() for k, v in json_data.items()}
        return respostas_aluno
    except Exception as e:
        raise ValueError(f"Erro ao interpretar resposta do Gemini: {e}\nTexto bruto recebido:\n{raw_text}")

# ---------------------------------------------------------
# INTERFACE PRINCIPAL STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="EREM Joaquim Távora - Corretor OMR Gemini", layout="wide", page_icon="📌")
aplicar_estilo_jt()

st.session_state["dados_turmas"] = carregar_estudantes()

if "gabaritos_oficiais" not in st.session_state:
    st.session_state["gabaritos_oficiais"] = carregar_gabaritos_do_disco()
if "historico" not in st.session_state:
    st.session_state["historico"] = carregar_historico_do_disco()

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

tab_correcao, tab_manual, tab_gabarito, tab_estudantes, tab_relatorio = st.tabs([
    "📷 Corrigir Prova com IA", "✍️ Lançamento Manual", "📝 Gabaritos Oficiais", "👥 Estudantes por Turma", "📊 Resultados da Turma"
])

# ---------------------------------------------------------
# ABA 1: CORRIGIR PROVA VIA GEMINI
# ---------------------------------------------------------
with tab_correcao:
    st.header("Captura da Foto e Extração Inteligente de Respostas")

    col_info, col_cam = st.columns([1, 2])

    with col_info:
        st.subheader("1. Identificação do Estudante")
        
        dia_selecionado = st.selectbox("Selecione o Dia do Simulado:", options=["1º Dia", "2º Dia"], index=0)
        
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

        chave_gabarito_ativa = f"{ano_estudante} - {dia_selecionado}"

        with st.expander("📄 Ficha do Aluno e Gabarito Ativo", expanded=True):
            st.markdown(f"**Nome:** {nome_aluno}")
            st.markdown(f"**Turma:** {turma_selecionada} | **Nº Chamada:** {num_aluno if num_aluno else 'N/A'}")
            st.info(f"🎯 **Gabarito Vinculado:** {chave_gabarito_ativa}")

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
                    with st.spinner(f"🤖 O Gemini está analisando as respostas do {dia_selecionado}..."):
                        try:
                            respostas_aluno = extrair_respostas_com_gemini(pil_image, gemini_key, dia_selecionado)
                            st.session_state["respostas_extraidas"] = (respostas_aluno, nome_aluno, turma_selecionada, ano_estudante, num_aluno, mat_aluno, dia_selecionado)
                            st.success("Extração visual concluída com sucesso!")
                        except Exception as err:
                            st.error(f"Erro ao processar imagem com o Gemini: {err}")

    if "respostas_extraidas" in st.session_state:
        respostas_aluno, nome_aluno, turma_selecionada, ano_estudante, num_aluno, mat_aluno, dia_sel = st.session_state["respostas_extraidas"]
        
        chave_gab = f"{ano_estudante} - {dia_sel}"
        gabarito_oficial = st.session_state["gabaritos_oficiais"].get(chave_gab, {})

        detalhes = []
        total_acertos = 0
        
        disc_map = DISCIPLINAS_POR_DIA[dia_sel]
        acertos_por_disc = {disc: 0 for disc in disc_map.keys()}

        max_q = 30 if dia_sel == "2º Dia" else 40

        for q in range(1, max_q + 1):
            resp = respostas_aluno.get(q, "Branco/Nulo")
            gab = gabarito_oficial.get(q, "-")
            correto = (resp == gab)
            disc = obter_disciplina(q, dia_sel)

            if correto:
                total_acertos += 1
                if disc in acertos_por_disc:
                    acertos_por_disc[disc] += 1

            detalhes.append({
                "Questão": q,
                "Disciplina": disc,
                "Resposta do Aluno (Gemini)": resp,
                "Gabarito Oficial": gab,
                "Status": "✅ Acertou" if correto else "❌ Errou",
            })

        nota = (total_acertos / float(max_q)) * 10.0

        st.divider()
        st.subheader(f"🎯 Resultado da Avaliação - {dia_sel}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Acertos", f"{total_acertos} / {max_q}")
        m2.metric("Nota Final", f"{nota:.2f} / 10.0")
        m3.metric("Estudante / Turma", f"{nome_aluno} ({turma_selecionada})")

        cols_disc = st.columns(len(acertos_por_disc))
        for i, (d_nome, d_acertos) in enumerate(acertos_por_disc.items()):
            max_q_disc = len(disc_map[d_nome])
            cols_disc[i].metric(d_nome.split(" ")[0], f"{d_acertos}/{max_q_disc}")

        c_salvar, c_cancelar = st.columns(2)
        if c_salvar.button("💾 Salvar Resultado no Histórico", type="primary"):
            registro = {
                "Dia": dia_sel,
                "Série": ano_estudante,
                "Turma": turma_selecionada,
                "Nº": num_aluno,
                "Matrícula": mat_aluno,
                "Aluno": nome_aluno,
                "Total Acertos": total_acertos,
                "Nota Final": round(nota, 2)
            }
            for d_nome, d_acertos in acertos_por_disc.items():
                max_q_disc = len(disc_map[d_nome])
                registro[d_nome.split(" ")[0]] = f"{d_acertos}/{max_q_disc}"

            st.session_state["historico"].append(registro)
            salvar_historico_em_disco(st.session_state["historico"])
            st.success(f"Resultado de {nome_aluno} ({dia_sel}) salvo com sucesso!")

        if c_cancelar.button("🗑️ Limpar Resultado"):
            del st.session_state["respostas_extraidas"]
            st.rerun()

        st.subheader("📋 Tabela Comparativa Detalhada")
        st.dataframe(pd.DataFrame(detalhes), height=400, use_container_width=True)

# ---------------------------------------------------------
# ABA 2: LANÇAMENTO MANUAL DE NOTAS
# ---------------------------------------------------------
with tab_manual:
    st.header("✍️ Lançamento Manual de Nota")
    st.markdown("Utilize esta opção para lançar notas de cartões corrigidos manualmente ou fora da aplicação.")

    col_m_aluno, col_m_nota = st.columns([1, 1])

    with col_m_aluno:
        st.subheader("1. Identificação do Estudante")
        
        dia_man = st.selectbox("Selecione o Dia do Simulado:", options=["1º Dia", "2º Dia"], key="dia_man_sel")
        dados_turmas = st.session_state["dados_turmas"]
        lista_turmas = list(dados_turmas.keys())

        turma_man = st.selectbox("Selecione a Turma:", options=lista_turmas, key="turma_man")
        ano_estudante_man = obter_ano_da_turma(turma_man)
        alunos_man = dados_turmas.get(turma_man, [])

        opcoes_alunos_man = [f"Nº {a['numero']} - {a['nome']}" if a["numero"] else a["nome"] for a in alunos_man]

        if opcoes_alunos_man:
            aluno_idx_man = st.selectbox("Selecione o Aluno:", range(len(opcoes_alunos_man)), format_func=lambda i: opcoes_alunos_man[i], key="aluno_man")
            aluno_obj_man = alunos_man[aluno_idx_man]
            nome_m, num_m, mat_m = aluno_obj_man["nome"], aluno_obj_man["numero"], aluno_obj_man["matricula"]
        else:
            nome_m = st.text_input("Nome do Aluno:", key="nome_m_custom")
            num_m, mat_m = "", ""

        with st.expander("📄 Ficha do Aluno", expanded=True):
            st.markdown(f"**Nome:** {nome_m}")
            st.markdown(f"**Turma:** {turma_man} | **Nº Chamada:** {num_m if num_m else 'N/A'}")
            st.info(f"🎯 **Série e Dia:** {ano_estudante_man} - {dia_man}")

    with col_m_nota:
        st.subheader("2. Lançamento da Nota")
        
        tipo_entrada = st.radio("Modo de Entrada:", ["Total de Acertos", "Nota Final Direta (0 a 10)"], horizontal=True)

        max_q_man = 30 if dia_man == "2º Dia" else 40

        if tipo_entrada == "Total de Acertos":
            acertos_m = st.number_input(f"Total de Acertos (0 a {max_q_man}):", min_value=0, max_value=max_q_man, value=max_q_man//2, step=1)
            nota_m = (acertos_m / float(max_q_man)) * 10.0
            st.metric("Nota Calculada", f"{nota_m:.2f} / 10.0")
        else:
            nota_m = st.number_input("Nota Final (0.0 a 10.0):", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
            acertos_m = int(round((nota_m / 10.0) * max_q_man))
            st.metric("Acertos Estimados", f"{acertos_m} / {max_q_man}")

        st.divider()
        com_detalhamento = st.checkbox("Deseja informar o acerto específico por disciplina?")

        acertos_disc_man = {}
        if com_detalhamento:
            st.caption(f"Informe os acertos por matéria do **{dia_man}**:")
            c_d1, c_d2 = st.columns(2)
            
            if dia_man == "1º Dia":
                acertos_disc_man["Filosofia"] = c_d1.number_input("Filosofia (máx 5):", 0, 5, 0)
                acertos_disc_man["História"] = c_d1.number_input("História (máx 5):", 0, 5, 0)
                acertos_disc_man["Geografia"] = c_d1.number_input("Geografia (máx 5):", 0, 5, 0)
                acertos_disc_man["Sociologia"] = c_d1.number_input("Sociologia (máx 5):", 0, 5, 0)
                
                acertos_disc_man["Educação"] = c_d2.number_input("Educação Física (máx 4):", 0, 4, 0)
                acertos_disc_man["Inglês"] = c_d2.number_input("Inglês (máx 6):", 0, 6, 0)
                acertos_disc_man["Português"] = c_d2.number_input("Português (máx 10):", 0, 10, 0)
            else:
                acertos_disc_man["Biologia"] = c_d1.number_input("Biologia (máx 5):", 0, 5, 0)
                acertos_disc_man["Química"] = c_d1.number_input("Química (máx 5):", 0, 5, 0)
                acertos_disc_man["Física"] = c_d1.number_input("Física (máx 5):", 0, 5, 0)
                
                acertos_disc_man["Matemática"] = c_d2.number_input("Matemática (máx 10):", 0, 10, 0)
                acertos_disc_man["Arte"] = c_d2.number_input("Arte (máx 5):", 0, 5, 0)

            soma_acertos = sum(acertos_disc_man.values())
            st.info(f"Soma dos acertos inseridos: **{soma_acertos} / {max_q_man}**")
            acertos_m = soma_acertos
            nota_m = (acertos_m / float(max_q_man)) * 10.0

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Salvar Nota Manual no Histórico", type="primary", use_container_width=True):
            if not nome_m:
                st.warning("⚠️ Selecione ou informe o nome do aluno.")
            else:
                registro_m = {
                    "Dia": dia_man,
                    "Série": ano_estudante_man,
                    "Turma": turma_man,
                    "Nº": num_m,
                    "Matrícula": mat_m,
                    "Aluno": nome_m,
                    "Total Acertos": acertos_m,
                    "Nota Final": round(nota_m, 2)
                }

                if com_detalhamento:
                    for k_d, v_d in acertos_disc_man.items():
                        max_d = 5
                        if k_d == "Matemática" or k_d == "Português": max_d = 10
                        elif k_d == "Educação": max_d = 4
                        elif k_d == "Inglês": max_d = 6
                        registro_m[k_d] = f"{v_d}/{max_d}"

                st.session_state["historico"].append(registro_m)
                salvar_historico_em_disco(st.session_state["historico"])
                st.success(f"✅ Nota do estudante **{nome_m}** ({dia_man}) salva com sucesso!")

# ---------------------------------------------------------
# ABA 3: GABARITOS OFICIAIS
# ---------------------------------------------------------
with tab_gabarito:
    st.header("Cadastrar e Gerenciar Gabaritos Oficiais")
    
    col_g1, col_g2 = st.columns(2)
    dia_gab_sel = col_g1.selectbox("Selecione o Dia:", ["1º Dia", "2º Dia"])
    ano_gab_sel = col_g2.selectbox("Selecione o Ano / Série:", ["1º Ano", "2º Ano", "3º Ano"])
    
    chave_gab_sel = f"{ano_gab_sel} - {dia_gab_sel}"
    disc_map_sel = DISCIPLINAS_POR_DIA[dia_gab_sel]
    
    disc_filtro = st.selectbox("Filtrar por Disciplina:", ["Todas as Disciplinas"] + list(disc_map_sel.keys()))

    gabarito_ano_atual = st.session_state["gabaritos_oficiais"].get(chave_gab_sel, {})
    
    if disc_filtro == "Todas as Disciplinas":
        questoes_exibidas = range(1, 31) if dia_gab_sel == "2º Dia" else range(1, 41)
    else:
        questoes_exibidas = disc_map_sel[disc_filtro]

    df_gab_editor = pd.DataFrame([
        {"Questão": q, "Disciplina": obter_disciplina(q, dia_gab_sel), "Gabarito Oficial": gabarito_ano_atual.get(q, "A")}
        for q in questoes_exibidas
    ])

    df_gab_modificado = st.data_editor(
        df_gab_editor,
        column_config={"Gabarito Oficial": st.column_config.SelectboxColumn("Resposta Correta", options=["A", "B", "C", "D", "E"], required=True)},
        hide_index=True, use_container_width=True
    )

    if st.button(f"💾 Salvar Gabarito do {chave_gab_sel}", type="primary"):
        if chave_gab_sel not in st.session_state["gabaritos_oficiais"]:
            st.session_state["gabaritos_oficiais"][chave_gab_sel] = {}
            
        for _, row_g in df_gab_modificado.iterrows():
            st.session_state["gabaritos_oficiais"][chave_gab_sel][int(row_g["Questão"])] = str(row_g["Gabarito Oficial"])
            
        salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"])
        st.success(f"Gabarito do **{chave_gab_sel}** salvo com sucesso!")

# ---------------------------------------------------------
# ABA 4: ESTUDANTES
# ---------------------------------------------------------
with tab_estudantes:
    st.header("Lista de Estudantes Cadastrados por Turma")
    turmas_map = st.session_state["dados_turmas"]
    t_sel = st.selectbox("Visualizar Turma:", list(turmas_map.keys()))
    st.dataframe(pd.DataFrame(turmas_map.get(t_sel, [])), use_container_width=True)

# ---------------------------------------------------------
# ABA 5: RELATÓRIO
# ---------------------------------------------------------
with tab_relatorio:
    st.header("Relatório Geral das Correções")
    if st.session_state["historico"]:
        df_h = pd.DataFrame(st.session_state["historico"])
        st.dataframe(df_h, use_container_width=True)
        st.download_button("📥 Baixar Planilha de Notas (CSV)", df_h.to_csv(index=False).encode("utf-8"), "resultados.csv", "text/csv")
    else:
        st.info("Nenhum cartão corrigido e salvo ainda.")
