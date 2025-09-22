"""
Servicio de detección de manzanas adaptado para la API
"""
import os
import json
import cv2
import numpy as np
import onnxruntime as ort
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import asyncio

class DetectionService:
    def __init__(self):
        self.model_path = "modelo_manzana.onnx"
        self.session = None
        self.input_name = None
        self.has_model = False
        self.stats_file = Path("detection_stats.json")
        
        # Configuración
        self.roi_pad = 10
        self.min_roi_area = 1500
        self.circularity_min = 0.02
        
        # Normalización
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        
        # Cargar modelo
        self._load_model()
        
        # Cargar estadísticas existentes
        self._load_stats()
    
    def _load_model(self):
        """Cargar modelo ONNX"""
        try:
            if Path(self.model_path).exists():
                self.session = ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
                self.input_name = self.session.get_inputs()[0].name
                self.has_model = True
                print(f"[INFO] Modelo ONNX cargado: {self.model_path}")
            else:
                print(f"[WARN] Modelo no encontrado: {self.model_path}")
        except Exception as e:
            print(f"[ERROR] Error cargando modelo: {e}")
            self.has_model = False
    
    def is_model_loaded(self) -> bool:
        """Verificar si el modelo está cargado"""
        return self.has_model
    
    def _load_stats(self):
        """Cargar estadísticas existentes"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            except:
                self.stats = self._create_empty_stats()
        else:
            self.stats = self._create_empty_stats()
    
    def _create_empty_stats(self) -> Dict[str, Any]:
        """Crear estadísticas vacías"""
        return {
            "summary": {
                "total_detections": 0,
                "total_fruits": 0,
                "total_non_fruits": 0,
                "fruits_by_type": {},
                "fruits_by_status": {"OK": 0, "MALOGRADA": 0},
                "success_rate": 0.0
            },
            "detection_history": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """Guardar estadísticas"""
        self.stats["last_updated"] = datetime.now().isoformat()
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def mask_fruit_roi(self, bgr: np.ndarray) -> np.ndarray:
        """Segmentación por color+morfología para obtener máscara aproximada de fruta"""
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Condiciones genéricas para colores saturados (frutas)
        sat_cond = s > 35
        not_too_bright = v < 245
        not_too_dark = v > 20

        base = (sat_cond & not_too_bright & not_too_dark).astype(np.uint8) * 255

        # Limpiar
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        base = cv2.morphologyEx(base, cv2.MORPH_OPEN, kernel, iterations=1)
        base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Componentes conectados -> elegir la componente más grande razonable
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(base, connectivity=8)
        if num_labels <= 1:
            return np.zeros_like(base)

        # Buscar componente con mayor área que cumpla umbral
        areas = stats[1:, cv2.CC_STAT_AREA]
        idx_sorted = np.argsort(-areas)
        for idx in idx_sorted:
            area = int(areas[idx])
            if area >= self.min_roi_area:
                comp_idx = idx + 1
                mask = (labels == comp_idx).astype(np.uint8) * 255
                # Suavizar y devolver
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
                return mask
        return np.zeros_like(base)
    
    def extract_roi_from_mask(self, bgr: np.ndarray, mask: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
        """Devuelve ROI recortada y bounding box (x,y,w,h)"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < self.min_roi_area:
            return None, None
        
        x, y, w, h = cv2.boundingRect(largest)
        # Padding
        x0 = max(0, x - self.roi_pad)
        y0 = max(0, y - self.roi_pad)
        x1 = min(bgr.shape[1], x + w + self.roi_pad)
        y1 = min(bgr.shape[0], y + h + self.roi_pad)
        roi = bgr[y0:y1, x0:x1].copy()
        
        return roi, (x0, y0, x1-x0, y1-y0)
    
    def preprocess_for_model(self, roi: np.ndarray) -> np.ndarray:
        """Normaliza ROI y la deja con shape (1, C, H, W)"""
        img = cv2.resize(roi, (224, 224))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img = (img - self.mean) / self.std
        img = np.transpose(img, (2, 0, 1)).astype(np.float32)
        img = np.expand_dims(img, 0)
        return img
    
    def predict_model_on_roi(self, roi: np.ndarray) -> Tuple[Optional[str], Optional[float]]:
        """Devuelve (label, conf). label = 'buena'|'mala'"""
        if not self.has_model:
            return None, None
        
        try:
            inp = self.preprocess_for_model(roi)
            out = self.session.run(None, {self.input_name: inp})[0]
            out = np.asarray(out)
            
            # Manejar softmax/logits o sigmoid
            if out.ndim == 2 and out.shape[1] >= 2:
                # Aplicar softmax numéricamente estable
                exps = np.exp(out - np.max(out, axis=1, keepdims=True))
                probs = exps / np.sum(exps, axis=1, keepdims=True)
                prob = float(probs[0].max())
                idx = int(probs[0].argmax())
                label = "buena" if idx == 0 else "mala"
                return label, prob
            else:
                # Salida 1D sigmoidea
                val = float(out.reshape(-1)[0])
                prob_spoiled = 1.0 / (1.0 + np.exp(-val))
                label = "mala" if prob_spoiled >= 0.5 else "buena"
                conf = prob_spoiled if label == "mala" else (1.0 - prob_spoiled)
                return label, conf
        except Exception as e:
            print(f"[ERROR] Error en predicción del modelo: {e}")
            return None, None
    
    def heuristica_on_roi(self, roi: np.ndarray) -> Tuple[str, float]:
        """Analiza ROI recortada; devuelve (label, score_between_0_1)"""
        if roi is None or roi.size == 0:
            return "desconocido", 0.0
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # Detectar manchas oscuras (umbral adaptable)
        _, dark = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
        dark_ratio = cv2.countNonZero(dark) / float(gray.size + 1e-9)
        # Detectar textural irregularity (laplacian variance)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Heurística combinada (valores empíricos; ajustar)
        score_spoiled = min(1.0, dark_ratio * 4.0 + (1.0 if lap_var < 50 else 0.0) * 0.3)
        label = "mala" if score_spoiled >= 0.4 else "buena"
        conf = 1.0 - score_spoiled if label == "buena" else score_spoiled
        return label, conf
    
    def fuse_labels(self, model_label: Optional[str], model_conf: Optional[float], 
                   heur_label: str, heur_conf: float) -> Tuple[str, float, str]:
        """Devuelve (final_label, final_conf, source)"""
        if model_label is None:
            return heur_label, heur_conf, "heuristica"
        
        # Preferir modelo, pero si coinciden, reforzar
        if model_label == heur_label:
            base_conf = (model_conf + heur_conf) / 2.0
            source = "ambos"
            final = model_label
        else:
            # Si modelo dice mala o alta confianza, priorizarlo
            base_conf = 0.7 * (model_conf if model_conf is not None else 0.6) + 0.3 * heur_conf
            source = "modelo" if (model_conf or 0) >= 0.6 else "mix"
            final = model_label
        
        return final, float(base_conf), source
    
    async def process_image(self, image: np.ndarray, filename: str) -> Dict[str, Any]:
        """Procesar imagen y devolver resultado completo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1) Extraer máscara y ROI candidata
        mask = self.mask_fruit_roi(image)
        roi, bbox = self.extract_roi_from_mask(image, mask)
        
        # 2) Clasificar si hay ROI válida
        model_label, model_conf = None, None
        heur_label, heur_conf = None, None
        
        if roi is not None:
            # Ejecutar heurística siempre
            heur_label, heur_conf = self.heuristica_on_roi(roi)
            # Ejecutar modelo si está disponible
            if self.has_model:
                model_label, model_conf = self.predict_model_on_roi(roi)
        else:
            # No ROI: no clasificar
            heur_label, heur_conf = "no_fruta", 0.0
        
        # 3) Fusionar resultados
        if model_label is None:
            if heur_label is None:
                final_label, final_conf, source = "no_fruta", 0.0, "none"
            else:
                final_label, final_conf, source = heur_label, heur_conf, "heuristica"
        else:
            final_label, final_conf, source = self.fuse_labels(
                model_label, model_conf, heur_label or model_label, heur_conf or (model_conf or 0.0)
            )
        
        # 4) Determinar tipo de fruta y estado
        is_fruit = final_label not in ["no_fruta", "desconocido"]
        fruit_type = "Manzana" if is_fruit else "No_Fruta"
        spoiled = final_label == "mala" if is_fruit else False
        
        # 5) Análisis adicional
        analysis_details = {}
        if bbox is not None:
            # Calcular circularidad
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                perimeter = cv2.arcLength(largest, True)
                if perimeter > 0:
                    circularity = 4.0 * np.pi * area / (perimeter * perimeter)
                    if circularity < self.circularity_min:
                        analysis_details["alert"] = f"ALERTA: Circularidad muy baja: {circularity:.2f} (mín: {self.circularity_min})"
        
        # 6) Guardar archivos
        file_paths = await self._save_detection_files(image, roi, mask, timestamp, filename)
        
        # 7) Crear resultado
        result = {
            "timestamp": timestamp,
            "classification": final_label,
            "confidence": final_conf,
            "is_fruit": is_fruit,
            "fruit_type": fruit_type,
            "spoiled": spoiled,
            "image_shape": list(image.shape),
            "analysis_details": analysis_details,
            "file_paths": file_paths
        }
        
        # 8) Actualizar estadísticas
        await self._update_stats(result)
        
        return result
    
    async def _save_detection_files(self, image: np.ndarray, roi: Optional[np.ndarray], 
                                  mask: np.ndarray, timestamp: str, filename: str) -> Dict[str, Optional[str]]:
        """Guardar archivos de la detección"""
        # Crear directorios
        results_dir = Path("salidas")
        masks_dir = results_dir / "masks"
        results_img_dir = results_dir / "results"
        metadata_dir = results_dir / "metadata"
        
        for dir_path in [results_dir, masks_dir, results_img_dir, metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Guardar imagen original
        original_path = results_img_dir / f"{timestamp}_{filename}"
        cv2.imwrite(str(original_path), image)
        
        # Guardar ROI si existe
        roi_path = None
        if roi is not None:
            roi_path = results_img_dir / f"{timestamp}_roi_{filename}"
            cv2.imwrite(str(roi_path), roi)
        
        # Guardar máscara
        mask_path = masks_dir / f"{timestamp}_mask_{filename}"
        cv2.imwrite(str(mask_path), mask)
        
        return {
            "original": str(original_path),
            "roi": str(roi_path) if roi_path else None,
            "mask": str(mask_path)
        }
    
    async def _update_stats(self, result: Dict[str, Any]):
        """Actualizar estadísticas con el nuevo resultado"""
        # Actualizar resumen
        self.stats["summary"]["total_detections"] += 1
        
        if result["is_fruit"]:
            self.stats["summary"]["total_fruits"] += 1
            fruit_type = result["fruit_type"]
            if fruit_type not in self.stats["summary"]["fruits_by_type"]:
                self.stats["summary"]["fruits_by_type"][fruit_type] = 0
            self.stats["summary"]["fruits_by_type"][fruit_type] += 1
            
            if result["spoiled"]:
                self.stats["summary"]["fruits_by_status"]["MALOGRADA"] += 1
            else:
                self.stats["summary"]["fruits_by_status"]["OK"] += 1
        else:
            self.stats["summary"]["total_non_fruits"] += 1
        
        # Calcular tasa de éxito (frutas buenas / total frutas)
        total_fruits = self.stats["summary"]["total_fruits"]
        if total_fruits > 0:
            good_fruits = self.stats["summary"]["fruits_by_status"]["OK"]
            self.stats["summary"]["success_rate"] = good_fruits / total_fruits
        
        # Agregar al historial
        history_entry = {
            "timestamp": result["timestamp"],
            "classification": result["classification"],
            "confidence": result["confidence"],
            "is_fruit": result["is_fruit"],
            "fruit_type": result["fruit_type"],
            "spoiled": result["spoiled"],
            "file_paths": result["file_paths"]
        }
        
        self.stats["detection_history"].append(history_entry)
        
        # Limitar historial a 1000 entradas
        if len(self.stats["detection_history"]) > 1000:
            self.stats["detection_history"] = self.stats["detection_history"][-1000:]
        
        # Guardar estadísticas
        self._save_stats()
