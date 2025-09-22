# Sistema de Detección de Manzanas con IA

Este proyecto implementa un sistema completo de detección y clasificación de manzanas usando inteligencia artificial, con un backend API REST y un frontend web moderno.

## 🏗️ Arquitectura del Sistema

El proyecto está dividido en dos partes principales:

### Backend (ProyectoFruta/)
- **API REST** con FastAPI para procesamiento de imágenes
- **Modelo ONNX** para clasificación de manzanas (buena/mala)
- **Servicio de detección** que combina IA y heurísticas
- **Almacenamiento** de resultados y estadísticas en JSON

### Frontend (InterfazMonitoreoManzanas/)
- **Aplicación React + Vite** con interfaz moderna
- **Componentes UI** usando Radix UI y Tailwind CSS
- **Integración con API** para subir imágenes y mostrar resultados
- **Visualización** de estadísticas y resultados en tiempo real

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- Node.js 16+
- npm o yarn

### Backend

1. **Navegar al directorio del backend:**
   ```bash
   cd ProyectoFruta
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv entorno_ia
   ```

3. **Activar entorno virtual:**
   ```bash
   # Windows
   entorno_ia\Scripts\activate
   
   # Linux/Mac
   source entorno_ia/bin/activate
   ```

4. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verificar que el modelo ONNX existe:**
   ```bash
   # El archivo modelo_manzana.onnx debe estar en el directorio
   ls -la modelo_manzana.onnx
   ```

6. **Iniciar el servidor:**
   ```bash
   python app.py
   ```

   El backend estará disponible en: `http://localhost:8000`

### Frontend

1. **Navegar al directorio del frontend:**
   ```bash
   cd InterfazMonitoreoManzanas
   ```

2. **Instalar dependencias:**
   ```bash
   npm install
   ```

3. **Iniciar el servidor de desarrollo:**
   ```bash
   npm run dev
   ```

   El frontend estará disponible en: `http://localhost:5173`

## 📡 API Endpoints

### Backend API (FastAPI)

#### `GET /health`
Verificar estado del servicio y modelo.

**Respuesta:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-01-20T10:30:00"
}
```

#### `POST /detect`
Procesar imagen y obtener resultado de detección.

**Parámetros:**
- `file`: Archivo de imagen (multipart/form-data)

**Respuesta:**
```json
{
  "timestamp": "20250120_103000",
  "classification": "buena",
  "confidence": 0.95,
  "is_fruit": true,
  "fruit_type": "Manzana",
  "spoiled": false,
  "image_shape": [720, 1280, 3],
  "analysis_details": {},
  "file_paths": {
    "original": "salidas/results/20250120_103000_image.jpg",
    "roi": "salidas/results/20250120_103000_roi_image.jpg",
    "mask": "salidas/masks/20250120_103000_mask_image.jpg"
  }
}
```

#### `GET /stats`
Obtener estadísticas de detección.

**Respuesta:**
```json
{
  "summary": {
    "total_detections": 150,
    "total_fruits": 120,
    "total_non_fruits": 30,
    "fruits_by_type": {"Manzana": 120},
    "fruits_by_status": {"OK": 90, "MALOGRADA": 30},
    "success_rate": 0.75
  },
  "detection_history": [...],
  "last_updated": "2025-01-20T10:30:00"
}
```

#### `GET /history?limit=50`
Obtener historial de detecciones.

#### `DELETE /stats`
Resetear estadísticas.

## 🎯 Flujo de Trabajo

### 1. Inicio del Sistema
```bash
# Terminal 1 - Backend
cd ProyectoFruta
entorno_ia\Scripts\activate
python app.py

# Terminal 2 - Frontend
cd InterfazMonitoreoManzanas
npm run dev
```

### 2. Uso de la Aplicación

1. **Abrir navegador** en `http://localhost:5173`
2. **Verificar conexión** - El frontend mostrará el estado del backend
3. **Navegar a "Subir Imagen"** desde el sidebar
4. **Arrastrar o seleccionar** una imagen de manzana
5. **Hacer clic en "Analizar Imagen"**
6. **Ver resultados** de clasificación y análisis
7. **Consultar estadísticas** en la pestaña correspondiente

### 3. Procesamiento de Imágenes

El sistema procesa las imágenes en las siguientes etapas:

1. **Segmentación**: Detecta regiones de interés (ROI) usando análisis de color
2. **Extracción**: Recorta la región de la manzana
3. **Clasificación IA**: Usa el modelo ONNX para clasificar (buena/mala)
4. **Heurística**: Aplica análisis adicional (manchas, textura)
5. **Fusión**: Combina resultados de IA y heurística
6. **Almacenamiento**: Guarda resultados y actualiza estadísticas

## 🔧 Configuración Avanzada

### Parámetros del Modelo
En `detection_service.py` puedes ajustar:

```python
# Configuración de detección
ROI_PAD = 10                 # padding alrededor de ROI
MIN_ROI_AREA = 1500          # área mínima para ROI válida
CIRCULARITY_MIN = 0.02       # circularidad mínima
```

### Normalización de Imágenes
```python
# Ajustar según tu entrenamiento
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
```

### CORS y Puertos
En `app.py`:
```python
# Configurar CORS para otros puertos
allow_origins=["http://localhost:5173", "http://localhost:3000"]
```

## 📊 Estructura de Datos

### Resultado de Detección
```typescript
interface DetectionResult {
  timestamp: string;           // YYYYMMDD_HHMMSS
  classification: string;      // "buena" | "mala" | "no_fruta"
  confidence: number;          // 0.0 - 1.0
  is_fruit: boolean;          // Si se detectó fruta
  fruit_type: string;         // "Manzana" | "No_Fruta"
  spoiled: boolean;           // Si está malograda
  image_shape: number[];      // [height, width, channels]
  analysis_details: object;   // Alertas y detalles adicionales
  file_paths: {               // Rutas de archivos generados
    original: string;
    roi: string | null;
    mask: string | null;
  };
}
```

### Estadísticas
```typescript
interface StatsResponse {
  summary: {
    total_detections: number;
    total_fruits: number;
    total_non_fruits: number;
    fruits_by_type: Record<string, number>;
    fruits_by_status: { OK: number; MALOGRADA: number };
    success_rate: number;
  };
  detection_history: DetectionResult[];
  last_updated: string;
}
```

## 🐛 Solución de Problemas

### Backend no responde
1. Verificar que el entorno virtual esté activado
2. Comprobar que todas las dependencias estén instaladas
3. Verificar que el modelo ONNX existe y es válido
4. Revisar logs en la consola

### Frontend no se conecta al backend
1. Verificar que el backend esté ejecutándose en puerto 8000
2. Comprobar configuración CORS en `app.py`
3. Verificar que no haya firewall bloqueando la conexión

### Errores de procesamiento de imágenes
1. Verificar formato de imagen (JPG, PNG, GIF)
2. Comprobar tamaño de archivo (máximo 10MB)
3. Revisar logs del backend para errores específicos

### Modelo no carga
1. Verificar que `modelo_manzana.onnx` existe
2. Comprobar permisos de lectura del archivo
3. Verificar que onnxruntime esté instalado correctamente

## 📁 Estructura de Archivos

```
ProyectoFruta/
├── app.py                    # API FastAPI principal
├── detection_service.py      # Servicio de detección
├── requirements.txt          # Dependencias Python
├── modelo_manzana.onnx       # Modelo entrenado
├── salidas/                  # Resultados generados
│   ├── results/             # Imágenes procesadas
│   ├── masks/               # Máscaras generadas
│   └── metadata/            # Metadatos JSON
└── dataset/                 # Dataset de entrenamiento

InterfazMonitoreoManzanas/
├── src/
│   ├── services/
│   │   └── api.ts           # Servicio de API
│   ├── components/
│   │   ├── ImageUpload.tsx  # Componente de subida
│   │   ├── DetectionResults.tsx # Resultados
│   │   └── ...              # Otros componentes
│   └── App.tsx              # Componente principal
├── package.json             # Dependencias Node.js
└── vite.config.ts           # Configuración Vite
```

## 🔮 Próximas Mejoras

- [ ] Soporte para múltiples tipos de frutas
- [ ] Interfaz de cámara en tiempo real
- [ ] Base de datos SQLite para persistencia
- [ ] Autenticación y usuarios
- [ ] API de administración
- [ ] Exportación de reportes
- [ ] Notificaciones en tiempo real
- [ ] Optimización de rendimiento

## 📝 Licencia

Este proyecto es de uso educativo y de investigación.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**Desarrollado con ❤️ usando Python, FastAPI, React y TypeScript**
