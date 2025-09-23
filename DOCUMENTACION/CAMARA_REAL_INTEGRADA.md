# 📹 Cámara Real Integrada - Sistema Completo

## 🎯 **Problema Solucionado**

Tu `detectar_fruta.py` tenía un loop principal que abría la cámara real con `cv2.VideoCapture(0)` y procesaba frames en tiempo real, pero el backend solo simulaba capturas. Ahora está **completamente integrado**.

## ✅ **Integración Completa Implementada**

### **1. CameraService - Loop Principal Real**

**Nuevo archivo:** `ProyectoFruta/camera_service.py`

**Funcionalidades integradas de `detectar_fruta.py`:**
- ✅ **`cv2.VideoCapture(0)`** - Abre cámara real
- ✅ **Loop principal** - Procesa frames continuamente
- ✅ **Detección ROI** - Extrae regiones de interés
- ✅ **Clasificación** - Usa modelo ONNX + heurística
- ✅ **Suavizado** - Votación y EMA como en el original
- ✅ **Teclas equivalentes** - `'c'`, `'l'`, `'s'` convertidas a endpoints

### **2. Endpoints de Cámara Real**

**Nuevos endpoints en el backend:**
```python
POST /camera/start     # Inicia cámara (equivale a abrir detectar_fruta.py)
POST /camera/stop      # Detiene cámara (equivale a 'q' para salir)
POST /capture          # Captura frame (equivale a 'c' para capturar)
POST /toggle_live      # Toggle live (equivale a 'l' para live on/off)
GET  /camera/status    # Estado de la cámara
```

### **3. Integración con Modelo ONNX**

**El CameraService usa:**
- ✅ **Mismo modelo ONNX** que tu script original
- ✅ **Misma heurística** de detección
- ✅ **Mismo suavizado** de resultados
- ✅ **Misma lógica** de fusión modelo + heurística

## 🚀 **Cómo Funciona Ahora**

### **Flujo Completo:**

1. **Backend inicia** → CameraService se inicializa
2. **Frontend se conecta** → Inicia cámara automáticamente
3. **Usuario hace clic en "MONITOREO"** → Activa modo live
4. **Loop de cámara procesa frames** → Igual que `detectar_fruta.py`
5. **Usuario hace clic en "CAPTURAR"** → Captura frame actual
6. **Resultado se muestra** → Con información real del modelo

### **Equivalencias con detectar_fruta.py:**

| Función Original | Endpoint API | Acción |
|------------------|--------------|---------|
| `cv2.VideoCapture(0)` | `POST /camera/start` | Inicia cámara |
| `'c'` (capturar) | `POST /capture` | Captura frame |
| `'l'` (live toggle) | `POST /toggle_live` | Toggle modo live |
| `'s'` (stats) | `GET /stats` | Estadísticas |
| `'q'` (salir) | `POST /camera/stop` | Detiene cámara |

## 🔧 **Archivos Creados/Modificados**

### **Backend:**
- `ProyectoFruta/camera_service.py` - **NUEVO** - Loop principal de cámara
- `ProyectoFruta/app.py` - Endpoints de cámara integrados

### **Frontend:**
- `InterfazMonitoreoManzanas/src/services/api.ts` - Nuevos endpoints
- `InterfazMonitoreoManzanas/src/App.tsx` - Inicio automático de cámara

## 🎮 **Uso del Sistema Completo**

### **1. Iniciar Sistema:**
```bash
# Terminal 1 - Backend (con cámara real)
restart_backend.bat

# Terminal 2 - Frontend
start_frontend.bat
```

### **2. Verificar Cámara:**
- El backend debería mostrar: `"Cámara 0 iniciada correctamente"`
- El frontend debería mostrar: `"✅ Cámara iniciada automáticamente"`

### **3. Usar Funciones:**
1. **Ir a pestaña "Cámara"**
2. **Hacer clic en "MONITOREO"** → Activa modo live real
3. **Hacer clic en "CAPTURAR"** → Captura frame de cámara real
4. **Ver resultados** → Del modelo ONNX real

## 📊 **Diferencias Antes vs Después**

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Cámara** | Simulada | Real (`cv2.VideoCapture(0)`) |
| **Loop** | No existía | Loop principal como `detectar_fruta.py` |
| **CAPTURAR** | Imagen estática | Frame real de cámara |
| **MONITOREO** | Simulación | Procesamiento en tiempo real |
| **Modelo** | Solo en subida | En cámara + subida |
| **ROI** | No | Detección real de regiones |

## 🔍 **Verificación de Funcionamiento**

### **En consola del backend deberías ver:**
```
[INFO] Modelo ONNX cargado: modelo_manzana.onnx
Cámara 0 iniciada correctamente
Loop de cámara iniciado
```

### **En consola del frontend deberías ver:**
```
✅ Cámara iniciada automáticamente
✅ Backend conectado: {status: "healthy", model_loaded: true}
```

### **Al usar las funciones:**
- **MONITOREO**: `"Modo live activado"`
- **CAPTURAR**: `"📸 Captura guardada: captura_YYYYMMDD_HHMMSS.jpg"`

## 🎉 **Resultado Final**

**¡Ahora tienes el sistema completo!**

- ✅ **Cámara real** funcionando como `detectar_fruta.py`
- ✅ **Loop principal** procesando frames continuamente
- ✅ **Modelo ONNX** funcionando en tiempo real
- ✅ **Interfaz web** conectada a la cámara real
- ✅ **Todas las funciones** equivalentes a las teclas originales

**El sistema ahora es una versión web completa de tu `detectar_fruta.py` con interfaz moderna y funcionalidad real de cámara.** 🚀

## 🆘 **Solución de Problemas**

### **Si la cámara no inicia:**
1. Verificar que no haya otra aplicación usando la cámara
2. Verificar permisos de cámara
3. Probar con `camera_index=1` si hay múltiples cámaras

### **Si hay errores de OpenCV:**
1. Verificar que `opencv-python` esté instalado
2. Reiniciar el backend
3. Verificar que la cámara esté conectada

---

**¡El sistema está completamente funcional con cámara real!** 📹✨
