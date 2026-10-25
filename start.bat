@echo off
chcp 65001 >nul
title JullEditor v3.3.1 (Cyber-Legal Local CPU)

:: Puente de 1 clic hacia el orquestador 100% Python (run.py).
:: Sin logica propia: solo localiza Python y ejecuta python run.py
cd /d "%~dp0"

set "PYCMD="
where py.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 set "PYCMD=py.exe"
if "%PYCMD%"=="" (
    where python.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "PYCMD=python.exe"
)

if "%PYCMD%"=="" (
    echo [ERROR] No se encontro Python. Instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

"%PYCMD%" run.py %*
