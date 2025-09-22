# detectar_fruta.py - detección ROI + clasificación ONNX + heurística + suavizado de resultados
import cv2
import numpy as np
import onnxruntime as ort
import time
from collections import deque
from datetime import datetime

# ----------------------------
# Configuración (ajustable)
# ----------------------------
MODEL_PATH = "modelo_manzana.onnx"
FRAME_SKIP_FOR_MODEL = 3     # ejecutar modelo cada N frames (reduce CPU)
ROI_PAD = 10                 # padding alrededor de la caja ROI (px)
MIN_ROI_AREA = 1500          # área mínima para considerar ROI válida
CIRCULARITY_MIN = 0.02       # circularidad mínima (manzana circular)
SMOOTH_WINDOW = 5            # cantidad de frames para votación de etiqueta
EMA_ALPHA = 0.5              # suavizado exponencial para confianza

# Normalización usada durante entrenamiento
# AJUSTA ESTO si tu entrenamiento usó otras medias/desv (ImageNet por defecto)
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# ----------------------------
# Cargar modelo ONNX (si existe)
# ----------------------------
try:
    session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    has_model = True
    print("[INFO] Modelo ONNX cargado:", MODEL_PATH)
except Exception as e:
    session = None
    input_name = None
    has_model = False
    print("[WARN] No se pudo cargar modelo ONNX:", e)

# ----------------------------
# Helpers: segmentación / ROI
# ----------------------------
def mask_fruit_roi(bgr):
    """Segmentación por color+morfología para obtener máscara aproximada de fruta."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # condiciones genéricas para colores saturados (frutas)
    sat_cond = s > 35
    not_too_bright = v < 245
    not_too_dark = v > 20

    base = (sat_cond & not_too_bright & not_too_dark).astype(np.uint8) * 255

    # limpiar
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    base = cv2.morphologyEx(base, cv2.MORPH_OPEN, kernel, iterations=1)
    base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, kernel, iterations=1)

    # componentes conectados -> elegir la componente más grande razonable
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(base, connectivity=8)
    if num_labels <= 1:
        return np.zeros_like(base)

    # buscar componente con mayor área que cumpla umbral
    areas = stats[1:, cv2.CC_STAT_AREA]
    idx_sorted = np.argsort(-areas)
    for idx in idx_sorted:
        area = int(areas[idx])
        if area >= MIN_ROI_AREA:
            comp_idx = idx + 1
            mask = (labels == comp_idx).astype(np.uint8) * 255
            # suavizar y devolver
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
            return mask
    return np.zeros_like(base)

def extract_roi_from_mask(bgr, mask):
    """Devuelve ROI recortada y bounding box (x,y,w,h). Si no válida devuelve None."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < MIN_ROI_AREA:
        return None, None
    x,y,w,h = cv2.boundingRect(largest)
    # padding
    x0 = max(0, x - ROI_PAD)
    y0 = max(0, y - ROI_PAD)
    x1 = min(bgr.shape[1], x + w + ROI_PAD)
    y1 = min(bgr.shape[0], y + h + ROI_PAD)
    roi = bgr[y0:y1, x0:x1].copy()
    # circularidad
    perimeter = cv2.arcLength(largest, True)
    circ = 0.0
    if perimeter > 0:
        circ = 4.0 * np.pi * area / (perimeter * perimeter)
    if circ < CIRCULARITY_MIN:
        # aún así permitimos (por si son manzanas parcialmente recortadas),
        # pero devolvemos marca de baja circularidad.
        pass
    return roi, (x0, y0, x1-x0, y1-y0)

# ----------------------------
# Helpers: preprocesado y predicción ONNX
# ----------------------------
def preprocess_for_model(roi):
    """Normaliza ROI y la deja con shape (1, C, H, W)"""
    img = cv2.resize(roi, (224,224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    img = (img - MEAN) / STD
    img = np.transpose(img, (2,0,1)).astype(np.float32)
    img = np.expand_dims(img, 0)
    return img

def predict_model_on_roi(roi):
    """Devuelve (label, conf). label = 'buena'|'mala'"""
    if not has_model:
        return None, None
    inp = preprocess_for_model(roi)
    out = session.run(None, {input_name: inp})[0]  # shape (1, C)
    out = np.asarray(out)
    # manejar softmax/logits o sigmoid
    if out.ndim == 2 and out.shape[1] >= 2:
        # aplicar softmax numéricamente estable
        exps = np.exp(out - np.max(out, axis=1, keepdims=True))
        probs = exps / np.sum(exps, axis=1, keepdims=True)
        prob = float(probs[0].max())
        idx = int(probs[0].argmax())
        label = "buena" if idx == 0 else "mala"
        return label, prob
    else:
        # salida 1D sigmoidea
        val = float(out.reshape(-1)[0])
        prob_spoiled = 1.0 / (1.0 + np.exp(-val))
        label = "mala" if prob_spoiled >= 0.5 else "buena"
        conf = prob_spoiled if label == "mala" else (1.0 - prob_spoiled)
        return label, conf

# ----------------------------
# Heurística focal en ROI (manchas, mordeduras)
# ----------------------------
def heuristica_on_roi(roi):
    """Analiza ROI recortada; devuelve (label, score_between_0_1)"""
    if roi is None or roi.size == 0:
        return "desconocido", 0.0
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # detectar manchas oscuras (umbral adaptable)
    _, dark = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
    dark_ratio = cv2.countNonZero(dark) / float(gray.size + 1e-9)
    # detectar textural irregularity (laplacian variance)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # heurística combinada (valores empíricos; ajustar)
    score_spoiled = min(1.0, dark_ratio * 4.0 + (1.0 if lap_var < 50 else 0.0) * 0.3)
    label = "mala" if score_spoiled >= 0.4 else "buena"
    conf = 1.0 - score_spoiled if label == "buena" else score_spoiled
    return label, conf

# ----------------------------
# Fusión y suavizado
# ----------------------------
label_window = deque(maxlen=SMOOTH_WINDOW)
conf_ema = None

def fuse_labels(model_label, model_conf, heur_label, heur_conf):
    """Devuelve (final_label, final_conf, source) y aplica suavizado temporal"""
    global conf_ema
    # preferir modelo, pero si coinciden, reforzar
    if model_label == heur_label:
        base_conf = (model_conf + heur_conf) / 2.0
        source = "ambos"
        final = model_label
    else:
        # si modelo dice mala o alta confianza, priorizarlo
        base_conf = 0.7 * (model_conf if model_conf is not None else 0.6) + 0.3 * heur_conf
        source = "modelo" if (model_conf or 0) >= 0.6 else "mix"
        final = model_label
    # suavizar confianza con EMA
    if conf_ema is None:
        conf_ema = base_conf
    else:
        conf_ema = EMA_ALPHA * base_conf + (1-EMA_ALPHA) * conf_ema
    # suavizar etiqueta por votación simple en ventana
    label_window.append(final)
    # majority vote
    vals, counts = np.unique(np.array(label_window), return_counts=True)
    voted = vals[np.argmax(counts)]
    return voted, float(conf_ema), source

# ----------------------------
# Estadísticas y util
# ----------------------------
stats = {"capturas_total": 0, "buena": 0, "mala": 0}
detection_history = []

def save_capture(frame, roi_bbox, final_label, final_conf):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname_full = f"salidas/captura_{ts}.jpg"
    cv2.imwrite(fname_full, frame)
    if roi_bbox is not None:
        x,y,w,h = roi_bbox
        roi = frame[y:y+h, x:x+w]
        cv2.imwrite(f"salidas/captura_{ts}_roi.jpg", roi)
    # log
    detection_history.append({"ts": ts, "label": final_label, "conf": final_conf, "file": fname_full})

# ----------------------------
# Main loop: cámara + detección ROI + clasificación
# ----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("No se pudo abrir la cámara")

frame_idx = 0
live_classify = True   # si quieres presionar tecla para toggle, se puede agregar

print("Iniciado. Teclas: c=capturar | s=stats | q=salir | l=toggle live classify")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_idx += 1

    # 1) extraer máscara y ROI candidata
    mask = mask_fruit_roi(frame)
    roi, bbox = extract_roi_from_mask(frame, mask)

    # mostrar máscara y bbox para debug
    vis = frame.copy()
    if bbox is not None:
        x,y,w,h = bbox
        cv2.rectangle(vis, (x,y), (x+w, y+h), (0,255,255), 2)

    # 2) decidir si clasificar (si hay ROI válida)
    model_label, model_conf = None, None
    heur_label, heur_conf = None, None
    if roi is not None:
        # ejecutar heurística siempre
        heur_label, heur_conf = heuristica_on_roi(roi)
        # ejecutar modelo cada N frames para ahorrar CPU
        if has_model and (frame_idx % FRAME_SKIP_FOR_MODEL == 0):
            try:
                model_label, model_conf = predict_model_on_roi(roi)
            except Exception as e:
                print("[ERROR] inferencia ONNX:", e)
                model_label, model_conf = None, None
        # si no hay modelo o no fue ejecutado, dejamos model_label None
    else:
        # no ROI: no clasificar
        pass

    # 3) fusionar resultados y suavizar
    # Si no hay modelo (model_label None) usar heurística sola
    if model_label is None:
        if heur_label is None:
            final_label, final_conf, source = "no_fruta", 0.0, "none"
        else:
            final_label, final_conf, source = heur_label, heur_conf, "heuristica"
    else:
        final_label, final_conf, source = fuse_labels(model_label, model_conf or 0.0, heur_label or model_label, heur_conf or (model_conf or 0.0))

    # 4) mostrar overlay en vivo (bbox, mask, label sólo cuando ROI existe)
    display = vis.copy()
    if mask is not None and mask.any():
        # overlay mask (transparente)
        mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        display = cv2.addWeighted(display, 1.0, mask_color, 0.25, 0)
    if bbox is not None:
        x,y,w,h = bbox
        color = (0,255,0) if "buena" in final_label else (0,0,255)
        cv2.rectangle(display, (x,y), (x+w, y+h), color, 2)
        cv2.putText(display, f"{final_label} ({source}) {final_conf:.2f}", (x, max(15,y-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # mostrar instrucciones arriba
    cv2.putText(display, "Presiona 'c' capturar | 's' stats | 'q' salir | 'l' live on/off", (10,20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    cv2.imshow("Detector Fruta - ROI + Clasificacion", display)

    # ----- key handling -----
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('l'):
        live_classify = not live_classify
        print("[INFO] live_classify =", live_classify)
    elif key == ord('s'):
        print("=== STATS ===")
        print("Total capturas:", stats["capturas_total"])
        print("Buenas:", stats["buena"], "Mala:", stats["mala"])
        print("Hist len:", len(detection_history))
    elif key == ord('c'):
        # guardar captura y mostrar resultado en consola
        os_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # ensure folder
        import os
        os.makedirs("salidas", exist_ok=True)
        save_capture(frame, bbox, final_label, final_conf)
        stats["capturas_total"] += 1
        if "buena" in final_label:
            stats["buena"] += 1
        elif "mala" in final_label:
            stats["mala"] += 1
        print(f"📸 Captura guardada ({os_ts}) -> Resultado: {final_label} | Confianza: {final_conf:.2f} | Fuente: {source}")

# cleanup
cap.release()
cv2.destroyAllWindows()
