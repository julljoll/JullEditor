@echo off
chcp 65001 >nul
title JullEditor v3.2.1 - Generador de Articulos Juridico-Cientificos (Venezuela)

:: =========================================================================
:: JullEditor v3.2.1 — Puente de 1 clic hacia el motor 100% Python
:: Este archivo NO contiene logica: solo localiza el interprete de Python
:: y delega TODO en backend/cli_generator.py (misma logica que la GUI web).
:: Flujos soportados: --cli (asistente interactivo), --test, --file <md>,
:: o sin argumentos para abrir el menu principal del orquestador run.py.
:: =========================================================================

:: 1. Localizar interprete de Python (py.exe > python.exe)
set "PYCMD="
where py.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 set "PYCMD=py.exe"
if "%PYCMD%"=="" (
    where python.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "PYCMD=python.exe"
)

if "%PYCMD%"=="" (
    echo.
    echo =========================================================================
    echo [ERROR] No se encontro el interprete de Python en el sistema.
    echo Instala Python 3.11+ desde https://python.org marcando "Add to PATH".
    echo =========================================================================
    echo.
    pause
    exit /b 1
)

:: 2. Posicionar raiz del proyecto y delegar en el orquestador Python
cd /d "%~dp0"

:bucle_trabajo
"%PYCMD%" run.py %*
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% EQU 0 (
    echo.
    echo =========================================================================
    echo ^| Deseas generar otro articulo juridico-cientifico?
    echo ^|   [1] Si, volver al menu de JullEditor
    echo ^|   [2] No, salir
    echo =========================================================================
    set "OTRO="
    set /p "OTRO=Elige una opcion [1-2] (Enter para salir): "
    if "!OTRO!"=="1" (
        cls
        goto :bucle_trabajo
    )
) else (
    echo.
    echo [INFO] La sesion finalizo con codigo %EXIT_CODE%. Presiona ENTER para salir...
    pause >nul
)
exit /b %EXIT_CODE%
