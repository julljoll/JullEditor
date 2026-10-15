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
    (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    "$env:LOCALAPPDATA\Python\bin\python.exe",
    (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
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

# 2. Localizar Ollama e iniciar servicio
$ollamaCmd = (Get-Command ollama.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
if (-not $ollamaCmd) {
    $ollamaCandidate = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaCandidate) {
        $ollamaCmd = $ollamaCandidate
        $env:PATH = "$env:LOCALAPPDATA\Programs\Ollama;$env:PATH"
    }
}

if ($ollamaCmd) {
    Write-Host "[OK] Ollama detectado: $ollamaCmd" -ForegroundColor Green
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
    } catch {
        $health = $null
    }
    if (-not $health) {
        Write-Host "[INFO] Iniciando servicio de Ollama en segundo plano..." -ForegroundColor Cyan
        Start-Process -FilePath $ollamaCmd -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }

    # Verificar presencia del modelo Granite
    try {
        $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction SilentlyContinue
        $hasGranite = $tags.models | Where-Object { $_.name -like "*granite*" }
        if (-not $hasGranite) {
            Write-Host "[AVISO] Modelo IBM Granite no detectado en Ollama." -ForegroundColor Yellow
            Write-Host "Puedes descargarlo ejecutando: ollama pull granite3.3:8b (o granite3.3:2b)" -ForegroundColor Yellow
        } else {
            $modelName = $hasGranite[0].name
            Write-Host "[OK] Modelo IBM Granite detectado: $modelName" -ForegroundColor Green
            # Warm-up rápido para precargar el modelo en memoria RAM
            try {
                $warmPayload = '{"model":"' + $modelName + '","keep_alive":"30m"}'
                Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body $warmPayload -ContentType "application/json" -TimeoutSec 3 -ErrorAction SilentlyContinue | Out-Null
                Write-Host "[OK] Modelo precargado en memoria RAM (keep_alive: 30m)." -ForegroundColor Green
            } catch {}
        }
    } catch {}
} else {
    Write-Host "[ADVERTENCIA] Ollama no encontrado. Asegurate de que este corriendo en localhost:11434" -ForegroundColor DarkYellow
}

# 3. Abrir navegador
Write-Host "[INFO] Abriendo navegador en http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000"

# 4. Iniciar servidor FastAPI
Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host "   Servidor Web Activo: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "   Presiona CTRL+C para detener la aplicacion" -ForegroundColor Green
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host ""

& $pythonCmd -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
