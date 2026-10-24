@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title JullEditor — Explorador Informacion_docling_rag & Creador de Artículos TSJ

:: =========================================================================
:: JullEditor v3.1.0 — Explorador en Vivo de Informacion_docling_rag
:: Muestra el contenido de Informacion_docling_rag, permite seleccionar
:: el documento a trabajar y se actualiza automáticamente al agregar archivos.
:: =========================================================================

:: 1. Localizar intérprete de Python (prioriza Python 3.14 o py/python en PATH)
set "PYCMD="
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PYCMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
) else (
    where py.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PYCMD=py.exe"
    ) else (
        where python.exe >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "PYCMD=python.exe"
        )
    )
)

if "%PYCMD%"=="" (
    echo.
    echo =========================================================================
    echo [ERROR] No se encontro el interprete de Python en el sistema.
    echo Instala Python desde https://python.org o asegurate de agregarlo al PATH.
    echo =========================================================================
    echo.
    pause
    exit /b 1
)

:: 2. Posicionar directorio raíz y ejecutar explorador y generador interactivo
cd /d "%~dp0"

:bucle_trabajo
"%PYCMD%" -m backend.cli_generator %*
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% EQU 0 (
    echo.
    echo =========================================================================
    echo ¿Deseas trabajar con otro documento de Informacion_docling_rag?
    echo   [1] Si, volver al explorador de Informacion_docling_rag (actualizado)
    echo   [2] No, salir de JullEditor
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

