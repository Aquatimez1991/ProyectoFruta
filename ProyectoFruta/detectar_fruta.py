#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector inteligente de frutas con identificación de tipo y detección de malogrado.

Funcionalidades:
1. Identificación del tipo de fruta (manzana, plátano, naranja, etc.)
2. Detección de productos que NO son frutas
3. Análisis de estado (malogrado/OK) con puntaje y visualización
4. Alertas cuando se detecta un objeto que no es una fruta
5. Sistema de conteo y estadísticas de detección
6. Almacenamiento organizado para entrenamiento de IA

Modo 1 (heurístico, por defecto):
- Captura una imagen con la tecla 'c'.
- Identifica el tipo de fruta usando análisis de color y forma
- Analiza si está malograda con reglas de color/contraste/textura
- Alerta si el objeto no es una fruta
- Cuenta y registra estadísticas de detección

Modo 2 (modelo opcional ONNX):
- Si existe un archivo 'model.onnx' en el mismo directorio, se intentará usarlo.
- Debe ser un modelo de clasificación de imágenes con salida binaria:
  índice 0 = OK / índice 1 = MALOGRADA (o similar); adaptar si difiere.
- Se hace un preprocesado básico (224x224, [0,1]) que puedes ajustar.

Requisitos:
pip install opencv-python numpy onnxruntime (opcional para modo ONNX)

Ejecución:
python detectar_fruta.py --camera 0 --save
Presiona 'c' para capturar, 'q' para salir, 's' para mostrar estadísticas.

Autor: ChatGPT (GPT-5 Thinking)
"""
import os
import sys
import argparse
import time
import json
from dataclasses import dataclass
from datetime import datetime

import cv2
import numpy as np

# Intentar importar onnxruntime si el usuario tiene un modelo
try:
    import onnxruntime as ort
    HAS_ORT = True
except Exception:
    HAS_ORT = False

@dataclass
class DetectionStats:
    """Clase para manejar estadísticas de detección"""
    total_detections: int = 0
    total_fruits: int = 0
    total_non_fruits: int = 0
    fruits_by_type: dict = None
    fruits_by_status: dict = None
    detection_history: list = None
    
    def __post_init__(self):
        if self.fruits_by_type is None:
            self.fruits_by_type = {}
        if self.fruits_by_status is None:
            self.fruits_by_status = {'OK': 0, 'MALOGRADA': 0}
        if self.detection_history is None:
            self.detection_history = []
    
    def add_detection(self, is_fruit: bool, fruit_type: str = None, status: str = None, confidence: float = 0.0, score: float = 0.0):
        """Añade una nueva detección a las estadísticas"""
        self.total_detections += 1
        
        detection_record = {
            'timestamp': datetime.now().isoformat(),
            'is_fruit': is_fruit,
            'fruit_type': fruit_type,
            'status': status,
            'confidence': confidence,
            'score': score
        }
        self.detection_history.append(detection_record)
        
        if is_fruit:
            self.total_fruits += 1
            
            # Contar por tipo de fruta
            if fruit_type:
                if fruit_type not in self.fruits_by_type:
                    self.fruits_by_type[fruit_type] = {'total': 0, 'OK': 0, 'MALOGRADA': 0}
                self.fruits_by_type[fruit_type]['total'] += 1
                
                # Contar por estado
                if status:
                    self.fruits_by_type[fruit_type][status] += 1
                    self.fruits_by_status[status] += 1
        else:
            self.total_non_fruits += 1
    
    def get_summary(self):
        """Retorna un resumen de las estadísticas"""
        return {
            'total_detections': self.total_detections,
            'total_fruits': self.total_fruits,
            'total_non_fruits': self.total_non_fruits,
            'fruits_by_type': self.fruits_by_type,
            'fruits_by_status': self.fruits_by_status,
            'success_rate': self.total_fruits / max(self.total_detections, 1) * 100
        }
    
    def save_to_file(self, filename: str = "detection_stats.json"):
        """Guarda las estadísticas en un archivo JSON"""
        stats_data = {
            'summary': self.get_summary(),
            'detection_history': self.detection_history,
            'last_updated': datetime.now().isoformat()
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

@dataclass
class HeuristicConfig:
    # Umbrales ajustables (HSV y métricas)
    dark_v_thresh: int = 60          # V bajo: posibles magulladuras
    dark_s_thresh: int = 80          # S bajo junto con V bajo refuerza mancha
    dark_min_ratio: float = 0.035    # % mínimo de píxeles oscuros para sospechar

    brown_h_low: int = 10            # tonos marrones/rojizos (moho seco/oxidación)
    brown_h_high: int = 25           # en HSV aprox.
    brown_s_min: int = 70
    brown_v_max: int = 150
    brown_min_ratio: float = 0.02

    mold_green_h_low: int = 80       # moho verdoso/azulado
    mold_green_h_high: int = 140
    mold_s_min: int = 40
    mold_v_max: int = 160
    mold_min_ratio: float = 0.01

    low_sat_high_val_s: int = 35     # zonas blanquecinas con baja saturación (posible moho blanco)
    low_sat_high_val_v: int = 200
    low_sat_high_val_min_ratio: float = 0.015

    laplace_blur_thresh: float = 20.0  # nitidez mínima (evitar falsos por desenfoque)

    final_spoiled_score_thresh: float = 0.5  # umbral final para marcar MALOGRADA

    # Umbrales para detección de frutas
    fruit_min_area: int = 500        # área mínima para considerar fruta (más reducido)
    fruit_max_area: int = 1000000    # área máxima para considerar fruta (mucho más aumentado)
    fruit_min_circularity: float = 0.05  # circularidad mínima (muy reducido para plátanos)
    fruit_max_aspect_ratio: float = 8.0  # relación de aspecto máxima (aumentado para plátanos)


def compute_laplacian_variance(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def is_fruit(bgr, fruit_mask, cfg: HeuristicConfig):
    """
    Determina si el objeto detectado es una fruta basándose en características geométricas y de color.
    """
    # Calcular área del objeto
    area = np.count_nonzero(fruit_mask)
    
    # Verificar área mínima (más flexible)
    if area < cfg.fruit_min_area:
        return False, f"Área muy pequeña: {area} píxeles (mín: {cfg.fruit_min_area})"
    
    if area > cfg.fruit_max_area:
        return False, f"Área muy grande: {area} píxeles (máx: {cfg.fruit_max_area})"
    
    # Calcular contornos para análisis geométrico
    contours, _ = cv2.findContours(fruit_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, "No se encontraron contornos"
    
    # Usar el contorno más grande
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Calcular circularidad
    perimeter = cv2.arcLength(largest_contour, True)
    if perimeter == 0:
        return False, "Perímetro cero"
    
    circularity = 4 * np.pi * area / (perimeter * perimeter)
    
    # Calcular relación de aspecto
    x, y, w, h = cv2.boundingRect(largest_contour)
    aspect_ratio = max(w, h) / min(w, h)
    
    # Análisis de color - las frutas suelen tener colores saturados
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    masked_hsv = cv2.bitwise_and(hsv, hsv, mask=fruit_mask)
    
    # Calcular saturación promedio (más flexible)
    mean_saturation = np.mean(masked_hsv[fruit_mask > 0, 1])
    mean_hue = np.mean(masked_hsv[fruit_mask > 0, 0])
    
    # Criterios especiales para plátanos (objetos alargados y amarillos)
    is_banana_like = (aspect_ratio > 1.5 and 15 <= mean_hue <= 40 and mean_saturation > 40)
    
    # Si parece un plátano, ser más flexible con la circularidad
    if is_banana_like:
        if circularity < 0.03:  # Muy bajo para plátanos
            return False, f"Circularidad muy baja para plátano: {circularity:.2f}"
        if aspect_ratio > cfg.fruit_max_aspect_ratio:
            return False, f"Relación de aspecto muy alta: {aspect_ratio:.2f} (máx: {cfg.fruit_max_aspect_ratio})"
    else:
        # Para otras frutas, usar criterios normales
        if circularity < cfg.fruit_min_circularity:
            return False, f"Circularidad muy baja: {circularity:.2f} (mín: {cfg.fruit_min_circularity})"
        if aspect_ratio > cfg.fruit_max_aspect_ratio:
            return False, f"Relación de aspecto muy alta: {aspect_ratio:.2f} (máx: {cfg.fruit_max_aspect_ratio})"
    
    if mean_saturation < 15:  # Muy poco saturado (reducido de 20 a 15)
        return False, f"Saturación muy baja: {mean_saturation:.1f} (mín: 15)"
    
    fruit_type = "plátano" if is_banana_like else "fruta"
    return True, f"Objeto parece ser una {fruit_type} (área: {area}, circularidad: {circularity:.2f}, saturación: {mean_saturation:.1f}, aspecto: {aspect_ratio:.2f})"


def identify_fruit_type(bgr, fruit_mask):
    """
    Identifica el tipo de fruta basándose en análisis de color y forma.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    masked_hsv = cv2.bitwise_and(hsv, hsv, mask=fruit_mask)
    
    # Obtener píxeles de la fruta
    fruit_pixels = masked_hsv[fruit_mask > 0]
    
    if len(fruit_pixels) == 0:
        return "Desconocido", 0.0
    
    # Calcular histograma de tono (H)
    hist_h = cv2.calcHist([masked_hsv], [0], fruit_mask, [180], [0, 180])
    hist_h = hist_h.flatten()
    
    # Calcular color dominante
    dominant_h = np.argmax(hist_h)
    mean_s = np.mean(fruit_pixels[:, 1])
    mean_v = np.mean(fruit_pixels[:, 2])
    
    # Análisis de forma
    contours, _ = cv2.findContours(fruit_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = max(w, h) / min(w, h)
    else:
        aspect_ratio = 1.0
    
    # Debug: mostrar valores detectados
    print(f"DEBUG - Color detectado: H={dominant_h}, S={mean_s:.1f}, V={mean_v:.1f}, Aspecto={aspect_ratio:.2f}")
    
    # Clasificación basada en color y forma
    fruit_type = "Desconocido"
    confidence = 0.0
    
    # Manzana (roja/verde, circular)
    if (0 <= dominant_h <= 10 or 170 <= dominant_h <= 180) and aspect_ratio < 1.5:
        if mean_s > 100 and mean_v > 100:
            fruit_type = "Manzana"
            confidence = 0.8
    elif 40 <= dominant_h <= 80 and aspect_ratio < 1.5:  # Verde
        if mean_s > 80 and mean_v > 100:
            fruit_type = "Manzana Verde"
            confidence = 0.7
    
    # Plátano (amarillo, alargado) - criterios más flexibles
    elif 15 <= dominant_h <= 40 and aspect_ratio > 1.5:  # Rango de tono más amplio
        if mean_s > 80 and mean_v > 100:  # Saturación y valor más flexibles
            fruit_type = "Plátano"
            confidence = 0.9
        elif mean_s > 60 and mean_v > 80:  # Criterios aún más flexibles
            fruit_type = "Plátano"
            confidence = 0.7
    
    # Naranja (naranja, circular)
    elif 10 <= dominant_h <= 25 and aspect_ratio < 1.5:
        if mean_s > 120 and mean_v > 120:
            fruit_type = "Naranja"
            confidence = 0.8
    
    # Limón (amarillo, circular/ovalado)
    elif 25 <= dominant_h <= 35 and aspect_ratio < 2.0:
        if mean_s > 100 and mean_v > 150:
            fruit_type = "Limón"
            confidence = 0.7
    
    # Fresa (roja, forma irregular)
    elif (0 <= dominant_h <= 10 or 170 <= dominant_h <= 180) and aspect_ratio < 1.8:
        if mean_s > 120 and mean_v > 100:
            fruit_type = "Fresa"
            confidence = 0.6
    
    # Uva (morada/verde, pequeña y circular)
    elif (120 <= dominant_h <= 140 or 40 <= dominant_h <= 80) and aspect_ratio < 1.3:
        if mean_s > 80 and mean_v > 80:
            fruit_type = "Uva"
            confidence = 0.6
    
    # Pera (verde/amarilla, forma de pera)
    elif (40 <= dominant_h <= 80 or 20 <= dominant_h <= 40) and 1.2 < aspect_ratio < 2.0:
        if mean_s > 60 and mean_v > 100:
            fruit_type = "Pera"
            confidence = 0.7
    
    return fruit_type, confidence


def analyze_histogram(bgr, mask=None):
    """
    Analiza histogramas de color para detectar anomalías en la fruta.
    """
    if mask is None:
        mask = np.ones(bgr.shape[:2], dtype=np.uint8) * 255
    
    # Convertir a diferentes espacios de color
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    
    # Calcular histogramas
    hist_b = cv2.calcHist([bgr], [0], mask, [256], [0, 256])
    hist_g = cv2.calcHist([bgr], [1], mask, [256], [0, 256])
    hist_r = cv2.calcHist([bgr], [2], mask, [256], [0, 256])
    hist_h = cv2.calcHist([hsv], [0], mask, [180], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], mask, [256], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], mask, [256], [0, 256])
    
    # Normalizar histogramas
    hist_b = cv2.normalize(hist_b, hist_b).flatten()
    hist_g = cv2.normalize(hist_g, hist_g).flatten()
    hist_r = cv2.normalize(hist_r, hist_r).flatten()
    hist_h = cv2.normalize(hist_h, hist_h).flatten()
    hist_s = cv2.normalize(hist_s, hist_s).flatten()
    hist_v = cv2.normalize(hist_v, hist_v).flatten()
    
    # Calcular métricas de distribución
    def calculate_skewness(hist):
        """Calcula la asimetría del histograma"""
        mean = np.sum(np.arange(len(hist)) * hist)
        variance = np.sum(((np.arange(len(hist)) - mean) ** 2) * hist)
        std = np.sqrt(variance)
        if std == 0:
            return 0
        skewness = np.sum(((np.arange(len(hist)) - mean) ** 3) * hist) / (std ** 3)
        return skewness
    
    # Detectar picos anómalos en el histograma de valor (V)
    v_peaks = []
    for i in range(1, len(hist_v) - 1):
        if hist_v[i] > hist_v[i-1] and hist_v[i] > hist_v[i+1] and hist_v[i] > 0.1:
            v_peaks.append(i)
    
    # Detectar zonas muy oscuras o muy claras
    dark_ratio = np.sum(hist_v[:50])  # Píxeles muy oscuros
    bright_ratio = np.sum(hist_v[200:])  # Píxeles muy claros
    
    return {
        'histograms': {'b': hist_b, 'g': hist_g, 'r': hist_r, 'h': hist_h, 's': hist_s, 'v': hist_v},
        'v_peaks': v_peaks,
        'dark_ratio': dark_ratio,
        'bright_ratio': bright_ratio,
        'v_skewness': calculate_skewness(hist_v),
        's_skewness': calculate_skewness(hist_s)
    }


def ratio(mask):
    # % de píxeles verdaderos respecto del área de interés
    return float(np.count_nonzero(mask)) / float(mask.size + 1e-9)


def detect_edges_advanced(bgr, mask=None):
    """
    Detección avanzada de bordes usando múltiples técnicas de OpenCV.
    """
    if mask is None:
        mask = np.ones(bgr.shape[:2], dtype=np.uint8) * 255
    
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # Aplicar máscara
    gray = cv2.bitwise_and(gray, gray, mask=mask)
    
    # 1. Canny edge detection
    edges_canny = cv2.Canny(gray, 50, 150)
    
    # 2. Sobel edges
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    sobel_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
    edges_sobel = np.uint8(sobel_magnitude > 30)
    
    # 3. Laplacian edges
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    edges_laplacian = np.uint8(np.absolute(laplacian) > 30)
    
    # 4. Scharr edges (más sensible que Sobel)
    scharr_x = cv2.Scharr(gray, cv2.CV_64F, 1, 0)
    scharr_y = cv2.Scharr(gray, cv2.CV_64F, 0, 1)
    scharr_magnitude = np.sqrt(scharr_x**2 + scharr_y**2)
    edges_scharr = np.uint8(scharr_magnitude > 20)
    
    # Combinar diferentes detecciones
    combined_edges = cv2.bitwise_or(edges_canny, edges_sobel)
    combined_edges = cv2.bitwise_or(combined_edges, edges_laplacian)
    combined_edges = cv2.bitwise_or(combined_edges, edges_scharr)
    
    # Morfología para limpiar
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    combined_edges = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)
    
    return {
        'canny': edges_canny,
        'sobel': edges_sobel,
        'laplacian': edges_laplacian,
        'scharr': edges_scharr,
        'combined': combined_edges
    }


def detect_blobs(bgr, mask=None):
    """
    Detecta blobs (manchas) usando SimpleBlobDetector de OpenCV.
    """
    if mask is None:
        mask = np.ones(bgr.shape[:2], dtype=np.uint8) * 255
    
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_and(gray, gray, mask=mask)
    
    # Configurar detector de blobs
    params = cv2.SimpleBlobDetector_Params()
    
    # Filtrar por área
    params.filterByArea = True
    params.minArea = 50
    params.maxArea = 5000
    
    # Filtrar por circularidad
    params.filterByCircularity = True
    params.minCircularity = 0.1
    params.maxCircularity = 1.0
    
    # Filtrar por convexidad
    params.filterByConvexity = True
    params.minConvexity = 0.3
    params.maxConvexity = 1.0
    
    # Filtrar por inercia (elongación)
    params.filterByInertia = True
    params.minInertiaRatio = 0.1
    params.maxInertiaRatio = 1.0
    
    # Crear detector
    detector = cv2.SimpleBlobDetector_create(params)
    
    # Detectar blobs
    keypoints = detector.detect(gray)
    
    # Crear imagen de visualización
    blob_vis = cv2.drawKeypoints(gray, keypoints, np.array([]), (0, 0, 255),
                                cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    
    # Analizar características de los blobs
    blob_info = []
    for kp in keypoints:
        x, y = int(kp.pt[0]), int(kp.pt[1])
        size = kp.size
        response = kp.response
        
        # Obtener color del blob
        if 0 <= x < bgr.shape[1] and 0 <= y < bgr.shape[0]:
            color = bgr[y, x]
            hsv_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2HSV)[0][0]
        else:
            hsv_color = [0, 0, 0]
        
        blob_info.append({
            'center': (x, y),
            'size': size,
            'response': response,
            'color_bgr': color.tolist(),
            'color_hsv': hsv_color.tolist()
        })
    
    return {
        'keypoints': keypoints,
        'blob_count': len(keypoints),
        'blob_info': blob_info,
        'visualization': blob_vis
    }


def mask_fruit_roi(bgr):
    """
    Crea una máscara aproximada de la fruta para reducir fondo.
    Usa segmentación mejorada por color (espacio HSV) y elimina fondo.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    
    # Crear máscara más restrictiva para frutas
    # Las frutas suelen tener colores saturados y no son blancas/negras
    h, s, v = cv2.split(hsv)
    
    # Máscara para colores saturados (frutas típicas)
    saturated = s > 30  # Saturación mínima
    
    # Excluir fondos muy claros o muy oscuros
    not_too_bright = v < 240
    not_too_dark = v > 30
    
    # Excluir colores muy poco saturados (fondos grises)
    not_gray = s > 20
    
    # Combinar condiciones
    base = (saturated & not_too_bright & not_too_dark & not_gray).astype(np.uint8) * 255

    # Morfología para limpiar ruido
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    
    # Limpiar ruido pequeño
    base = cv2.morphologyEx(base, cv2.MORPH_OPEN, kernel_small, iterations=1)
    # Rellenar huecos pequeños
    base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, kernel_small, iterations=1)

    # Encontrar componentes conectados
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(base, connectivity=8)
    if num_labels <= 1:
        return base

    # Filtrar componentes por área y forma
    areas = stats[1:, cv2.CC_STAT_AREA]
    widths = stats[1:, cv2.CC_STAT_WIDTH]
    heights = stats[1:, cv2.CC_STAT_HEIGHT]
    
    # Filtrar por área mínima y máxima
    valid_components = []
    for i in range(1, num_labels):
        area = areas[i-1]
        w, h = widths[i-1], heights[i-1]
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
        
        # Criterios más flexibles
        if (area > 1000 and area < 800000 and  # Área razonable
            aspect_ratio < 6.0):  # No demasiado alargado
            valid_components.append((i, area))
    
    if not valid_components:
        return base
    
    # Seleccionar el componente más grande que cumple los criterios
    largest_idx, _ = max(valid_components, key=lambda x: x[1])
    fruit_mask = (labels == largest_idx).astype(np.uint8) * 255
    
    # Limpiar la máscara final
    fruit_mask = cv2.morphologyEx(fruit_mask, cv2.MORPH_CLOSE, kernel_large, iterations=1)
    
    return fruit_mask


def analyze_heuristic(bgr, cfg: HeuristicConfig):
    h, w = bgr.shape[:2]

    # ROI de fruta (para ignorar fondo)
    fruit_mask = mask_fruit_roi(bgr)
    masked = cv2.bitwise_and(bgr, bgr, mask=fruit_mask)

    # Verificar si es una fruta
    is_fruit_obj, fruit_reason = is_fruit(bgr, fruit_mask, cfg)
    
    # Identificar tipo de fruta
    fruit_type, fruit_confidence = identify_fruit_type(bgr, fruit_mask)
    
    # Si no es una fruta, retornar alerta
    if not is_fruit_obj:
        return {
            'is_fruit': False,
            'fruit_reason': fruit_reason,
            'fruit_type': 'No es fruta',
            'fruit_confidence': 0.0,
            'spoiled': False,
            'score': 0.0,
            'debug': {'alert': f'ALERTA: {fruit_reason}'},
            'vis': np.zeros_like(bgr),
            'white_overlay': np.zeros_like(bgr),
            'fruit_mask': fruit_mask,
            'edge_analysis': {'combined': np.zeros((h, w), dtype=np.uint8)},
            'blob_analysis': {'visualization': np.zeros((h, w), dtype=np.uint8)},
            'histogram_analysis': {'histograms': {'v': np.zeros(256)}}
        }

    hsv = cv2.cvtColor(masked, cv2.COLOR_BGR2HSV)

    # Desenfoque?
    sharpness = compute_laplacian_variance(masked)
    
    # Análisis avanzado con OpenCV
    histogram_analysis = analyze_histogram(masked, fruit_mask)
    edge_analysis = detect_edges_advanced(masked, fruit_mask)
    blob_analysis = detect_blobs(masked, fruit_mask)

    # Manchas oscuras (magulladuras): V bajo & S medio/bajo
    dark_mask = (hsv[...,2] < cfg.dark_v_thresh) & (hsv[...,1] < cfg.dark_s_thresh)

    # Tonos marrones oscuros (oxidación/pudrición)
    brown_mask = (hsv[...,0] >= cfg.brown_h_low) & (hsv[...,0] <= cfg.brown_h_high) & \
                 (hsv[...,1] >= cfg.brown_s_min) & (hsv[...,2] <= cfg.brown_v_max)

    # Moho verdoso/azulado
    moldg_mask = (hsv[...,0] >= cfg.mold_green_h_low) & (hsv[...,0] <= cfg.mold_green_h_high) & \
                 (hsv[...,1] >= cfg.mold_s_min) & (hsv[...,2] <= cfg.mold_v_max)

    # Zonas blancas desaturadas (posible moho blanco)
    white_mold_mask = (hsv[...,1] < cfg.low_sat_high_val_s) & (hsv[...,2] > cfg.low_sat_high_val_v)

    # Considerar solo dentro del ROI
    roi = (fruit_mask > 0)
    if np.count_nonzero(roi) < 1000:
        # ROI demasiado pequeño: probablemente falló la segmentación
        roi = np.ones((h,w), dtype=bool)

    dark_r = ratio(dark_mask & roi)
    brown_r = ratio(brown_mask & roi)
    moldg_r = ratio(moldg_mask & roi)
    white_r = ratio(white_mold_mask & roi)

    # Ponderación empírica
    # Nota: Ajusta estos pesos en pruebas reales.
    score = (
        0.45 * min(1.0, dark_r / cfg.dark_min_ratio) +
        0.25 * min(1.0, brown_r / cfg.brown_min_ratio) +
        0.20 * min(1.0, moldg_r / cfg.mold_min_ratio) +
        0.10 * min(1.0, white_r / cfg.low_sat_high_val_min_ratio)
    )
    # Penaliza si la imagen está muy borrosa
    if sharpness < cfg.laplace_blur_thresh:
        score *= 0.8

    # Normalizar a [0,1] de forma simple (los ratios normalizados ya están capados a 1)
    score = np.clip(score, 0.0, 1.0)
    spoiled = score >= cfg.final_spoiled_score_thresh

    debug = {
        "dark_ratio": dark_r,
        "brown_ratio": brown_r,
        "green_mold_ratio": moldg_r,
        "white_mold_ratio": white_r,
        "sharpness": sharpness,
        "score": score,
        "spoiled": spoiled,
        "histogram_dark_ratio": histogram_analysis['dark_ratio'],
        "histogram_bright_ratio": histogram_analysis['bright_ratio'],
        "histogram_v_skewness": histogram_analysis['v_skewness'],
        "blob_count": blob_analysis['blob_count'],
        "edge_density": np.sum(edge_analysis['combined']) / (h * w)
    }

    # Visualización de máscaras (para depuración)
    vis = np.zeros_like(bgr)
    vis[..., 0] = (moldg_mask & roi).astype(np.uint8) * 255         # canal azul = moho verd/azul
    vis[..., 1] = (brown_mask & roi).astype(np.uint8) * 255         # canal verde = marrón
    vis[..., 2] = (dark_mask & roi).astype(np.uint8) * 255          # canal rojo = oscuro
    # zonas blancas se mostrarán por separado con overlay
    white_overlay = (white_mold_mask & roi).astype(np.uint8) * 255
    white_overlay = cv2.cvtColor(white_overlay, cv2.COLOR_GRAY2BGR)

    return {
        'is_fruit': True,
        'fruit_reason': fruit_reason,
        'fruit_type': fruit_type,
        'fruit_confidence': fruit_confidence,
        'spoiled': spoiled,
        'score': score,
        'debug': debug,
        'vis': vis,
        'white_overlay': white_overlay,
        'fruit_mask': fruit_mask,
        'edge_analysis': edge_analysis,
        'blob_analysis': blob_analysis,
        'histogram_analysis': histogram_analysis
    }


def try_onnx_infer(bgr, model_path="model.onnx"):
    if not HAS_ORT:
        return None
    if not os.path.exists(model_path):
        return None

    # Preprocesado básico; ajusta según tu modelo
    img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))  # CHW
    img = np.expand_dims(img, 0)        # NCHW

    # Ejecutar ONNX
    sess = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    input_name = sess.get_inputs()[0].name
    outputs = sess.run(None, {input_name: img})

    # Suponemos salida [N,2] (OK, MALOGRADA). Adapta si tu modelo difiere.
    out = outputs[0]
    if out.ndim == 2 and out.shape[1] >= 2:
        # argmax
        pred_idx = int(np.argmax(out, axis=1)[0])
        spoiled_prob = float(np.exp(out[0,1]) / np.sum(np.exp(out[0,:])))
        return {"pred_idx": pred_idx, "spoiled_prob": spoiled_prob, "raw": out}
    else:
        # Si es una sola neurona (sigmoid)
        val = float(out.reshape(-1)[0])
        spoiled_prob = 1.0 / (1.0 + np.exp(-val))
        pred_idx = 1 if spoiled_prob >= 0.5 else 0
        return {"pred_idx": pred_idx, "spoiled_prob": spoiled_prob, "raw": out}


def create_training_structure(base_dir: str = "salidas"):
    """Crea la estructura de carpetas para entrenamiento de IA"""
    training_dirs = [
        f"{base_dir}/training_data",
        f"{base_dir}/training_data/OK",
        f"{base_dir}/training_data/MALOGRADA",
        f"{base_dir}/training_data/NO_FRUIT",
        f"{base_dir}/metadata",
        f"{base_dir}/masks",
        f"{base_dir}/results"
    ]
    
    # Crear subcarpetas por tipo de fruta
    fruit_types = ["Manzana", "Manzana Verde", "Plátano", "Naranja", "Limón", "Fresa", "Uva", "Pera", "Desconocido"]
    for fruit_type in fruit_types:
        training_dirs.extend([
            f"{base_dir}/training_data/OK/{fruit_type}",
            f"{base_dir}/training_data/MALOGRADA/{fruit_type}"
        ])
    
    for dir_path in training_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    return training_dirs

def save_training_data(bgr, analysis_result, timestamp: str, base_dir: str = "salidas"):
    """Guarda los datos de entrenamiento de forma organizada"""
    # Crear estructura de carpetas
    create_training_structure(base_dir)
    
    # Determinar estado y tipo
    is_fruit = analysis_result['is_fruit']
    fruit_type = analysis_result.get('fruit_type', 'Desconocido')
    spoiled = analysis_result.get('spoiled', False)
    fruit_confidence = analysis_result.get('fruit_confidence', 0.0)
    score = analysis_result.get('score', 0.0)
    
    # Determinar carpeta de destino
    if not is_fruit:
        status_dir = "NO_FRUIT"
        fruit_type = "No_Fruta"
    else:
        status_dir = "MALOGRADA" if spoiled else "OK"
    
    # Crear nombres de archivo
    filename_base = f"{timestamp}_{fruit_type}_{status_dir}"
    
    # Guardar imagen original
    original_path = f"{base_dir}/training_data/{status_dir}/{fruit_type}/{filename_base}.jpg"
    cv2.imwrite(original_path, bgr)
    
    # Guardar imagen con resultados si es fruta
    if is_fruit:
        overlay = analysis_result.get('vis', np.zeros_like(bgr))
        result_path = f"{base_dir}/results/{filename_base}_result.jpg"
        cv2.imwrite(result_path, overlay)
        
        # Guardar máscaras
        fruit_mask = analysis_result.get('fruit_mask', np.zeros_like(bgr))
        mask_path = f"{base_dir}/masks/{filename_base}_mask.png"
        cv2.imwrite(mask_path, fruit_mask)
    
    # Crear metadatos
    metadata = {
        'timestamp': timestamp,
        'is_fruit': is_fruit,
        'fruit_type': fruit_type,
        'spoiled': spoiled,
        'confidence': fruit_confidence,
        'score': score,
        'file_paths': {
            'original': original_path,
            'result': f"{base_dir}/results/{filename_base}_result.jpg" if is_fruit else None,
            'mask': f"{base_dir}/masks/{filename_base}_mask.png" if is_fruit else None
        },
        'analysis_details': analysis_result.get('debug', {}),
        'image_shape': bgr.shape
    }
    
    # Guardar metadatos
    metadata_path = f"{base_dir}/metadata/{filename_base}_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return metadata


def main():
    ap = argparse.ArgumentParser(description="Identificador de fruta malograda por webcam")
    ap.add_argument("--camera", type=int, default=0, help="Índice de cámara (0 por defecto)")
    ap.add_argument("--width", type=int, default=1280, help="Ancho de captura")
    ap.add_argument("--height", type=int, default=720, help="Alto de captura")
    ap.add_argument("--save", action="store_true", help="Guardar la foto capturada y resultados")
    ap.add_argument("--training", action="store_true", help="Modo entrenamiento: guarda datos organizados para IA")
    ap.add_argument("--no-viz", action="store_true", help="No abrir ventanas de visualización")
    ap.add_argument("--model", type=str, default="model.onnx", help="Ruta al modelo ONNX (opcional)")
    ap.add_argument("--max-area", type=int, default=1000000, help="Área máxima para considerar fruta")
    ap.add_argument("--min-area", type=int, default=500, help="Área mínima para considerar fruta")
    ap.add_argument("--stats-file", type=str, default="detection_stats.json", help="Archivo para guardar estadísticas")
    args = ap.parse_args()

    # Inicializar estadísticas
    stats = DetectionStats()

    cap = cv2.VideoCapture(args.camera)
    if args.width and args.height:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la cámara. Prueba con --camera 1 (u otro índice).")
        sys.exit(1)

    print("Presiona 'c' para capturar, 'q' para salir, 's' para estadísticas...")
    last_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] No se pudo leer un frame de la cámara.")
            break
        last_frame = frame.copy()

        # Mostrar vista previa con instrucciones
        preview = frame.copy()
        cv2.putText(preview, "Presiona 'c' para capturar, 'q' para salir, 's' para estadísticas",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,0), 3, cv2.LINE_AA)
        cv2.putText(preview, "Presiona 'c' para capturar, 'q' para salir, 's' para estadísticas",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 1, cv2.LINE_AA)

        if not args.no_viz:
            cv2.imshow("Camara - Detector de Fruta", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Mostrar estadísticas
            summary = stats.get_summary()
            print("\n" + "="*50)
            print("ESTADÍSTICAS DE DETECCIÓN")
            print("="*50)
            print(f"Total de detecciones: {summary['total_detections']}")
            print(f"Frutas detectadas: {summary['total_fruits']}")
            print(f"No frutas: {summary['total_non_fruits']}")
            print(f"Tasa de éxito: {summary['success_rate']:.1f}%")
            print("\nPor estado:")
            for status, count in summary['fruits_by_status'].items():
                print(f"  {status}: {count}")
            print("\nPor tipo de fruta:")
            for fruit_type, data in summary['fruits_by_type'].items():
                print(f"  {fruit_type}: {data['total']} (OK: {data['OK']}, MALOGRADA: {data['MALOGRADA']})")
            print("="*50)
            continue
        elif key == ord('c'):
            # Procesar la captura
            bgr = last_frame
            ts = time.strftime("%Y%m%d_%H%M%S")

            # Intentar inferencia con modelo si está disponible
            onnx_info = try_onnx_infer(bgr, args.model)

            cfg = HeuristicConfig()
            # Usar parámetros de línea de comandos si se proporcionan
            cfg.fruit_min_area = args.min_area
            cfg.fruit_max_area = args.max_area
            analysis_result = analyze_heuristic(bgr, cfg)

            # Verificar si es una fruta
            if not analysis_result['is_fruit']:
                # Registrar en estadísticas
                stats.add_detection(
                    is_fruit=False,
                    fruit_type="No_Fruta",
                    status="NO_FRUIT",
                    confidence=0.0,
                    score=0.0
                )
                
                # Mostrar alerta de que no es una fruta
                alert_vis = bgr.copy()
                cv2.putText(alert_vis, "ALERTA: NO ES UNA FRUTA", (20, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                cv2.putText(alert_vis, f"Razon: {analysis_result['fruit_reason']}", (20, 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.putText(alert_vis, f"Total detecciones: {stats.total_detections}", (20, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(alert_vis, "Presiona 'c' para otra captura, 'q' para salir", (20, 160), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Mostrar información de debug
                fruit_mask = analysis_result['fruit_mask']
                area = np.count_nonzero(fruit_mask)
                cv2.putText(alert_vis, f"Area detectada: {area} pixeles", (20, 200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(alert_vis, f"Min area: {cfg.fruit_min_area}, Max area: {cfg.fruit_max_area}", (20, 230), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                
                if not args.no_viz:
                    cv2.imshow("ALERTA - No es fruta", alert_vis)
                    # Mostrar la máscara de detección para debug
                    cv2.imshow("Mascara de deteccion", fruit_mask)
                
                print(f"ALERTA: {analysis_result['fruit_reason']}")
                print(f"Área detectada: {area} píxeles")
                print(f"Rango esperado: {cfg.fruit_min_area} - {cfg.fruit_max_area} píxeles")
                
                # Guardar datos de entrenamiento si está habilitado
                if args.training:
                    save_training_data(bgr, analysis_result, ts)
                    print(f"[INFO] Datos de entrenamiento guardados para NO_FRUIT")
                
                continue

            # Es una fruta, continuar con el análisis
            spoiled = analysis_result['spoiled']
            score = analysis_result['score']
            debug = analysis_result['debug']
            vis_masks = analysis_result['vis']
            white_overlay = analysis_result['white_overlay']
            fruit_mask = analysis_result['fruit_mask']
            edge_analysis = analysis_result['edge_analysis']
            blob_analysis = analysis_result['blob_analysis']
            histogram_analysis = analysis_result['histogram_analysis']
            fruit_type = analysis_result['fruit_type']
            fruit_confidence = analysis_result['fruit_confidence']

            # Decisión final: si hay onnx, combinar suavemente (priorizar modelo)
            final_label = "MALOGRADA" if spoiled else "OK"
            final_score = score
            combo_note = "heuristico"

            if onnx_info is not None:
                model_spoiled = (onnx_info["pred_idx"] == 1)
                model_prob = onnx_info["spoiled_prob"]
                # Combinación: si el modelo es muy seguro (>0.7), ganará;
                # si no, tomar heurístico o promedio.
                if model_prob >= 0.7:
                    final_label = "MALOGRADA"
                    final_score = max(final_score, model_prob)
                    combo_note = "modelo(on)"
                elif model_prob <= 0.3:
                    final_label = "OK"
                    final_score = min(final_score, 1.0 - model_prob)
                    combo_note = "modelo(on)"
                else:
                    # promediamos con heurístico
                    final_score = (final_score + model_prob) / 2.0
                    final_label = "MALOGRADA" if final_score >= 0.5 else "OK"
                    combo_note = "mix"

            # Registrar en estadísticas
            stats.add_detection(
                is_fruit=True,
                fruit_type=fruit_type,
                status=final_label,
                confidence=fruit_confidence,
                score=final_score
            )

            # Visualización de resultados
            out_vis = bgr.copy()
            # Dibujar contorno ROI
            contours, _ = cv2.findContours(fruit_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(out_vis, contours, -1, (0,255,255), 2)

            # Overlay de máscaras
            alpha = 0.5
            overlay = cv2.addWeighted(out_vis, 1.0, vis_masks, alpha, 0)
            overlay = cv2.addWeighted(overlay, 1.0, white_overlay, 0.35, 0)

            # Texto de salida
            fruit_info = f"Fruta: {fruit_type} (conf: {fruit_confidence:.2f})"
            cv2.putText(overlay, fruit_info, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(overlay, fruit_info, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2, cv2.LINE_AA)
            
            txt = f"Estado: {final_label} | score={final_score:.2f} ({combo_note})"
            cv2.putText(overlay, txt, (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(overlay, txt, (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0) if final_label=="OK" else (0,0,255), 2, cv2.LINE_AA)

            # Mostrar contadores
            counter_info = f"Total: {stats.total_detections} | Frutas: {stats.total_fruits} | {final_label}: {stats.fruits_by_status[final_label]}"
            cv2.putText(overlay, counter_info, (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(overlay, counter_info, (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1, cv2.LINE_AA)

            # Info debug breve
            dbg1 = f"dark={debug['dark_ratio']:.3f} brown={debug['brown_ratio']:.3f} green={debug['green_mold_ratio']:.3f} white={debug['white_mold_ratio']:.3f} sharp={debug['sharpness']:.1f}"
            cv2.putText(overlay, dbg1, (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(overlay, dbg1, (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1, cv2.LINE_AA)
            
            # Info adicional de OpenCV
            dbg2 = f"blobs={debug['blob_count']} edges={debug['edge_density']:.3f} hist_dark={debug['histogram_dark_ratio']:.3f} hist_skew={debug['histogram_v_skewness']:.2f}"
            cv2.putText(overlay, dbg2, (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(overlay, dbg2, (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

            if not args.no_viz:
                cv2.imshow("Resultado - Detector de Fruta", overlay)
                cv2.imshow("Mascaras (B=moho verd/azul, G=marron, R=oscuro)", vis_masks)
                
                # Mostrar análisis avanzado de OpenCV
                cv2.imshow("Deteccion de Bordes", edge_analysis['combined'])
                cv2.imshow("Deteccion de Blobs", blob_analysis['visualization'])
                
                # Crear visualización de histograma
                hist_vis = np.zeros((300, 512, 3), dtype=np.uint8)
                hist_v = histogram_analysis['histograms']['v']
                for i in range(len(hist_v)-1):
                    x1 = int(i * 512 / len(hist_v))
                    x2 = int((i+1) * 512 / len(hist_v))
                    y1 = 300 - int(hist_v[i] * 300)
                    y2 = 300 - int(hist_v[i+1] * 300)
                    cv2.line(hist_vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.imshow("Histograma de Valor (V)", hist_vis)

            # Guardar datos según el modo
            if args.save:
                os.makedirs("salidas", exist_ok=True)
                cv2.imwrite(f"salidas/captura_{ts}.jpg", bgr)
                cv2.imwrite(f"salidas/resultado_{ts}.jpg", overlay)
                cv2.imwrite(f"salidas/mascaras_{ts}.png", vis_masks)
                print(f"[INFO] Guardado en carpeta 'salidas' con timestamp {ts}")

            if args.training:
                metadata = save_training_data(bgr, analysis_result, ts)
                print(f"[INFO] Datos de entrenamiento guardados para {fruit_type} - {final_label}")

            print(f"=== RESULTADO DEL ANÁLISIS ===")
            print(f"Tipo de fruta: {fruit_type} (confianza: {fruit_confidence:.2f})")
            print(f"Estado: {final_label} | Puntaje: {final_score:.2f} ({combo_note})")
            print(f"Detalles: {dbg1}")
            print(f"Estadísticas: Total={stats.total_detections}, Frutas={stats.total_fruits}, {final_label}={stats.fruits_by_status[final_label]}")
            print("=" * 40)

    # Guardar estadísticas finales
    stats.save_to_file(args.stats_file)
    print(f"\n[INFO] Estadísticas guardadas en {args.stats_file}")
    
    # Mostrar resumen final
    summary = stats.get_summary()
    print("\n" + "="*50)
    print("RESUMEN FINAL DE SESIÓN")
    print("="*50)
    print(f"Total de detecciones: {summary['total_detections']}")
    print(f"Frutas detectadas: {summary['total_fruits']}")
    print(f"No frutas: {summary['total_non_fruits']}")
    print(f"Tasa de éxito: {summary['success_rate']:.1f}%")
    print("="*50)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
