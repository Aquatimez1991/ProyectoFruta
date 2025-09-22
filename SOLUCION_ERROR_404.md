# 🔧 Solución para Error 404 en /toggle_live

## 🚨 **Problema Identificado**
```
POST http://localhost:8000/toggle_live 404 (Not Found)
```

## ✅ **Soluciones Paso a Paso**

### **1. Reiniciar el Backend (Solución Principal)**

El error 404 indica que el endpoint no está disponible. Esto suele pasar cuando:
- El servidor no se reinició después de agregar nuevos endpoints
- Hay un error en el código que impide que el servidor arranque correctamente

**Solución:**
```bash
# Usar el script de reinicio automático
restart_backend.bat

# O manualmente:
# 1. Detener el backend (Ctrl+C)
# 2. Ejecutar de nuevo:
cd ProyectoFruta
entorno_ia\Scripts\activate
python app.py
```

### **2. Verificar que el Backend Esté Funcionando**

**Ejecutar diagnóstico:**
```bash
python diagnostico_api.py
```

**O probar manualmente en el navegador:**
- Abrir: `http://localhost:8000/health`
- Debería mostrar: `{"status":"healthy","model_loaded":true,...}`

### **3. Usar el Panel de Diagnóstico en la Interfaz**

1. Abrir el frontend en `http://localhost:3000`
2. Ir a la pestaña **"Subir Imagen"**
3. Hacer clic en **"Ejecutar Diagnóstico"**
4. Verificar que todos los endpoints estén en verde

### **4. Verificar Logs del Backend**

En la consola del backend deberías ver:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Si hay errores, aparecerán aquí.**

### **5. Verificar Archivos del Backend**

Asegúrate de que estos archivos existan y estén actualizados:
- `ProyectoFruta/app.py` (debe tener el endpoint `/toggle_live`)
- `ProyectoFruta/detection_service.py`
- `ProyectoFruta/modelo_manzana.onnx`

## 🔍 **Diagnóstico Detallado**

### **Verificar Endpoints Disponibles:**
```bash
# Probar cada endpoint individualmente
curl http://localhost:8000/health
curl http://localhost:8000/test
curl -X POST http://localhost:8000/toggle_live
```

### **Verificar CORS:**
El frontend en puerto 3000 debe poder comunicarse con el backend en puerto 8000.

### **Verificar Puerto:**
```bash
# Verificar que el puerto 8000 esté en uso
netstat -an | findstr :8000
```

## 🚀 **Pasos de Solución Rápida**

1. **Detener backend** (Ctrl+C en la consola)
2. **Ejecutar:** `restart_backend.bat`
3. **Verificar** que aparezca: `Uvicorn running on http://0.0.0.0:8000`
4. **Abrir frontend** en `http://localhost:3000`
5. **Ir a "Subir Imagen"** y ejecutar diagnóstico
6. **Probar funciones de cámara**

## 🎯 **Verificación Final**

Después de reiniciar, deberías poder:

1. **Ver en la consola del backend:**
   ```
   [INFO] Modelo ONNX cargado: modelo_manzana.onnx
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Ver en el frontend:**
   - Indicador verde: "Backend conectado"
   - Diagnóstico: Todos los endpoints en verde

3. **Probar funciones:**
   - MONITOREO: Debería activar sin errores
   - CAPTURAR: Debería procesar con el modelo real
   - LIVE: Debería toggle correctamente

## 🆘 **Si el Problema Persiste**

1. **Verificar versión de Python:**
   ```bash
   python --version
   # Debe ser 3.8 o superior
   ```

2. **Reinstalar dependencias:**
   ```bash
   cd ProyectoFruta
   entorno_ia\Scripts\activate
   pip install --upgrade -r requirements.txt
   ```

3. **Verificar que no haya otros servicios en puerto 8000:**
   ```bash
   netstat -ano | findstr :8000
   ```

4. **Revisar firewall/antivirus** que puedan estar bloqueando la conexión

---

**💡 La causa más común es que el backend no se reinició después de los cambios. Usa `restart_backend.bat` para solucionarlo.**
