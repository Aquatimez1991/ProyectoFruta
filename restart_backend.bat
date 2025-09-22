@echo off
echo Reiniciando Backend de Deteccion de Manzanas...
echo.

cd ProyectoFruta

echo Deteniendo procesos existentes en puerto 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo Esperando 2 segundos...
timeout /t 2 /nobreak >nul

echo Activando entorno virtual...
call entorno_ia\Scripts\activate

echo Verificando dependencias...
python -c "import fastapi, uvicorn, cv2, onnxruntime, numpy" 2>nul
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

echo Verificando modelo ONNX...
if not exist "modelo_manzana.onnx" (
    echo ERROR: No se encontro el modelo modelo_manzana.onnx
    echo Asegurate de que el archivo existe en el directorio ProyectoFruta
    pause
    exit /b 1
)

echo.
echo Iniciando servidor backend en http://localhost:8000
echo Presiona Ctrl+C para detener el servidor
echo.

python app.py

pause
