"""
Servicio de cámara que integra la funcionalidad de detectar_fruta.py
"""
import cv2
import numpy as np
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict, Any
import json
from pathlib import Path

class CameraService:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.is_live = False
        self.frame_idx = 0
        self.camera_thread = None
        self.latest_frame = None
        self.latest_result = None
        self.callbacks = []
        
        # Configuración del loop principal (igual que detectar_fruta.py)
        self.frame_skip_for_model = 3
        self.roi_pad = 10
        self.min_roi_area = 1500
        self.circularity_min = 0.02
        self.smooth_window = 5
        self.ema_alpha = 0.5
        
        # Normalización
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        
        # Suavizado (igual que detectar_fruta.py)
        self.label_window = []
        self.conf_ema = None
        
        # Estadísticas
        self.stats = {"capturas_total": 0, "buena": 0, "mala": 0}
        
        # Control de actualización de estadísticas en modo live
        self.last_live_classification = None
        self.live_classification_count = 0
        self.detection_history = []
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Agregar callback para recibir resultados"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remover callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def notify_callbacks(self, result: Dict[str, Any]):
        """Notificar a todos los callbacks"""
        for callback in self.callbacks:
            try:
                callback(result)
            except Exception as e:
                print(f"Error en callback: {e}")
    
    def start_camera(self, camera_index: int = 0) -> bool:
        """Iniciar la cámara (igual que detectar_fruta.py)"""
        try:
            # Si la cámara ya está corriendo, no hacer nada
            if self.is_running and self.cap and self.cap.isOpened():
                print(f"Cámara {camera_index} ya está corriendo")
                return True
            
            # Si hay una cámara anterior, limpiarla primero
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # Esperar un poco antes de reiniciar
            import time
            time.sleep(0.5)
            
            # Crear nueva instancia de cámara
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                print(f"No se pudo abrir la cámara {camera_index}")
                return False
            
            # Configurar resolución
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            self.is_running = True
            self.is_live = False  # Empezar en modo manual
            self.frame_idx = 0
            self.latest_frame = None
            self.latest_result = None
            
            # Iniciar thread del loop principal
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()
            
            print(f"Cámara {camera_index} iniciada correctamente")
            return True
            
        except Exception as e:
            print(f"Error iniciando cámara: {e}")
            return False
    
    def stop_camera(self):
        """Detener la cámara"""
        self.is_running = False
        self.is_live = False
        
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        print("Cámara detenida")
    
    def toggle_live(self) -> bool:
        """Toggle modo live (igual que tecla 'l' en detectar_fruta.py)"""
        # Si la cámara no está corriendo, intentar iniciarla
        if not self.is_running:
            print("Cámara no está corriendo, intentando iniciar...")
            if not self.start_camera():
                print("No se pudo iniciar la cámara")
                return False
        
        self.is_live = not self.is_live
        print(f"Modo live: {'ON' if self.is_live else 'OFF'}")
        return self.is_live
    
    def capture_frame(self) -> Optional[Dict[str, Any]]:
        """Capturar frame actual (igual que tecla 'c' en detectar_fruta.py)"""
        # Si la cámara no está corriendo, intentar iniciarla
        if not self.is_running:
            print("Cámara no está corriendo, intentando iniciar...")
            if not self.start_camera():
                print("No se pudo iniciar la cámara")
                return None
        
        if self.latest_frame is None:
            print("No hay frame disponible para capturar")
            return None
        
        # Procesar frame actual
        result = self._process_frame(self.latest_frame, force_capture=True)
        
        if result:
            # Guardar captura
            self._save_capture(self.latest_frame, result)
            
            # Actualizar estadísticas usando el DetectionService si está disponible
            if hasattr(self, 'detection_service') and self.detection_service:
                # Usar el DetectionService para actualizar estadísticas del archivo JSON
                import asyncio
                try:
                    # Crear un loop de evento si no existe
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Ejecutar la actualización de estadísticas
                    loop.run_until_complete(self.detection_service._update_stats(result))
                except Exception as e:
                    print(f"Error actualizando estadísticas: {e}")
            
            # También actualizar estadísticas locales para compatibilidad
            self.stats["capturas_total"] += 1
            if result.get("is_fruit"):
                if result.get("spoiled"):
                    self.stats["mala"] += 1
                else:
                    self.stats["buena"] += 1
        
        return result
    
    def _update_stats_for_live_mode(self, result: Dict[str, Any]):
        """Actualizar estadísticas en modo live usando DetectionService"""
        current_classification = result.get("classification", "")
        
        # Solo actualizar estadísticas si hay un cambio significativo en la clasificación
        # o si es la primera clasificación
        if (self.last_live_classification != current_classification and 
            current_classification not in ["no_fruta", "desconocido"]):
            
            self.last_live_classification = current_classification
            self.live_classification_count += 1
            
            # Actualizar estadísticas usando DetectionService
            if hasattr(self, 'detection_service') and self.detection_service:
                import asyncio
                try:
                    # Crear un loop de evento si no existe
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Ejecutar la actualización de estadísticas
                    loop.run_until_complete(self.detection_service._update_stats(result))
                    print(f"📊 Estadísticas actualizadas en modo live: {current_classification}")
                except Exception as e:
                    print(f"Error actualizando estadísticas en modo live: {e}")
            
            # También actualizar estadísticas locales para compatibilidad
            if result.get("is_fruit"):
                if result.get("spoiled"):
                    self.stats["mala"] += 1
                else:
                    self.stats["buena"] += 1
            self.stats["capturas_total"] += 1
    
    def _create_display_frame(self, frame: np.ndarray, mask: np.ndarray, bbox: Optional[tuple], 
                             final_label: str, final_conf: float, source: str) -> np.ndarray:
        """Crear frame con overlay visual (igual que detectar_fruta.py)"""
        display = frame.copy()
        
        # 1) Overlay de máscara (transparente)
        if mask is not None and mask.any():
            mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            display = cv2.addWeighted(display, 1.0, mask_color, 0.25, 0)
        
        # 2) Bounding box y texto de clasificación
        if bbox is not None:
            x, y, w, h = bbox
            
            # Color del bounding box según clasificación
            if "buena" in final_label:
                color = (0, 255, 0)  # Verde para buena
            elif "mala" in final_label:
                color = (0, 0, 255)  # Rojo para mala
            else:
                color = (255, 255, 0)  # Amarillo para otros
            
            # Dibujar bounding box
            cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
            
            # Texto de clasificación
            text = f"{final_label} ({source}) {final_conf:.2f}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_x = x
            text_y = max(15, y - 10)
            
            # Fondo para el texto
            cv2.rectangle(display, (text_x, text_y - text_size[1] - 5), 
                         (text_x + text_size[0] + 5, text_y + 5), color, -1)
            
            # Texto
            cv2.putText(display, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 3) Instrucciones (igual que detectar_fruta.py)
        instructions = "Presiona 'c' capturar | 's' stats | 'q' salir | 'l' live on/off"
        cv2.putText(display, instructions, (10, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return display
    
    def _camera_loop(self):
        """Loop principal de la cámara (igual que detectar_fruta.py)"""
        print("Loop de cámara iniciado")
        
        while self.is_running:
            if not self.cap:
                break
                
            ret, frame = self.cap.read()
            if not ret:
                print("Error leyendo frame de la cámara")
                break
            
            self.frame_idx += 1
            self.latest_frame = frame.copy()
            
            # Procesar frame si está en modo live
            if self.is_live:
                result = self._process_frame(frame)
                if result:
                    self.latest_result = result
                    self.notify_callbacks(result)
                    
                    # Actualizar estadísticas también en modo live
                    self._update_stats_for_live_mode(result)
            
            # Control de FPS (igual que detectar_fruta.py)
            time.sleep(0.033)  # ~30 FPS
        
        print("Loop de cámara terminado")
    
    def _process_frame(self, frame: np.ndarray, force_capture: bool = False) -> Optional[Dict[str, Any]]:
        """Procesar frame (igual que detectar_fruta.py)"""
        try:
            # 1) Extraer máscara y ROI candidata
            mask = self._mask_fruit_roi(frame)
            roi, bbox = self._extract_roi_from_mask(frame, mask)
            
            # 2) Decidir si clasificar
            model_label, model_conf = None, None
            heur_label, heur_conf = None, None
            
            if roi is not None:
                # Ejecutar heurística siempre
                heur_label, heur_conf = self._heuristica_on_roi(roi)
                
                # Ejecutar modelo cada N frames o si es captura forzada
                if force_capture or (self.frame_idx % self.frame_skip_for_model == 0):
                    if hasattr(self, 'detection_service') and self.detection_service:
                        model_label, model_conf = self._predict_model_on_roi_with_service(roi)
                    else:
                        model_label, model_conf = self._predict_model_on_roi(roi)
            else:
                heur_label, heur_conf = "no_fruta", 0.0
            
            # 3) Fusionar resultados
            if model_label is None:
                if heur_label is None:
                    final_label, final_conf, source = "no_fruta", 0.0, "none"
                else:
                    final_label, final_conf, source = heur_label, heur_conf, "heuristica"
            else:
                final_label, final_conf, source = self._fuse_labels(
                    model_label, model_conf, heur_label or model_label, heur_conf or (model_conf or 0.0)
                )
            
            # 4) Crear resultado
            is_fruit = final_label not in ["no_fruta", "desconocido"]
            fruit_type = "Manzana" if is_fruit else "No_Fruta"
            spoiled = final_label == "mala" if is_fruit else False
            
            # Crear frame con overlay visual (igual que detectar_fruta.py)
            display_frame = self._create_display_frame(frame, mask, bbox, final_label, final_conf, source)
            
            result = {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "classification": final_label,
                "confidence": final_conf,
                "is_fruit": is_fruit,
                "fruit_type": fruit_type,
                "spoiled": spoiled,
                "image_shape": list(frame.shape),
                "analysis_details": {},
                "file_paths": {
                    "original": None,
                    "roi": None,
                    "mask": None
                },
                "bbox": bbox,
                "source": source,
                "display_frame": display_frame  # Frame con overlay visual
            }
            
            return result
            
        except Exception as e:
            print(f"Error procesando frame: {e}")
            return None
    
    def _mask_fruit_roi(self, bgr: np.ndarray) -> np.ndarray:
        """Segmentación por color+morfología (igual que detectar_fruta.py)"""
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        sat_cond = s > 35
        not_too_bright = v < 245
        not_too_dark = v > 20

        base = (sat_cond & not_too_bright & not_too_dark).astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        base = cv2.morphologyEx(base, cv2.MORPH_OPEN, kernel, iterations=1)
        base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, kernel, iterations=1)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(base, connectivity=8)
        if num_labels <= 1:
            return np.zeros_like(base)

        areas = stats[1:, cv2.CC_STAT_AREA]
        idx_sorted = np.argsort(-areas)
        for idx in idx_sorted:
            area = int(areas[idx])
            if area >= self.min_roi_area:
                comp_idx = idx + 1
                mask = (labels == comp_idx).astype(np.uint8) * 255
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
                return mask
        return np.zeros_like(base)
    
    def _extract_roi_from_mask(self, bgr: np.ndarray, mask: np.ndarray):
        """Extraer ROI (igual que detectar_fruta.py)"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < self.min_roi_area:
            return None, None
        
        x, y, w, h = cv2.boundingRect(largest)
        x0 = max(0, x - self.roi_pad)
        y0 = max(0, y - self.roi_pad)
        x1 = min(bgr.shape[1], x + w + self.roi_pad)
        y1 = min(bgr.shape[0], y + h + self.roi_pad)
        roi = bgr[y0:y1, x0:x1].copy()
        
        return roi, (x0, y0, x1-x0, y1-y0)
    
    def _heuristica_on_roi(self, roi: np.ndarray):
        """Heurística (igual que detectar_fruta.py)"""
        if roi is None or roi.size == 0:
            return "desconocido", 0.0
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, dark = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
        dark_ratio = cv2.countNonZero(dark) / float(gray.size + 1e-9)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        score_spoiled = min(1.0, dark_ratio * 4.0 + (1.0 if lap_var < 50 else 0.0) * 0.3)
        label = "mala" if score_spoiled >= 0.4 else "buena"
        conf = 1.0 - score_spoiled if label == "buena" else score_spoiled
        return label, conf
    
    def _predict_model_on_roi(self, roi: np.ndarray):
        """Predicción del modelo (igual que detectar_fruta.py)"""
        # Esta función se implementará cuando se integre con DetectionService
        # Por ahora devolver None para usar solo heurística
        return None, None
    
    def set_detection_service(self, detection_service):
        """Configurar el servicio de detección para usar el modelo ONNX"""
        self.detection_service = detection_service
    
    def _predict_model_on_roi_with_service(self, roi: np.ndarray):
        """Predicción usando el DetectionService"""
        if not hasattr(self, 'detection_service') or not self.detection_service:
            return None, None
        
        try:
            return self.detection_service.predict_model_on_roi(roi)
        except Exception as e:
            print(f"Error en predicción del modelo: {e}")
            return None, None
    
    def _fuse_labels(self, model_label: Optional[str], model_conf: Optional[float], 
                    heur_label: str, heur_conf: float):
        """Fusionar etiquetas (igual que detectar_fruta.py)"""
        if model_label is None:
            return heur_label, heur_conf, "heuristica"
        
        if model_label == heur_label:
            base_conf = (model_conf + heur_conf) / 2.0
            source = "ambos"
            final = model_label
        else:
            base_conf = 0.7 * (model_conf if model_conf is not None else 0.6) + 0.3 * heur_conf
            source = "modelo" if (model_conf or 0) >= 0.6 else "mix"
            final = model_label
        
        return final, float(base_conf), source
    
    def _save_capture(self, frame: np.ndarray, result: Dict[str, Any]):
        """Guardar captura (igual que detectar_fruta.py)"""
        try:
            timestamp = result["timestamp"]
            
            # Crear directorios
            results_dir = Path("salidas/results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar frame
            filename = f"captura_{timestamp}.jpg"
            filepath = results_dir / filename
            cv2.imwrite(str(filepath), frame)
            
            # Actualizar resultado con ruta del archivo
            result["file_paths"]["original"] = str(filepath)
            
            # Agregar al historial
            self.detection_history.append({
                "timestamp": timestamp,
                "classification": result["classification"],
                "confidence": result["confidence"],
                "is_fruit": result["is_fruit"],
                "fruit_type": result["fruit_type"],
                "spoiled": result["spoiled"],
                "file_paths": result["file_paths"]
            })
            
            print(f"📸 Captura guardada: {filename}")
            
        except Exception as e:
            print(f"Error guardando captura: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {
            "summary": {
                "total_detections": self.stats["capturas_total"],
                "total_fruits": self.stats["buena"] + self.stats["mala"],
                "total_non_fruits": 0,  # Se puede calcular
                "fruits_by_type": {"Manzana": self.stats["buena"] + self.stats["mala"]},
                "fruits_by_status": {"OK": self.stats["buena"], "MALOGRADA": self.stats["mala"]},
                "success_rate": self.stats["buena"] / max(1, self.stats["buena"] + self.stats["mala"])
            },
            "detection_history": self.detection_history,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Obtener el frame más reciente"""
        return self.latest_frame
    
    def get_latest_display_frame(self) -> Optional[np.ndarray]:
        """Obtener el frame más reciente con overlay visual"""
        if self.latest_result and 'display_frame' in self.latest_result:
            return self.latest_result['display_frame']
        return self.latest_frame
    
    def get_latest_result(self) -> Optional[Dict[str, Any]]:
        """Obtener el resultado más reciente"""
        return self.latest_result
