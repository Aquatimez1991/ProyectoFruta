# 🍎 Instrucciones de Uso - Sistema de Detección de Manzanas

## 🚀 Inicio Rápido

### 1. Iniciar Backend
```bash
# Opción 1: Script automático
start_backend.bat

# Opción 2: Manual
cd ProyectoFruta
entorno_ia\Scripts\activate
python app.py
```

**Verificar que aparezca:**
```
[INFO] Modelo ONNX cargado: modelo_manzana.onnx
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Iniciar Frontend
```bash
# Opción 1: Script automático
start_frontend.bat

# Opción 2: Manual
cd InterfazMonitoreoManzanas
npm run dev
```

**Verificar que aparezca:**
```
VITE v6.3.6  ready in XXX ms
➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

## 🎯 Uso de las Funciones

### 📸 **Subir Imagen** (Nueva funcionalidad)
1. Abrir navegador en `http://localhost:3000`
2. Hacer clic en **"Subir Imagen"** en el sidebar (icono de upload)
3. Arrastrar una imagen o hacer clic para seleccionar
4. Hacer clic en **"Analizar Imagen"**
5. Ver resultados detallados del modelo de IA

### 📹 **Funciones de Cámara** (Ahora conectadas al backend)

#### **MONITOREO**
- Hacer clic en **"MONITOREO"** en la parte inferior
- Esto activa el modo live y se conecta al backend
- Verás el mensaje: *"Modo LIVE activo: Usando modelo de IA del backend"*

#### **CAPTURAR**
- Con el modo LIVE activo, hacer clic en **"CAPTURAR"**
- Esto usa el modelo de IA real del backend
- Procesa una imagen de prueba (`ejemplo.jpg` o `ejemplo1.jpg`)

#### **LIVE**
- Hacer clic en **"LIVE"** para activar/desactivar
- Cuando está activo, usa el backend para detección
- Muestra indicadores visuales del estado de conexión

## 🔧 **Verificación de Conexión**

### Indicadores Visuales en la Interfaz:

1. **En pestaña "Subir Imagen":**
   - ✅ Verde: *"Backend conectado: Modelo cargado y listo"*
   - ❌ Rojo: *"Backend no disponible"*

2. **En pestaña "Cámara":**
   - **Modo Manual:** *"Backend conectado: Las funciones de cámara usarán el modelo de IA real"*
   - **Modo LIVE:** *"Modo LIVE activo: Usando modelo de IA del backend"*

### Prueba de Conexión:
```bash
# Ejecutar script de prueba
python test_integration.py
```

## 🐛 **Solución de Problemas**

### Backend no responde:
1. Verificar que el entorno virtual esté activado
2. Comprobar que `modelo_manzana.onnx` existe
3. Revisar que el puerto 8000 esté libre

### Frontend no se conecta:
1. Verificar que el backend esté en puerto 8000
2. Comprobar que el frontend esté en puerto 3000
3. Revisar configuración CORS

### Funciones de cámara no funcionan:
1. Asegurarse de que el backend esté ejecutándose
2. Verificar que aparezca el indicador verde de conexión
3. Comprobar que `ejemplo.jpg` o `ejemplo1.jpg` existan en `ProyectoFruta/`

## 📊 **Diferencias con detectar_fruta.py**

| Función | detectar_fruta.py | Interfaz Web |
|---------|-------------------|--------------|
| **Captura** | `cv2.VideoCapture(0)` | Endpoint `/capture` |
| **Teclas** | `'c'` para capturar | Botón "CAPTURAR" |
| **Live** | `'l'` para toggle | Botón "LIVE" |
| **Stats** | `'s'` para stats | Pestaña "Estadísticas" |
| **Salida** | `'q'` para salir | Botón "SALIR" |

## 🎮 **Controles Equivalentes**

### Teclas del script original → Botones de la interfaz:
- **`'c'` (capturar)** → **"CAPTURAR"**
- **`'l'` (live on/off)** → **"LIVE"**
- **`'s'` (stats)** → **Pestaña "Estadísticas"**
- **`'q'` (salir)** → **"SALIR"**

### Funcionalidades adicionales:
- **Subida de archivos** (nueva)
- **Visualización de resultados** (mejorada)
- **Estadísticas en tiempo real** (nueva)
- **Historial de detecciones** (nueva)

## 🔄 **Flujo de Trabajo Recomendado**

1. **Iniciar ambos servicios** (backend + frontend)
2. **Verificar conexión** (indicadores verdes)
3. **Probar subida de imagen** (pestaña "Subir Imagen")
4. **Activar modo LIVE** (botón "MONITOREO")
5. **Capturar imágenes** (botón "CAPTURAR")
6. **Revisar estadísticas** (pestaña "Estadísticas")

## 📝 **Notas Importantes**

- El backend debe estar ejecutándose **antes** de usar las funciones de cámara
- Las imágenes se procesan usando el **mismo modelo ONNX** que `detectar_fruta.py`
- Los resultados se guardan automáticamente en `ProyectoFruta/salidas/`
- La interfaz web funciona en **puerto 3000** (no 5173 como en la documentación original)

---

**¡El sistema está listo para usar! 🎉**
