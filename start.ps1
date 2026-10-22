<#
.SYNOPSIS
Iniciador Profesional de Granite Blog Writer en PowerShell
#>

$Host.UI.RawUI.WindowTitle = "Granite Cyber-Legal Blog Writer (Local CPU)"
Write-Host "=========================================================================" -ForegroundColor Yellow
Write-Host "   INICIANDO GRANITE BLOG WRITER (CYBER-LEGAL BLUEPRINT v2.1)" -ForegroundColor Yellow
Write-Host "=========================================================================" -ForegroundColor Yellow
Write-Host ""

# 0. Verificar .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "[INFO] Creando archivo .env a partir de .env.example..." -ForegroundColor Cyan
        Copy-Item ".env.example" ".env"
    }
}

# 1. Localizar Python
$candidatePaths = @(
    "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
    (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    "$env:LOCALAPPDATA\Python\bin\python.exe",
    (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Python\Python312\python.exe",
    "C:\Python312\python.exe"
)

$pythonCmd = $null
foreach ($p in $candidatePaths) {
    if ($p -and (Test-Path $p) -and ($p -notlike "*WindowsApps\python.exe*")) {
        $pythonCmd = $p
        break
    }
}

if (-not $pythonCmd) {
    Write-Host "[ERROR] No se encontro Python en el sistema." -ForegroundColor Red
    Write-Host "Por favor instala Python y asegurate de marcar 'Add python.exe to PATH'."
    Read-Host "Presiona ENTER para salir..."
    exit 1
}

Write-Host "[OK] Python detectado: $pythonCmd" -ForegroundColor Green

# 1.1 Diagnóstico de Hardware y Perfil Recomendado
try {
    $cpuCount = (Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
    if (-not $cpuCount) { $cpuCount = [Environment]::ProcessorCount }
    $ramBytes = (Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue).TotalPhysicalMemory
    $ramGB = if ($ramBytes) { [math]::Round($ramBytes / 1GB, 1) } else { 8.0 }
    
    Write-Host "[HARDWARE] Hilos CPU: $cpuCount | Memoria RAM: ${ramGB} GB" -ForegroundColor Cyan
    if ($ramGB -lt 8.0) {
        Write-Host "[RECOMENDACION] RAM < 8GB: Se recomienda usar modelo liviano 'granite3.3:2b'." -ForegroundColor Yellow
    } else {
        Write-Host "[RECOMENDACION] RAM >= 8GB: Rendimiento óptimo con 'granite3.3:8b'." -ForegroundColor Green
    }
} catch {}

# 2. Localizar Ollama, iniciar servicio (Paso 1) y asegurar modelo granite3.3:8b (Paso 2)
$ollamaCmd = (Get-Command ollama.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
if (-not $ollamaCmd) {
    $candidateOllamaPaths = @(
        "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
        "$env:ProgramFiles\Ollama\ollama.exe",
        "$env:ProgramFiles(x86)\Ollama\ollama.exe"
    )
    foreach ($cand in $candidateOllamaPaths) {
        if (Test-Path $cand) {
            $ollamaCmd = $cand
            $ollamaDir = Split-Path $cand
            $env:PATH = "$ollamaDir;$env:PATH"
            break
        }
    }
}

if ($ollamaCmd) {
    Write-Host "[OK] Ollama detectado: $ollamaCmd" -ForegroundColor Green

    # =========================================================================
    # PASO 1: Iniciar automáticamente el servicio de Ollama (ollama serve)
    # =========================================================================
    $isOllamaRunning = $false
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($health) { $isOllamaRunning = $true }
    } catch {
        $isOllamaRunning = $false
    }

    if (-not $isOllamaRunning) {
        Write-Host ""
        Write-Host "[PASO 1] Iniciando servicio de Ollama en segundo plano (ollama serve)..." -ForegroundColor Cyan
        Start-Process -FilePath $ollamaCmd -ArgumentList "serve" -WindowStyle Hidden
        
        # Esperar hasta que el servicio responda (máximo 15 segundos)
        $attempts = 0
        while (-not $isOllamaRunning -and $attempts -lt 15) {
            Start-Sleep -Seconds 1
            $attempts++
            try {
                $testTags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($testTags) { $isOllamaRunning = $true }
            } catch {}
        }

        if ($isOllamaRunning) {
            Write-Host "[OK] Servicio de Ollama iniciado correctamente (localhost:11434)." -ForegroundColor Green
        } else {
            Write-Host "[AVISO] Ollama se inicio pero tardo en responder. Continuando..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[OK] Servicio de Ollama ya se encuentra activo (localhost:11434)." -ForegroundColor Green
    }

    # =========================================================================
    # PASO 2: Asegurar que el modelo 'granite3.3:8b' este descargado (ollama pull)
    # =========================================================================
    try {
        $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction SilentlyContinue
        $installedModels = @($tags.models | ForEach-Object { $_.name })
        
        $has8b = $installedModels | Where-Object { $_ -like "granite3.3:8b*" -or $_ -like "*granite*8b*" }
        $hasAnyGranite = $installedModels | Where-Object { $_ -like "*granite*" }

        if (-not $has8b) {
            Write-Host ""
            Write-Host "=========================================================================" -ForegroundColor Yellow
            Write-Host "[PASO 2] Descargando modelo recomendado: ollama pull granite3.3:8b" -ForegroundColor Yellow
            Write-Host "   (Esto solo se realiza una vez; la descarga se visualizara en esta terminal)" -ForegroundColor Gray
            Write-Host "=========================================================================" -ForegroundColor Yellow
            
            & $ollamaCmd pull granite3.3:8b
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Modelo IBM Granite 3.3 8B descargado exitosamente." -ForegroundColor Green
                $targetModel = "granite3.3:8b"
            } else {
                Write-Host "[AVISO] La descarga de granite3.3:8b no finalizo con codigo 0." -ForegroundColor Yellow
                if ($hasAnyGranite) {
                    $targetModel = $hasAnyGranite[0]
                    Write-Host "[INFO] Se utilizara el modelo Granite existente: $targetModel" -ForegroundColor Cyan
                } else {
                    $targetModel = "granite3.3:8b"
                }
            }
        } else {
            $targetModel = $has8b[0]
            Write-Host "[OK] Modelo IBM Granite verificado y listo: $targetModel" -ForegroundColor Green
        }

        # Warm-up rápido para precargar el modelo en memoria RAM (keep_alive: 30m)
        if ($targetModel) {
            try {
                $warmPayload = '{"model":"' + $targetModel + '","keep_alive":"30m"}'
                Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body $warmPayload -ContentType "application/json" -TimeoutSec 3 -ErrorAction SilentlyContinue | Out-Null
                Write-Host "[OK] Modelo precargado en memoria RAM ($targetModel · keep_alive: 30m)." -ForegroundColor Green
            } catch {}
        }
    } catch {
        Write-Host "[AVISO] No se pudo verificar la lista de modelos de Ollama: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ADVERTENCIA] Ollama no encontrado. Asegurate de instalarlo desde https://ollama.com" -ForegroundColor DarkYellow
}

# 3. Verificar y liberar el puerto 8000 si quedo ocupado por una instancia previa
try {
    $existingConns = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($existingConns) {
        foreach ($conn in $existingConns) {
            $prevPid = $conn.OwningProcess
            if ($prevPid -and $prevPid -ne 0 -and $prevPid -ne $PID) {
                $prevProc = Get-Process -Id $prevPid -ErrorAction SilentlyContinue
                if ($prevProc -and ($prevProc.ProcessName -like "*python*" -or $prevProc.ProcessName -like "*uvicorn*")) {
                    Write-Host "[INFO] Liberando puerto 8000 ocupado por proceso previo de Python (PID $prevPid)..." -ForegroundColor Cyan
                    Stop-Process -Id $prevPid -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 800
                } elseif ($prevProc) {
                    Write-Host "[ADVERTENCIA] El puerto 8000 esta en uso por el proceso '$($prevProc.ProcessName)' (PID $prevPid)." -ForegroundColor Yellow
                }
            }
        }
    }
} catch {}

# 4. Abrir navegador en segundo plano al iniciar
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 1
    Start-Process "http://127.0.0.1:8000"
} | Out-Null

# 5. Iniciar servidor FastAPI
Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host "   Servidor Web Activo: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "   Presiona CTRL+C para detener la aplicacion" -ForegroundColor Green
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host ""

& $pythonCmd -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

