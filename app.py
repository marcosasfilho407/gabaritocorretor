import cv2
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# GABARITO OFICIAL PADRÃO (40 QUESTÕES POR DISCIPLINA)
# ---------------------------------------------------------
GABARITO_SIMULADO_DEFAULT = {
    # Filosofia (01 a 05)
    1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E',
    # História (06 a 10)
    6: 'A', 7: 'B', 8: 'C', 9: 'D', 10: 'E',
    # Geografia (11 a 15)
    11: 'A', 12: 'B', 13: 'C', 14: 'D', 15: 'E',
    # Sociologia (16 a 20)
    16: 'A', 17: 'B', 18: 'C', 19: 'D', 20: 'E',
    # Educação Física (21 a 24)
    21: 'A', 22: 'B', 23: 'C', 24: 'D',
    # Inglês (25 a 30)
    25: 'A', 26: 'B', 27: 'C', 28: 'D', 29: 'E', 30: 'A',
    # Português (31 a 40)
    31: 'A', 32: 'B', 33: 'C', 34: 'D', 35: 'E', 36: 'A', 37: 'B', 38: 'C', 39: 'D', 40: 'E',
}

# Configuração da Página
st.set_page_config(page_title='Corretor de Simulado Trimestral', layout='wide')

# Inicialização de Variáveis na Sessão
if 'gabarito_oficial' not in st.session_state:
    st.session_state['gabarito_oficial'] = GABARITO_SIMULADO_DEFAULT.copy()

if 'historico' not in st.session_state:
    st.session_state['historico'] = []


def obter_disciplina(q):
    if 1 <= q <= 5:
        return 'Filosofia (01-05)'
    elif 6 <= q <= 10:
        return 'História (06-10)'
    elif 11 <= q <= 15:
        return 'Geografia (11-15)'
    elif 16 <= q <= 20:
        return 'Sociologia (16-20)'
    elif 21 <= q <= 24:
        return 'Educação Física (21-24)'
    elif 25 <= q <= 30:
        return 'Inglês (25-30)'
    elif 31 <= q <= 40:
        return 'Português (31-40)'
    return 'Desconhecida'


# ---------------------------------------------------------
# VISÃO COMPUTACIONAL (OMR POR ANCORAGEM E BLOCOS)
# ---------------------------------------------------------
def ordenar_pontos(pts):
    rect = np.zeros((4, 2), dtype='float32')
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]       # Superior Esquerdo (TL)
    rect[2] = pts[np.argmax(s)]       # Inferior Direito (BR)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]    # Superior Direito (TR)
    rect[3] = pts[np.argmax(diff)]    # Inferior Esquerdo (BL)
    return rect


def retificar_grelha(imagem, largura=1200, altura=800):
    """Localiza os 4 marcadores pretos de canto do cartão e aplica Perspective Warp."""
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh_adapt = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 21, 10
    )

    cnts, _ = cv2.findContours(thresh_adapt, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    ancoras = []
    for c in cnts:
        area = cv2.contourArea(c)
        if 80 < area < 8000:
            x, y, w, h = cv2.boundingRect(c)
            aspect = float(w) / h
            extent = area / float(w * h)
            if 0.65 <= aspect <= 1.35 and extent > 0.6:
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    ancoras.append((cx, cy, area))

    if len(ancoras) >= 4:
        ancoras = sorted(ancoras, key=lambda p: p[2], reverse=True)[:12]
        pts_cand = np.array([[p[0], p[1]] for p in ancoras], dtype="float32")

        pts_origem = ordenar_pontos(pts_cand)
        pts_destino = np.array([
            [0, 0],
            [largura - 1, 0],
            [largura - 1, altura - 1],
            [0, altura - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(pts_origem, pts_destino)
        return cv2.warpPerspective(imagem, M, (largura, altura))

    return cv2.resize(imagem, (largura, altura))


def ler_respostas_40_questoes(img_warped, gabarito_oficial=None, sensibilidade=10.0):
    """
    Processa os blocos específicos das 7 disciplinas no layout retificado (1200x800).
    """
    gray = cv2.cvtColor(img_warped, cv2.COLOR_BGR2GRAY)
    img_annotated = img_warped.copy()

    opcoes = ['A', 'B', 'C', 'D', 'E']
    respostas_aluno = {}

    largura_total = 1200
    altura_total = 800

    # Definição dos blocos de disciplinas (Coordenadas relativas)
    # [num_inicio, num_fim, col_idx (0..3), y_inicio_norm, y_fim_norm]
    blocos = [
        (1, 5, 0, 0.28, 0.54),    # Filosofia (Q01 - Q05)
        (6, 10, 0, 0.62, 0.94),   # História (Q06 - Q10)
        (11, 15, 1, 0.28, 0.54),  # Geografia (Q11 - Q15)
        (16, 20, 1, 0.62, 0.94),  # Sociologia (Q16 - Q20)
        (21, 24, 2, 0.28, 0.49),  # Educação Física (Q21 - Q24)
        (25, 30, 2, 0.58, 0.94),  # Inglês (Q25 - Q30)
        (31, 40, 3, 0.28, 0.94),  # Português (Q31 - Q40)
    ]

    for q_start, q_end, col_idx, y_start_ratio, y_end_ratio in blocos:
        num_questoes_bloco = q_end - q_start + 1
        col_x_start = col_idx * (largura_total / 4.0)
        col_w = largura_total / 4.0

        b_start_x = col_x_start + col_w * 0.24
        b_end_x = col_x_start + col_w * 0.92
        b_step = (b_end_x - b_start_x) / 5.0

        y_top_bloco = altura_total * y_start_ratio
        y_bot_bloco = altura_total * y_end_ratio

        for row in range(num_questoes_bloco):
            num_questao = q_start + row
            y_center = y_top_bloco + (row + 0.5) * ((y_bot_bloco - y_top_bloco) / float(num_questoes_bloco))

            medias_cinza = []
            coords_opcoes = []

            for opt_idx in range(5):
                bx = b_start_x + (opt_idx + 0.5) * b_step
                by = y_center

                r = 10
                x1, x2 = int(bx - r), int(bx + r)
                y1, y2 = int(by - r), int(by + r)

                roi = gray[max(0, y1):min(altura_total, y2), max(0, x1):min(largura_total, x2)]
                media_tom = float(np.mean(roi)) if roi.size > 0 else 255.0

                medias_cinza.append(media_tom)
                coords_opcoes.append((int(bx), int(by)))

            min_idx = int(np.argmin(medias_cinza))
            min_val = medias_cinza[min_idx]

            outras_medias = [m for i, m in enumerate(medias_cinza) if i != min_idx]
            media_outras = np.mean(outras_medias) if outras_medias else 255.0
            diferenca = media_outras - min_val

            if diferenca >= sensibilidade:
                resp_detectada = opcoes[min_idx]
                idx_marcado = min_idx
            else:
                resp_detectada = 'Branco/Nulo'
                idx_marcado = -1

            respostas_aluno[num_questao] = resp_detectada

            gab_correto = gabarito_oficial.get(num_questao) if gabarito_oficial else None

            for opt_idx, (bx, by) in enumerate(coords_opcoes):
                opcao_letra = opcoes[opt_idx]

                if opt_idx == idx_marcado:
                    if gab_correto and opcao_letra == gab_correto:
                        cor = (0, 255, 0)     # Verde: Acerto
                    elif gab_correto and opcao_letra != gab_correto:
                        cor = (0, 0, 255)     # Vermelho: Erro
                    else:
                        cor = (0, 255, 255)   # Amarelo
                    cv2.circle(img_annotated, (bx, by), 10, cor, -1)
                elif gab_correto and opcao_letra == gab_correto and resp_detectada != gab_correto:
                    cv2.circle(img_annotated, (bx, by), 10, (255, 0, 0), 2)

    return respostas_aluno, img_annotated


# ---------------------------------------------------------
# INTERFACE DO USUÁRIO (STREAMLIT)
# ---------------------------------------------------------
st.title('📌 Corretor de Cartão-Resposta - Simulado Trimestral (40 Questões)')

tab_gabarito, tab_correcao, tab_relatorio = st.tabs([
    '📝 Gabarito Oficial',
    '📷 Corrigir Prova',
    '📊 Resultados da Turma',
])

# ---------------------------------------------------------
# ABA 1: GABARITO OFICIAL
# ---------------------------------------------------------
with tab_gabarito:
    st.header('Cadastrar Gabarito Oficial')
    st.caption('Filosofia (01-05) | História (06-10) | Geografia (11-15) | Sociologia (16-20) | Ed. Física (21-24) | Inglês (25-30) | Português (31-40)')

    col_df, col_actions = st.columns([2, 1])

    with col_actions:
        st.subheader('Ações Rápidas')
        if st.button('🔄 Restaurar Gabarito Padrão'):
            st.session_state['gabarito_oficial'] = GABARITO_SIMULADO_DEFAULT.copy()
            st.success('Gabarito padrão restaurado!')
            st.rerun()

        st.divider()
        st.subheader('Importar via Arquivo')
        arquivo = st.file_uploader(
            'Upload de CSV ou XLSX (40 questões)', type=['csv', 'xlsx']
        )
        if arquivo:
            try:
                df_up = (
                    pd.read_csv(arquivo)
                    if arquivo.name.endswith('.csv')
                    else pd.read_excel(arquivo)
                )
                if 'Questão' in df_up.columns and 'Gabarito' in df_up.columns:
                    nuevo_gab = dict(
                        zip(df_up['Questão'][:40], df_up['Gabarito'][:40])
                    )
                    st.session_state['gabarito_oficial'].update(nuevo_gab)
                    st.success('Gabarito atualizado!')
                    st.rerun()
                else:
                    st.error("O arquivo precisa ter as colunas 'Questão' e 'Gabarito'.")
            except Exception as e:
                st.error(f'Erro ao carregar arquivo: {e}')

    with col_df:
        st.subheader('Tabela do Gabarito')
        df_gab = pd.DataFrame([
            {
                'Questão': q,
                'Disciplina': obter_disciplina(q),
                'Gabarito': st.session_state['gabarito_oficial'].get(q, 'A'),
            }
            for q in range(1, 41)
        ])

        df_editado = st.data_editor(
            df_gab,
            column_config={
                'Questão': st.column_config.NumberColumn('Questão', disabled=True),
                'Disciplina': st.column_config.TextColumn(
                    'Disciplina', disabled=True
                ),
                'Gabarito': st.column_config.SelectboxColumn(
                    'Resposta Correta',
                    options=['A', 'B', 'C', 'D', 'E'],
                    required=True,
                ),
            },
            hide_index=True,
            height=500,
            use_container_width=True,
        )

        if st.button('💾 Salvar Alterações na Tabela', type='primary'):
            st.session_state['gabarito_oficial'] = dict(
                zip(df_editado['Questão'], df_editado['Gabarito'])
            )
            st.success('Gabarito salvo com sucesso!')

# ---------------------------------------------------------
# ABA 2: CORRIGIR PROVA
# ---------------------------------------------------------
with tab_correcao:
    st.header('Captura ou Upload do Cartão de Respostas')

    col_info, col_cam = st.columns([1, 2])

    with col_info:
        st.subheader('Identificação')
        nome_aluno = st.text_input('Nome do Aluno:', placeholder='Ex: Carlos Eduardo')
        serie = st.selectbox('Série:', ['1º Ano', '2º Ano', '3º Ano'], index=2)
        turma = st.selectbox('Turma:', ['A', 'B', 'C', 'D'], index=0)

        st.divider()
        st.subheader('Ajustes da Leitura')
        sensibilidade_omr = st.slider(
            'Sensibilidade OMR (Contraste)',
            min_value=3.0,
            max_value=25.0,
            value=8.0,
            step=0.5,
            help='Reduza se o aluno usou caneta fraca/lápis; aumente se houver sombras fortes.'
        )

    with col_cam:
        origem = st.radio("Fonte da Imagem:", ["Câmera", "Enviar Arquivo (Upload)"], horizontal=True)
        img_input = None

        if origem == "Câmera":
            foto = st.camera_input('Posicione o cartão de respostas de 40 questões na tela')
            if foto:
                img_input = foto
        else:
            upload_img = st.file_uploader('Envie uma foto do cartão de respostas', type=['png', 'jpg', 'jpeg'])
            if upload_img:
                img_input = upload_img

    if img_input:
        if not nome_aluno:
            st.warning('⚠️ Por favor, informe o nome do aluno antes de prosseguir.')
        else:
            file_bytes = np.asarray(bytearray(img_input.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # 1. Retificar Perspectiva
            img_warped = retificar_grelha(img)

            # 2. Ler Respostas (40 questões)
            gabarito = st.session_state['gabarito_oficial']
            respostas_aluno, img_annotated = ler_respostas_40_questoes(
                img_warped, gabarito, sensibilidade=sensibilidade_omr
            )

            # Contagem por disciplina
            acertos_por_disc = {}
            total_por_disc = {
                'Filosofia (01-05)': 5, 'História (06-10)': 5, 'Geografia (11-15)': 5,
                'Sociologia (16-20)': 5, 'Educação Física (21-24)': 4,
                'Inglês (25-30)': 6, 'Português (31-40)': 10
            }

            detalhes = []
            total_acertos = 0

            for q in range(1, 41):
                resp = respostas_aluno.get(q, 'Branco/Nulo')
                gab = gabarito.get(q, '-')
                correto = (resp == gab)
                disc = obter_disciplina(q)

                if disc not in acertos_por_disc:
                    acertos_por_disc[disc] = 0

                if correto:
                    acertos_por_disc[disc] += 1
                    total_acertos += 1

                detalhes.append({
                    'Questão': q,
                    'Disciplina': disc,
                    'Resposta Aluno': resp,
                    'Gabarito': gab,
                    'Status': '✅ Acertou' if correto else '❌ Errou',
                })

            nota = (total_acertos / 40.0) * 10.0

            st.divider()
            st.subheader('Resumo do Desempenho')

            # Métrica Geral
            m1, m2, m3 = st.columns(3)
            m1.metric('Total de Acertos', f'{total_acertos} / 40')
            m2.metric('Nota Final', f'{nota:.2f} / 10.0')
            m3.metric('Série / Turma', f'{serie} - {turma}')

            # Métricas por Disciplina
            cols_disc = st.columns(len(acertos_por_disc))
            for i, (d_nome, d_acertos) in enumerate(acertos_por_disc.items()):
                tot = total_por_disc.get(d_nome, 5)
                cols_disc[i].metric(d_nome.split(' ')[0], f'{d_acertos}/{tot}')

            if st.button('💾 Salvar Resultado no Histórico', type='primary'):
                registro = {
                    'Aluno': nome_aluno,
                    'Série': serie,
                    'Turma': turma,
                    'Total Acertos': total_acertos,
                    'Nota Final': round(nota, 2),
                }
                for d_nome, d_acertos in acertos_por_disc.items():
                    registro[d_nome.split(' ')[0]] = f"{d_acertos}/{total_por_disc.get(d_nome, 5)}"

                st.session_state['historico'].append(registro)
                st.success(f'Resultado de {nome_aluno} salvo com sucesso!')

            col_img, col_det = st.columns(2)
            with col_img:
                st.subheader('Imagem Processada (Overlay OMR)')
                st.image(img_annotated, channels='BGR', use_container_width=True)
                st.caption("🟢 Verde = Acerto | 🔴 Vermelho = Erro | 🔵 Azul = Gabarito Correto")

            with col_det:
                st.subheader('Detalhamento por Questão')
                st.dataframe(
                    pd.DataFrame(detalhes), height=380, use_container_width=True
                )

# ---------------------------------------------------------
# ABA 3: RESULTADOS DA TURMA
# ---------------------------------------------------------
with tab_relatorio:
    st.header('Relatório Geral da Turma')

    if len(st.session_state['historico']) == 0:
        st.info('Nenhum cartão foi corrigido e salvo ainda.')
    else:
        df_hist = pd.DataFrame(st.session_state['historico'])
        st.dataframe(df_hist, use_container_width=True)

        csv = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='📥 Baixar Planilha de Notas (CSV)',
            data=csv,
            file_name='resultados_simulado_trimestral.csv',
            mime='text/csv',
        )

        if st.button('🗑️ Limpar Histórico'):
            st.session_state['historico'] = []
            st.rerun()