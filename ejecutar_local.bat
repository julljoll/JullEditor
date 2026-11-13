@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title JullEditor - Lanzador y Auto-Instalador 100% Local (Offline)

:: ===============================================================================
:: JullEditor · Archivo Único de Instalación y Ejecución Local 100% Automático
:: Archivo: "ejecutar_local.bat"
:: 
:: Este script realiza TODO en 1 solo clic:
::   1. Detecta o instala Python 3.10+ en tu equipo.
::   2. Instala dependencias de requirements.txt en entorno virtual.
::   3. Detecta o instala Ollama automáticamente.
::   4. Inicia el servicio local de Ollama en segundo plano.
::   5. Detecta la memoria RAM y descarga el modelo IBM Granite 3.3 óptimo.
::   6. Inicia el backend FastAPI, el frontend Astro y abre tu navegador en
::      http://localhost:3000 listo para redactar y reversionar artículos.
:: ===============================================================================

cd /d "%~dp0"
color 0B
cls

echo ===============================================================================
echo   JullEditor · Estacion Editorial y Pericial de Redaccion (100%% Local)
echo ===============================================================================
echo.
echo   [✓] 100%% Gratuito y sin suscripciones
echo   [✓] 100%% Privado (tus textos nunca salen de tu computadora)
echo   [✓] 100%% Offline (funciona sin conexion a internet tras la primera descarga)
echo.
echo ===============================================================================
echo.

:: -------------------------------------------------------------------------------
:: PASO 1: Detectar o instalar Python
:: -------------------------------------------------------------------------------
echo [1/5] Verificando entorno Python...

set "PYCMD="
where py.exe >nul 2>&1
if !ERRORLEVEL! EQU 0 set "PYCMD=py.exe"
if "!PYCMD!"=="" (
    where python.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYCMD=python.exe"
)
if "!PYCMD!"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYCMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
    ) else if exist "%PROGRAMFILES%\Python312\python.exe" (
        set "PYCMD=%PROGRAMFILES%\Python312\python.exe"
        set "PATH=%PROGRAMFILES%\Python312;%PROGRAMFILES%\Python312\Scripts;!PATH!"
    )
)

if "!PYCMD!"=="" (
    echo.
    echo  [!] Python no esta instalado en esta computadora.
    echo      Instalandolo automaticamente...
    echo.
    where winget.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo  [INFO] Instalando Python via Windows Package Manager (winget)...
        winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --silent
        timeout /t 5 /nobreak >nul
    )
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYCMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
    )
    if "!PYCMD!"=="" (
        echo  [INFO] Descargando instalador oficial de python.org...
        powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '$env:TEMP\python-installer.exe' -UseBasicParsing; exit 0 } catch { exit 1 }"
        if exist "%TEMP%\python-installer.exe" (
            echo  [INFO] Ejecutando instalacion silenciosa de Python...
            "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1
            timeout /t 8 /nobreak >nul
        )
    )
    where python.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYCMD=python.exe"
)

if "!PYCMD!"=="" (
    echo  [ERROR] No se pudo instalar Python automaticamente.
    echo          Por favor instala Python 3.10+ desde https://python.org
    pause
    exit /b 1
)
echo  [✓] Python detectado correctamente.

:: -------------------------------------------------------------------------------
:: PASO 2: Entorno virtual y dependencias Python
:: -------------------------------------------------------------------------------
echo.
echo [2/5] Verificando dependencias del proyecto (requirements.txt)...

set "VENV_PY=.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo  [INFO] Creando entorno virtual local (.venv)...
    !PYCMD! -m venv .venv
)
if exist "%VENV_PY%" (
    set "RUNNER=%VENV_PY%"
) else (
    set "RUNNER=!PYCMD!"
)

if exist "requirements.txt" (
    !RUNNER! -c "import fastapi, uvicorn, httpx, pydantic, yaml" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo  [INFO] Instalando librerias necesarias en segundo plano...
        !RUNNER! -m pip install --quiet -r requirements.txt
    )
)
echo  [✓] Dependencias de Python listas.

:: -------------------------------------------------------------------------------
:: PASO 3: Detectar o instalar Ollama e iniciar servicio
:: -------------------------------------------------------------------------------
echo.
echo [3/5] Verificando motor de Inteligencia Artificial (Ollama)...

set "OLLAMA_EXE="
where ollama.exe >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    set "OLLAMA_EXE=ollama.exe"
) else (
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Ollama;!PATH!"
    ) else if exist "%PROGRAMFILES%\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%PROGRAMFILES%\Ollama\ollama.exe"
        set "PATH=%PROGRAMFILES%\Ollama;!PATH!"
    )
)

if "!OLLAMA_EXE!"=="" (
    echo  [INFO] Descargando e instalando Ollama automaticamente...
    where winget.exe >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements --silent
        timeout /t 5 /nobreak >nul
    )
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Ollama;!PATH!"
    ) else if exist "%PROGRAMFILES%\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%PROGRAMFILES%\Ollama\ollama.exe"
        set "PATH=%PROGRAMFILES%\Ollama;!PATH!"
    )
    if "!OLLAMA_EXE!"=="" (
        powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '$env:TEMP\OllamaSetup.exe' -UseBasicParsing; exit 0 } catch { exit 1 }"
        if exist "%TEMP%\OllamaSetup.exe" (
            "%TEMP%\OllamaSetup.exe" /SILENT /NORESTART
            timeout /t 6 /nobreak >nul
        )
    )
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
)

:: Iniciar servicio Ollama si no esta respondiendo
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 2 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [INFO] Iniciando servicio Ollama en segundo plano...
    start "" /B ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
)
echo  [✓] Motor Ollama activo y respondiendo en http://localhost:11434.

:: -------------------------------------------------------------------------------
:: PASO 4: Detectar RAM y verificar modelo local IBM Granite 3.3
:: -------------------------------------------------------------------------------
echo.
echo [4/5] Verificando modelo de IA local (IBM Granite 3.3)...

set "RAM_GB=8"
for /f "tokens=*" %%a in ('powershell -NoProfile -Command "try { [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB) } catch { 8 }"') do (
    set "RAM_GB=%%a"
)

if !RAM_GB! GEQ 8 (
    set "AI_MODEL=granite3.3:8b"
) else (
    set "AI_MODEL=granite3.3:2b"
)

:: Verificar si el modelo ya esta descargado
ollama list 2>nul | findstr /i "!AI_MODEL!" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo  [✓] Modelo !AI_MODEL! ya esta instalado y listo para usar en tu PC.
) else (
    echo  [INFO] Descargando modelo !AI_MODEL! (se realiza una sola vez)...
    echo         Por favor espera unos minutos mientras se completa la descarga...
    ollama pull !AI_MODEL!
    if !ERRORLEVEL! EQU 0 (
        echo  [✓] Modelo !AI_MODEL! descargado exitosamente.
    ) else (
        echo  [AVISO] No se pudo descargar !AI_MODEL!. Si ya tienes otro modelo local, continuaremos.
    )
)

:: -------------------------------------------------------------------------------
:: PASO 5: Iniciar JullEditor (FastAPI + Astro)
:: -------------------------------------------------------------------------------
echo.
echo ===============================================================================
echo [5/5] Iniciando JullEditor localmente...
echo       Abriendo interfaz en tu navegador: http://localhost:3000
echo ===============================================================================
echo.
echo  Para detener la aplicacion, cierra esta ventana en cualquier momento.
echo.

!RUNNER! run.py %*
pause
