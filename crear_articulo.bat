@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title JullEditor v3.4.0 - Generador de Articulos Juridico-Cientificos (Venezuela)

:: =========================================================================
:: JullEditor v3.4.0 — Puente de 1 clic con AUTO-ARRANQUE INTELIGENTE
:: Este archivo NO contiene logica de generacion: solo garantiza el entorno
:: y delega TODO en Python (run.py -> backend/bootstrap.py):
::   [1] Verifica Python; si NO existe, lo INSTALA automaticamente
::       (winget python.python.3.12 -> fallback descarga oficial python.org)
::   [2] run.py analiza la computadora (CPU/RAM/SO/arquitectura)
::   [3] Instala dependencias Python faltantes (pip install -r requirements.txt)
::   [4] Instala Ollama si falta (winget / instalador oficial segun SO)
::   [5] Descarga el modelo Granite acorde al hardware (8b >=8GB / 2b <8GB)
:: Luego abre el menu del orquestador (--cli / --tui / web, misma GUI).
:: =========================================================================

:: ----------------------------------------------------------------------
:: PASO 1: Verificar Python — instalarlo de una vez si no existe
:: ----------------------------------------------------------------------
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
    echo [INFO] Python NO esta instalado en esta computadora.
    echo        Instalando Python automaticamente...
    echo =========================================================================
    echo.

    :: Intento A: winget (Windows 10/11 moderno)
    where winget.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --silent
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%LOCALAPPDATA%\Programs\Python\Launcher;!PATH!"
    )

    :: Verificar de nuevo tras winget
    set "PYCMD="
    where py.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYCMD=py.exe"
    if "!PYCMD!"=="" (
        where python.exe >nul 2>&1
        if !ERRORLEVEL! EQU 0 set "PYCMD=python.exe"
    )

    :: Intento B: descarga directa del instalador oficial python.org
    if "!PYCMD!"=="" (
        echo [INFO] winget no disponible o fallo. Descargando instalador oficial de python.org...
        powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
        if exist "%TEMP%\python-installer.exe" (
            echo [INFO] Ejecutando instalador silencioso con Add to PATH...
            "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1
            set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%LOCALAPPDATA%\Programs\Python\Launcher;!PATH!"
        )
    )

    :: Verificacion final
    set "PYCMD="
    where py.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYCMD=py.exe"
    if "!PYCMD!"=="" (
        where python.exe >nul 2>&1
        if !ERRORLEVEL! EQU 0 set "PYCMD=python.exe"
    )
)

if "%PYCMD%"=="" (
    echo.
    echo =========================================================================
    echo [ERROR] No se pudo instalar Python automaticamente.
    echo         Instalalo manualmente desde https://python.org marcando
    echo         la casilla "Add python.exe to PATH", y vuelve a abrir este .bat
    echo =========================================================================
    echo.
    pause
    exit /b 1
)

echo [OK] Interprete Python detectado: %PYCMD%

:: ----------------------------------------------------------------------
:: PASOS 2-5 + trabajo: el auto-arranque vive 100% en Python
:: (run.py -> backend/bootstrap.py): analisis de hardware, pip, Ollama,
:: ollama pull granite acorde a la maquina. Sin logica duplicada aqui.
:: ----------------------------------------------------------------------
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
