import cv2
import numpy as np
import matplotlib.pyplot as plt

def detect_bubbles(image_path):
    """
    Detecta as bolhas candidatas em um cartão-resposta.
    O foco é filtrar contornos para encontrar apenas as bolhas.
    """
    # 1. Pré-processamento: Gray, Blur, Adaptive Threshold
    img = cv2.imread(image_path)
    if img is None:
        return None, None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Binarização adaptativa é crucial para lidar com iluminação desigual
    # Adicionar um desfoque mediano ajuda a reduzir ruído de pequenos pontos
    gray_blur = cv2.medianBlur(gray, 5)
    binary = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY_INV, 11, 2)
    
    # 2. Encontrar contornos
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bubble_contours = []
    
    # 3. Filtragem Robust para encontrar bolhas candidatas
    for cnt in contours:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / h
        
        # Parâmetros de filtragem:
        # a. Área: deve estar em um intervalo razoável (ajustar conforme o cartão)
        # b. Proporção (perpendicularidade): bolhas são círculos, então w/h ~ 1.0
        if 100 < area < 5000 and 0.8 < aspect_ratio < 1.2:
            bubble_contours.append(cnt)
            
    # Criar uma imagem apenas com as bolhas candidatas para depuração
    # marked_bubbles_img = img.copy()
    # cv2.drawContours(marked_bubbles_img, bubble_contours, -1, (0, 0, 255), 2)
    # cv2.imwrite('candidatas.png', marked_bubbles_img)
            
    return img, bubble_contours

def identify_marked_bubbles_robust(img, bubble_contours, prefill_percent_threshold=50, darken_third_threshold=0.33):
    """
    Identifica quais bolhas candidatas foram marcadas com mais precisão.
    Usa preenchimento estatístico baseado em histograma para robustez.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    marked_indices = []
    marked_coords = []
    
    # 1. Binarização adaptativa para limpeza de fundo (ruído, sombras)
    # Isso ajuda a isolar a bolha, mas não é usado para contar preenchimento
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY_INV, 11, 2)
    
    for i, cnt in enumerate(bubble_contours):
        x, y, w, h = cv2.boundingRect(cnt)
        
        # 2. Criar máscara para a bolha exata
        mask = np.zeros(binary.shape, dtype="uint8")
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        
        # 3. Calcular preenchimento estatístico baseado em histograma (Robust)
        # Não apenas contar pixels. Calcular a porcentagem de pixels no terço *mais escuro*
        # (região perto de 0 no histograma).
        
        # Isolar a bolha usando a máscara na imagem em tons de cinza original
        # (antes da binarização adaptativa, mas talvez após limpeza básica, se houver)
        masked_bubble = cv2.bitwise_and(gray, gray, mask=mask)
        
        # Calcular o histograma da região mascarada
        hist = cv2.calcHist([masked_bubble], [0], mask, [256], [0, 256])
        
        # Calcular o número total de pixels na bolha
        total_pixels_in_bubble = cv2.countNonZero(mask)
        if total_pixels_in_bubble == 0:
            continue
            
        # Calcular a porcentagem de preenchimento na região escura (0 a 255/3 ~ 85)
        # Uma bolha marcada terá um pico claro nessa região.
        # Uma bolha em branco terá um pico claro na região clara (perto de 255).
        # A distância e forma dos picos são mais precisas do que apenas a contagem.
        num_pixels_dark = np.sum(hist[:int(256 * darken_third_threshold)])
        marked_prefill_percent = (num_pixels_dark / float(total_pixels_in_bubble)) * 100
        
        # Aplicar limiar estatístico sobre a porcentagem de preenchimento
        if marked_prefill_percent > prefill_percent_threshold:
            marked_indices.append(i)
            marked_coords.append((x, y, w, h))
            
    # Criar uma imagem com as bolhas marcadas identificadas
    result_img = img.copy()
    for (x, y, w, h) in marked_coords:
        cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    # cv2.drawContours(result_img, [bubble_contours[i] for i in marked_indices], -1, (0, 255, 0), 2)
            
    return marked_indices, marked_coords, result_img

def main(image_path, prefill_percent_threshold=50):
    img, bubble_contours = detect_bubbles(image_path)
    
    if img is not None and bubble_contours is not None:
        print(f"Número de bolhas candidatas encontradas: {len(bubble_contours)}")
        
        marked_indices, marked_coords, result_img = identify_marked_bubbles_robust(
            img, bubble_contours, prefill_percent_threshold
        )
        
        print(f"Número de bolhas marcadas identificadas: {len(marked_indices)}")
        
        # Exibir a imagem de resultado com bolhas marcadas
        plt.figure(figsize=(10, 8))
        plt.imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
        plt.title(f'Result - Marked: {len(marked_indices)}')
        plt.axis('off')
        plt.show()
        
        # Salvar a imagem de resultado
        cv2.imwrite('resultado_precisao_robusta.png', result_img)
        print("Imagem de resultado salva como 'resultado_precisao_robusta.png'")
        
    else:
        print(f"Não foi possível ler a imagem: {image_path}")

# --- Exemplo de uso ---
# Certifique-se de ter uma imagem 'cartao.png' no mesmo diretório
image_path = 'image_19.png'  # Substitua pelo caminho da sua imagem
main(image_path, prefill_percent_threshold=50) # Ajuste o threshold conforme necessário