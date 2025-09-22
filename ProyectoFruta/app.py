"""
API REST para detección de manzanas usando modelo ONNX
"""
import os
import json
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import aiofiles
import io

from detection_service import DetectionService
from camera_service import CameraService

# Configuración
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("salidas")
STATS_FILE = Path("detection_stats.json")

# Crear directorios si no existen
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Inicializar FastAPI
app = FastAPI(
    title="API Detección de Manzanas",
    description="API REST para detección y clasificación de manzanas usando modelo ONNX",
    version="1.0.0"
)

# Configurar CORS para permitir comunicación con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000"],  # Vite y otros puertos comunes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servicios
detection_service = DetectionService()
camera_service = CameraService()

# Configurar cámara con el servicio de detección
camera_service.set_detection_service(detection_service)

# Montar archivos estáticos para servir imágenes
app.mount("/static", StaticFiles(directory="salidas"), name="static")

# Modelos Pydantic para las respuestas
class DetectionResult(BaseModel):
    timestamp: str
    classification: str
    confidence: float
    is_fruit: bool
    fruit_type: str
    spoiled: bool
    image_shape: List[int]
    analysis_details: Dict[str, Any]
    file_paths: Dict[str, Optional[str]]

class StatsResponse(BaseModel):
    summary: Dict[str, Any]
    detection_history: List[Dict[str, Any]]
    last_updated: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificar estado del servicio"""
    return HealthResponse(
        status="healthy",
        model_loaded=detection_service.is_model_loaded(),
        timestamp=datetime.now().isoformat()
    )

@app.post("/detect", response_model=DetectionResult)
async def detect_fruit(file: UploadFile = File(...)):
    """
    Procesar imagen y devolver resultado de detección
    """
    try:
        # Validar tipo de archivo
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
        
        # Leer imagen
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="No se pudo procesar la imagen")
        
        # Procesar con el servicio de detección
        result = await detection_service.process_image(image, file.filename)
        
        return DetectionResult(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando imagen: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Obtener estadísticas de detección
    """
    try:
        if STATS_FILE.exists():
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            return StatsResponse(**stats_data)
        else:
            # Devolver estadísticas vacías si no existe el archivo
            return StatsResponse(
                summary={
                    "total_detections": 0,
                    "total_fruits": 0,
                    "total_non_fruits": 0,
                    "fruits_by_type": {},
                    "fruits_by_status": {"OK": 0, "MALOGRADA": 0},
                    "success_rate": 0.0
                },
                detection_history=[],
                last_updated=datetime.now().isoformat()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.get("/history")
async def get_detection_history(limit: int = 50):
    """
    Obtener historial de detecciones
    """
    try:
        if STATS_FILE.exists():
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            
            history = stats_data.get("detection_history", [])
            # Limitar resultados
            if limit > 0:
                history = history[-limit:]
            
            return {"history": history, "total": len(stats_data.get("detection_history", []))}
        else:
            return {"history": [], "total": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@app.delete("/stats")
async def reset_stats():
    """
    Resetear estadísticas
    """
    try:
        # Crear estadísticas vacías
        empty_stats = {
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
        
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(empty_stats, f, indent=2, ensure_ascii=False)
        
        return {"message": "Estadísticas reseteadas correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reseteando estadísticas: {str(e)}")

@app.post("/capture")
async def capture_and_detect():
    """
    Capturar frame actual de la cámara y procesar
    """
    try:
        # Usar el servicio de cámara real
        result = camera_service.capture_frame()
        
        if result is None:
            raise HTTPException(status_code=400, detail="No se pudo capturar frame de la cámara")
        
        return DetectionResult(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en captura: {str(e)}")

@app.post("/toggle_live")
async def toggle_live_mode():
    """
    Toggle modo live de la cámara
    """
    try:
        is_live = camera_service.toggle_live()
        return {
            "message": f"Modo live {'activado' if is_live else 'desactivado'}", 
            "is_live": is_live,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling live mode: {str(e)}")

@app.post("/camera/start")
async def start_camera():
    """
    Iniciar la cámara
    """
    try:
        success = camera_service.start_camera()
        if success:
            return {"message": "Cámara iniciada correctamente", "status": "started"}
        else:
            raise HTTPException(status_code=500, detail="No se pudo iniciar la cámara")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando cámara: {str(e)}")

@app.post("/camera/stop")
async def stop_camera():
    """
    Detener la cámara
    """
    try:
        camera_service.stop_camera()
        return {"message": "Cámara detenida correctamente", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deteniendo cámara: {str(e)}")

@app.get("/camera/status")
async def camera_status():
    """
    Obtener estado de la cámara
    """
    return {
        "is_running": camera_service.is_running,
        "is_live": camera_service.is_live,
        "frame_count": camera_service.frame_idx,
        "has_latest_frame": camera_service.latest_frame is not None,
        "has_latest_result": camera_service.latest_result is not None
    }

@app.get("/test")
async def test_endpoint():
    """
    Endpoint de prueba para verificar que la API funciona
    """
    return {
        "status": "ok", 
        "message": "API funcionando correctamente",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": detection_service.is_model_loaded(),
        "camera_running": camera_service.is_running
    }

@app.get("/video_stream")
async def video_stream():
    """
    Stream de video en tiempo real desde la cámara
    """
    def generate_frames():
        while camera_service.is_running:
            frame = camera_service.get_latest_frame()
            if frame is not None:
                # Codificar frame como JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control de FPS
            import time
            time.sleep(0.033)  # ~30 FPS
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/latest_image")
async def get_latest_image():
    """
    Obtener la imagen más reciente procesada
    """
    try:
        # Buscar la imagen más reciente en salidas/results
        results_dir = RESULTS_DIR / "results"
        if not results_dir.exists():
            raise HTTPException(status_code=404, detail="No hay imágenes procesadas")
        
        # Obtener archivos de imagen ordenados por fecha de modificación
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(results_dir.glob(ext))
        
        if not image_files:
            raise HTTPException(status_code=404, detail="No hay imágenes procesadas")
        
        # Ordenar por fecha de modificación (más reciente primero)
        latest_image = max(image_files, key=lambda x: x.stat().st_mtime)
        
        return FileResponse(
            path=str(latest_image),
            media_type="image/jpeg",
            filename=latest_image.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo imagen: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
