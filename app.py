import cv2
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# GABARITO OFICIAL PADRÃO DO 3º ANO (52 QUESTÕES DO CSV)
# ---------------------------------------------------------
GABARITO_3ANO_DEFAULT = {
    # Português (1 a 26)
    1: 'B', 2: 'D', 3: 'B', 4: 'A', 5: 'E', 6: 'A', 7: 'B', 8: 'E', 9: 'C', 10: 'E',
    11: 'A', 12: 'C', 13: 'E', 14: 'D', 15: 'A', 16: 'B', 17: 'C', 18: 'B', 19: 'A',
    20: 'B', 21: 'D', 22: 'E', 23: 'D', 24: 'A', 25: 'E', 26: 'D',
    # Matemática (27 a 52)
    27: 'C', 28: 'D', 29: 'C', 30: 'B', 31: 'C', 32: 'E', 33: 'C', 34: 'D', 35: 'C',
    36: 'C', 37: 'D', 38: 'C', 39: 'C', 40: 'E', 41: 'B', 42: 'A', 43: 'B', 44: 'C',
    45: 'A', 46: 'B', 47: 'D', 48: 'D', 49: 'B', 50: 'C', 51: 'E', 52: 'D',
}

# Configuração da Página
st.set_page_config(page_title='Corretor de Simulados - 3º Ano', layout='wide')

# Inicialização de Variáveis na Sessão
if 'gabarito_oficial' not in st.session_state:
    st.session_state['gabarito_oficial'] = GABARITO_3ANO_DEFAULT.copy()

if 'historico' not in st.session_state:
    st.session_state['historico'] = []


def obter_disciplina(q):
    return 'Português' if q <= 26 else 'Matemática'


# ---------------------------------------------------------
# VISÃO COMPUTACIONAL AVANÇADA (OMR POR ANCORAGEM)
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


def retificar_grelha(imagem, largura=1200, altura=600):
    """Localiza os 4 marcadores pretos de canto do cartão e aplica Perspective Warp."""
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold adaptativo para encontrar os quadrados pretos mesmo com sombras
    thresh_adapt = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 21, 10
    )

    cnts, _ = cv2.findContours(thresh_adapt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ancoras = []
    for c in cnts:
        area = cv2.contourArea(c)
        if 100 < area < 8000:
            x, y, w, h = cv2.boundingRect(c)
            aspect = float(w) / h
            extent = area / float(w * h)
            if 0.6 <= aspect <= 1.4 and extent > 0.6:
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    ancoras.append((cx, cy, area))

    if len(ancoras) >= 4:
        # Seleciona os candidatos mais consistentes
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

    # Fallback se a foto estiver muito aproximada/cortada
    return cv2.resize(imagem, (largura, altura))


def ler_respostas_52_questoes(img_warped, gabarito_oficial=None, sensibilidade=10.0):
    """
    Realiza a leitura OMR baseada no contraste relativo de tom de cinza.
    """
    gray = cv2.cvtColor(img_warped, cv2.COLOR_BGR2GRAY)
    img_annotated = img_warped.copy()

    opcoes = ['A', 'B', 'C', 'D', 'E']
    respostas_aluno = {}

    largura_total = 1200
    altura_total = 600
    largura_coluna = largura_total / 4.0

    # Calibração geométrica dos centros das bolhas
    y_top = 32
    y_bot = 582

    for col in range(4):
        col_x_start = col * largura_coluna
        b_start_x = col_x_start + largura_coluna * 0.20
        b_end_x = col_x_start + largura_coluna * 0.90
        b_step = (b_end_x - b_start_x) / 5.0

        for row in range(13):
            num_questao = col * 13 + row + 1
            y_center = y_top + (row + 0.5) * ((y_bot - y_top) / 13.0)

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

            # Avalia a bolha mais escura da linha
            min_idx = int(np.argmin(medias_cinza))
            min_val = medias_cinza[min_idx]

            outras_medias = [m for i, m in enumerate(medias_cinza) if i != min_idx]
            media_outras = np.mean(outras_medias) if outras_medias else 255.0
            diferenca_contraste = media_outras - min_val

            # Se a diferença para as outras for maior que o limiar de sensibilidade
            if diferenca_contraste >= sensibilidade:
                resp_detectada = opcoes[min_idx]
                idx_marcado = min_idx
            else:
                resp_detectada = 'Branco/Nulo'
                idx_marcado = -1

            respostas_aluno[num_questao] = resp_detectada

            # Desenho das marcações visuais (Overlay OMR)
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
                    # Desenha círculo azul na resposta correta quando o aluno errou ou deixou em branco
                    cv2.circle(img_annotated, (bx, by), 10, (255, 0, 0), 2)

    return respostas_aluno, img_annotated


# ---------------------------------------------------------
# INTERFACE DO USUÁRIO STREAMLIT
# ---------------------------------------------------------
st.title('📌 Corretor de Simulado - 3º Ano (52 Questões)')

tab_gabarito, tab_correcao, tab_relatorio = st.tabs([
    '📝 Gabarito Oficial (3º Ano)',
    '📷 Corrigir Prova',
    '📊 Resultados da Turma',
])

# ---------------------------------------------------------
# ABA 1: GABARITO OFICIAL
# ---------------------------------------------------------
with tab_gabarito:
    st.header('Gabarito Oficial - Prova do 3º Ano')
    st.caption('Q01 - Q26: Português | Q27 - Q52: Matemática')

    col_df, col_actions = st.columns([2, 1])

    with col_actions:
        st.subheader('Ações Rápidas')
        if st.button('🔄 Restaurar Gabarito Padrão (Planilha Enviada)'):
            st.session_state['gabarito_oficial'] = GABARITO_3ANO_DEFAULT.copy()
            st.success('Gabarito padrão do 3º ano restaurado!')
            st.rerun()

        st.divider()
        st.subheader('Importar Outro Gabarito')
        arquivo = st.file_uploader(
            'Upload de CSV ou XLSX (52 questões)', type=['csv', 'xlsx']
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
                        zip(df_up['Questão'][:52], df_up['Gabarito'][:52])
                    )
                    st.session_state['gabarito_oficial'].update(nuevo_gab)
                    st.success('Gabarito atualizado!')
                    st.rerun()
                else:
                    st.error("O arquivo precisa ter colunas 'Questão' e 'Gabarito'.")
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
            for q in range(1, 53)
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
        nome_aluno = st.text_input('Nome do Aluno:', placeholder='Ex: Maria Souza')
        turma = st.text_input('Turma:', value='3º Ano A')

        st.divider()
        st.subheader('Ajustes da Leitura')
        sensibilidade_omr = st.slider(
            'Sensibilidade da Caneta (OMR)',
            min_value=3.0,
            max_value=25.0,
            value=8.0,
            step=0.5,
            help='Diminua se o aluno usou caneta fraca ou lápis; aumente se houver reflexos/sombras.'
        )

        st.info('📌 Português: Q01 a Q26\n📌 Matemática: Q27 a Q52')

    with col_cam:
        origem = st.radio("Fonte da Imagem:", ["Câmera", "Enviar Arquivo (Upload)"], horizontal=True)
        img_input = None

        if origem == "Câmera":
            foto = st.camera_input('Posicione a folha de 52 questões na tela')
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

            # 1. Ajustar Perspectiva usando os 4 marcadores de canto
            img_warped = retificar_grelha(img)

            # 2. Ler Respostas e gerar visualização
            gabarito = st.session_state['gabarito_oficial']
            respostas_aluno, img_annotated = ler_respostas_52_questoes(
                img_warped, gabarito, sensibilidade=sensibilidade_omr
            )

            acertos_port = 0
            acertos_mat = 0
            detalhes = []

            for q in range(1, 53):
                resp = respostas_aluno.get(q, 'Branco/Nulo')
                gab = gabarito.get(q, '-')
                correto = (resp == gab)
                disc = obter_disciplina(q)

                if correto:
                    if disc == 'Português':
                        acertos_port += 1
                    else:
                        acertos_mat += 1

                detalhes.append({
                    'Questão': q,
                    'Disciplina': disc,
                    'Resposta Aluno': resp,
                    'Gabarito': gab,
                    'Status': '✅ Acertou' if correto else '❌ Errou',
                })

            total_acertos = acertos_port + acertos_mat
            nota = (total_acertos / 52.0) * 10.0

            st.divider()

            # Indicadores de Desempenho
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Português', f'{acertos_port} / 26')
            c2.metric('Matemática', f'{acertos_mat} / 26')
            c3.metric('Total Acertos', f'{total_acertos} / 52')
            c4.metric('Nota Final', f'{nota:.2f} / 10.0')

            if st.button('💾 Salvar Resultado no Histórico', type='primary'):
                st.session_state['historico'].append({
                    'Aluno': nome_aluno,
                    'Turma': turma,
                    'Português (26)': acertos_port,
                    'Matemática (26)': acertos_mat,
                    'Total Acertos (52)': total_acertos,
                    'Nota Final': round(nota, 2),
                })
                st.success(f'Resultado de {nome_aluno} salvo com sucesso!')

            col_img, col_det = st.columns(2)
            with col_img:
                st.subheader('Imagem Processada (Visualização OMR)')
                st.image(img_annotated, channels='BGR', use_container_width=True)
                st.caption("🟢 Círculo Verde = Acerto | 🔴 Círculo Vermelho = Erro | 🔵 Círculo Azul = Gabarito Correto")

            with col_det:
                st.subheader('Detalhamento')
                st.dataframe(
                    pd.DataFrame(detalhes), height=350, use_container_width=True
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
            file_name='resultados_3ano_simulado.csv',
            mime='text/csv',
        )

        if st.button('🗑️ Limpar Histórico'):
            st.session_state['historico'] = []
            st.rerun()