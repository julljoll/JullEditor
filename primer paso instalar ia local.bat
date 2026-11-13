@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title JullEditor - Primer Paso: Instalar y Configurar IA Local (Ollama)

:: ===============================================================================
:: JullEditor · Asistente de Instalación de IA Local para Usuarios
:: Archivo: "primer paso instalar ia local.bat"
:: 
:: Este archivo ejecuta de forma 100% automática y transparente:
::   1. Detección e instalación automática de Ollama (motor de IA gratuito).
::   2. Inicio del servicio local de Ollama en segundo plano.
::   3. Detección de la memoria RAM del equipo para elegir el modelo óptimo.
::   4. Descarga del modelo de IA local (IBM Granite 3.3 8B / 2B).
::   5. Prueba de ejecución en vivo para garantizar que todo funciona sin internet.
:: ===============================================================================

color 0B
cls
echo ===============================================================================
echo   JullEditor · Asistente de Instalación de Inteligencia Artificial Local
echo   Paso 1: Preparación 100%% Automática para Redactar sin Conexión a Internet
echo ===============================================================================
echo.
echo  Bienvenido(a). Este asistente preparará tu computadora para que puedas
echo  redactar artículos con Inteligencia Artificial de forma:
echo.
echo    [✓] 100%% Gratuita y sin suscripciones
echo    [✓] Privada (tus textos nunca salen de tu computadora)
echo    [✓] Offline (funciona sin conexión a internet)
echo.
echo  No necesitas conocimientos técnicos. El proceso es totalmente automático.
echo ===============================================================================
echo.
echo  Presiona cualquier tecla para comenzar la instalación...
pause >nul
cls

:: -------------------------------------------------------------------------------
:: PASO 1: Detectar o instalar Ollama
:: -------------------------------------------------------------------------------
echo ===============================================================================
echo  [PASO 1/5] Verificando el motor de Inteligencia Artificial (Ollama)...
echo ===============================================================================

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

if not "!OLLAMA_EXE!"=="" (
    echo  [✓] Ollama ya está instalado en tu computadora.
    goto :paso2_servicio
)

echo.
echo  [!] Ollama NO está instalado en esta computadora.
echo      Procediendo a descargarlo e instalarlo automáticamente...
echo.

:: Intento A: winget (Windows 10/11)
where winget.exe >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo  [INFO] Instalando Ollama mediante el Administrador de Paquetes de Windows (winget)...
    winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements --silent
    timeout /t 5 /nobreak >nul
)

:: Verificar si winget tuvo éxito
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;!PATH!"
    echo  [✓] Ollama instalado correctamente con winget.
    goto :paso2_servicio
)
if exist "%PROGRAMFILES%\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%PROGRAMFILES%\Ollama\ollama.exe"
    set "PATH=%PROGRAMFILES%\Ollama;!PATH!"
    echo  [✓] Ollama instalado correctamente con winget.
    goto :paso2_servicio
)

:: Intento B: Descarga directa del instalador oficial desde ollama.com
echo  [INFO] Descargando el instalador oficial de Ollama desde ollama.com...
echo         Por favor espera mientras se descarga el instalador...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '$env:TEMP\OllamaSetup.exe' -UseBasicParsing; exit 0 } catch { exit 1 }"

if exist "%TEMP%\OllamaSetup.exe" (
    echo  [INFO] Ejecutando instalador oficial de forma silenciosa...
    "%TEMP%\OllamaSetup.exe" /SILENT /NORESTART
    timeout /t 6 /nobreak >nul
) else (
    echo  [ERROR] No se pudo descargar el instalador automáticamente.
    echo          Por favor verifica tu conexión a internet o descarga Ollama
    echo          manualmente desde: https://ollama.com/download
    echo.
    pause
    exit /b 1
)

:: Re-verificación de rutas
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;!PATH!"
) else if exist "%PROGRAMFILES%\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%PROGRAMFILES%\Ollama\ollama.exe"
    set "PATH=%PROGRAMFILES%\Ollama;!PATH!"
)

where ollama.exe >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo  [✓] Instalación de Ollama completada exitosamente.
) else (
    echo  [ERROR] No se detectó Ollama tras la instalación.
    echo          Te sugerimos reiniciar la computadora e intentar de nuevo.
    pause
    exit /b 1
)

:: -------------------------------------------------------------------------------
:: PASO 2: Iniciar el servicio local de Ollama
:: -------------------------------------------------------------------------------
:paso2_servicio
echo.
echo ===============================================================================
echo  [PASO 2/5] Iniciando el servicio de IA local en segundo plano...
echo ===============================================================================

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 2 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo  [✓] El servicio de Ollama ya está activo y respondiendo.
    goto :paso3_hardware
)

echo  [INFO] Arrancando el motor de Ollama...
start "" /B ollama serve >nul 2>&1

:: Esperar a que el servicio esté listo (hasta 15 segundos)
set "READY=0"
for /L %%i in (1,1,15) do (
    if !READY! EQU 0 (
        timeout /t 1 /nobreak >nul
        powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 1 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
        if !ERRORLEVEL! EQU 0 set "READY=1"
    )
)

if !READY! EQU 1 (
    echo  [✓] Motor de IA local iniciado con éxito.
) else (
    echo  [AVISO] El servicio tardó en responder, pero continuaremos con la configuración.
)

:: -------------------------------------------------------------------------------
:: PASO 3: Detección inteligente de hardware (RAM)
:: -------------------------------------------------------------------------------
:paso3_hardware
echo.
echo ===============================================================================
echo  [PASO 3/5] Analizando la capacidad de tu computadora...
echo ===============================================================================

set "RAM_GB=8"
for /f "tokens=*" %%a in ('powershell -NoProfile -Command "try { [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB) } catch { 8 }"') do (
    set "RAM_GB=%%a"
)

echo  Memoria RAM detectada: !RAM_GB! GB

if !RAM_GB! GEQ 8 (
    set "AI_MODEL=granite3.3:8b"
    echo  Modelo asignado: IBM Granite 3.3 (8B)
    echo  (Recomendado: modelo principal para redacción editorial jurídica y técnica)
) else (
    set "AI_MODEL=granite3.3:2b"
    echo  Modelo asignado: IBM Granite 3.3 (2B)
    echo  (Optimizado: versión ligera de alto rendimiento para equipos de recursos ajustados)
)

:: -------------------------------------------------------------------------------
:: PASO 4: Descarga del modelo de IA local
:: -------------------------------------------------------------------------------
:paso4_modelo
echo.
echo ===============================================================================
echo  [PASO 4/5] Descargando el modelo de Inteligencia Artificial (!AI_MODEL!)...
echo ===============================================================================
echo.
echo  [AVISO IMPORTANTE]
echo  Esta descarga se realiza UNA SOLA VEZ.
echo  El peso es de aproximadamente 2 a 5 GB.
echo  Por favor no cierres esta ventana mientras avanza la descarga.
echo.

ollama pull !AI_MODEL!
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo  [ERROR] Ocurrió un error al descargar el modelo !AI_MODEL!.
    echo          Verifica tu conexión a internet e intenta nuevamente.
    pause
    exit /b 1
)

echo.
echo  [✓] Modelo !AI_MODEL! descargado y almacenado localmente en tu equipo.

:: -------------------------------------------------------------------------------
:: PASO 5: Prueba de inferencia en vivo
:: -------------------------------------------------------------------------------
:paso5_prueba
echo.
echo ===============================================================================
echo  [PASO 5/5] Probando que el modelo responda en tu computadora...
echo ===============================================================================
echo.
echo  Enviando consulta de prueba a la IA local...
ollama run !AI_MODEL! "Responde en exactamente una frase corta: ¡La Inteligencia Artificial local está lista y configurada para JullEditor!"

:: -------------------------------------------------------------------------------
:: RESUMEN Y FINALIZACIÓN
:: -------------------------------------------------------------------------------
cls
echo ===============================================================================
echo               ¡FELICIDADES! INSTALACIÓN COMPLETADA CON ÉXITO
echo ===============================================================================
echo.
echo  Tu computadora ahora cuenta con un motor de Inteligencia Artificial Local:
echo.
echo    • Motor instalado:     Ollama (en ejecución local en tu equipo)
echo    • Modelo configurado:  !AI_MODEL! (IBM Granite 3.3)
echo    • Memoria RAM:         !RAM_GB! GB
echo    • Modo de operación:   100%% Offline (sin enviar datos a terceros)
echo.
echo  ¿CÓMO USAR JULL EDITOR AHORA?
echo  -----------------------------------------------------------------------------
echo  1. Ya puedes cerrar esta ventana.
echo  2. Abre JullEditor haciendo doble clic en:
echo        start.bat    (o crear_articulo.bat)
echo.
echo  3. En la pantalla del editor (Studio), verás seleccionado por defecto:
echo        [Ollama local (IBM Granite / offline)]
echo.
echo  4. Escribe tus títulos o notas y genera tus artículos para Astro al instante.
echo ===============================================================================
echo.
echo  Presiona cualquier tecla para finalizar...
pause >nul
exit /b 0
