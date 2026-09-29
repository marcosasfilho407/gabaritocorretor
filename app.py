import cv2
import numpy as np

def ordenar_pontos(pts):
    """
    Ordena os 4 cantos: Top-Left, Top-Right, Bottom-Right, Bottom-Left
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # Top-Left
    rect[2] = pts[np.argmax(s)] # Bottom-Right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # Top-Right
    rect[3] = pts[np.argmax(diff)] # Bottom-Left
    return rect

def alinhamento_ancoras(image):
    """
    Detecta os 4 marcadores pretos nos cantos e aplica Perspective Warp.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Encontrar contornos dos marcadores de canto
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ancoras = []

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        # Filtra por contornos quadriláteros com área mínima
        if len(approx) == 4 and cv2.contourArea(c) > 500:
            x, y, w, h = cv2.boundingRect(approx)
            ar = w / float(h)
            if 0.8 <= ar <= 1.2:  # Proporção próxima a um quadrado
                M = cv2.moments(c)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                ancoras.append([cX, cY])

    if len(ancoras) < 4:
        raise ValueError("Não foi possível localizar os 4 marcadores de ancoragem.")

    # Ordena os pontos encontrados
    pts_origem = ordenar_pontos(np.array(ancoras[:4], dtype="float32"))

    # Dimensões padronizadas para a imagem corrigida
    largura_std, altura_std = 1000, 1400
    pts_destino = np.array([
        [0, 0],
        [largura_std - 1, 0],
        [largura_std - 1, altura_std - 1],
        [0, altura_std - 1]
    ], dtype="float32")

    # Matriz de transformação
    M = cv2.getPerspectiveTransform(pts_origem, pts_destino)
    warped = cv2.warpPerspective(image, M, (largura_std, altura_std))
    
    return warped

def MapearEstruturaCaderno(warped):
    """
    Mapeia os blocos de questões do caderno retificado.
    """
    gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    thresh_warped = cv2.threshold(gray_warped, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Configuração da Estrutura
    NUM_COLUNAS = 4
    QUESTOES_POR_COLUNA = 13
    TOTAL_QUESTOES = 52
    OPCOES = ['A', 'B', 'C', 'D', 'E']

    # As coordenadas relativas da grade dentro da imagem de 1000x1400
    # Estes valores de ROI devem ser ajustados conforme a proporção real do layout retificado
    
    # Exemplo de extração por amostragem em grade:
    # Coluna X, Linha Y, Opção Z podem ser iteradas diretamente via deslocamento fixo.
    
    respostas_detectadas = {}

    # Exemplo estrutural de varredura
    for col in range(NUM_COLUNAS):
        for q in range(QUESTOES_POR_COLUNA):
            num_questao = col * QUESTOES_POR_COLUNA + q + 1
            respostas_detectadas[num_questao] = []

            for opt_idx, opcao in enumerate(OPCOES):
                # Cálculo dos centros e áreas de interesse (ROI) de cada bolha
                # cx, cy representam o centro da bolha (A, B, C, D, E)
                # Aplicar cv2.countNonZero no ROI para medir o preenchimento.
                pass

    return thresh_warped