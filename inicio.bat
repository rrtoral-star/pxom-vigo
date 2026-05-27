@echo off
chcp 65001 >nul
echo ================================================================================
echo PXOM-SOLO - Sistema de Consulta de Normativa Urbanística
echo ================================================================================
echo.

REM Activar entorno virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✓ Entorno virtual activado
    echo.
) else (
    echo ✗ Error: No se encuentra el entorno virtual
    echo   Ejecuta: python -m venv venv
    pause
    exit /b 1
)

:menu
echo ================================================================================
echo HERRAMIENTAS DISPONIBLES
echo ================================================================================
echo.
echo  1. Buscar por palabra clave
echo  2. Consultar artículo completo
echo  3. Ver grafo de conexiones
echo  4. Estadísticas globales
echo  5. Regenerar datos (extraer PDF)
echo  6. Abrir PowerShell en este entorno
echo  0. Salir
echo.
set /p opcion="Selecciona una opción (0-6): "

if "%opcion%"=="1" goto buscar
if "%opcion%"=="2" goto consultar
if "%opcion%"=="3" goto grafo
if "%opcion%"=="4" goto stats
if "%opcion%"=="5" goto extraer
if "%opcion%"=="6" goto shell
if "%opcion%"=="0" goto salir
echo.
echo ✗ Opción inválida
echo.
goto menu

:buscar
echo.
set /p termino="Término a buscar: "
python buscar.py "%termino%"
echo.
pause
goto menu

:consultar
echo.
set /p numero="Número de artículo (ej: 34 o 62.6): "
python consultar.py %numero%
echo.
pause
goto menu

:grafo
echo.
set /p numero="Número de artículo: "
python consultar_grafo.py %numero%
echo.
pause
goto menu

:stats
echo.
python grafo_referencias.py
echo.
pause
goto menu

:extraer
echo.
echo ⚠ Esto regenerará todos los datos. ¿Continuar? (S/N)
set /p confirm=
if /i "%confirm%"=="S" (
    python src\pdf_extractor.py
    echo.
    pause
)
goto menu

:shell
echo.
echo ================================================================================
echo PowerShell activado con entorno virtual
echo Ejecuta los comandos manualmente. Escribe 'exit' para volver al menú
echo ================================================================================
echo.
cmd /k
goto menu

:salir
echo.
echo ¡Hasta luego!
exit /b 0