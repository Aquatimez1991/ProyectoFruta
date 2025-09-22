@echo off
echo Iniciando Frontend de Deteccion de Manzanas...
echo.

cd InterfazMonitoreoManzanas

echo Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado
    echo Por favor instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

echo Verificando dependencias...
if not exist "node_modules" (
    echo Instalando dependencias...
    npm install
)

echo.
echo Iniciando servidor frontend en http://localhost:5173
echo Presiona Ctrl+C para detener el servidor
echo.

npm run dev

pause
