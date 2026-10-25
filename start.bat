@echo off
chcp 65001 >nul
title JullEditor v3.4.0 (Cyber-Legal Local CPU)

:: Puente de 1 clic hacia el orquestador 100% Python (run.py).
:: El auto-arranque completo (analisis de PC, pip, Ollama, modelo Granite
:: acorde al hardware) vive en backend/bootstrap.py — sin logica aqui.
cd /d "%~dp0"

set "PYCMD="
where py.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 set "PYCMD=py.exe"
if "%PYCMD%"=="" (
    where python.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "PYCMD=python.exe"
)

if "%PYCMD%"=="" (
    echo [ERROR] No se encontro Python. Ejecuta crear_articulo.bat que lo
    echo         instala automaticamente, o instalalo desde https://python.org
    pause
    exit /b 1
)

"%PYCMD%" run.py %*
pause
