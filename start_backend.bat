@echo off
echo Iniciando Backend de Deteccion de Manzanas...
echo.

cd ProyectoFruta

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
