# prepare-python.ps1 — Fase 3 del plan Electron/Windows.
# Construye el runtime Python embebido (embeddable) en desktop/python/ con
# todas las dependencias de requirements.txt preinstaladas, listo para ser
# copiado al instalador por electron-builder (extraResources).
#
# Uso (en Windows, dentro de desktop/):
#   powershell -ExecutionPolicy Bypass -File scripts\prepare-python.ps1
# Variables opcionales:
#   $env:PY_VERSION  (default 3.11.9)

$ErrorActionPreference = "Stop"

$PyVersion = if ($env:PY_VERSION) { $env:PY_VERSION } else { "3.11.9" }
$DesktopDir = Split-Path -Parent $PSScriptRoot
$PythonDir  = Join-Path $DesktopDir "python"
$RepoRoot   = Split-Path -Parent $DesktopDir
$ZipUrl     = "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-embed-amd64.zip"

Write-Host "== JullEditor: preparando runtime Python embebido $PyVersion =="

# 1. Limpiar y descargar
if (Test-Path $PythonDir) { Remove-Item $PythonDir -Recurse -Force }
New-Item -ItemType Directory -Path $PythonDir | Out-Null

$tmpZip = Join-Path $env:TEMP "python-embed.zip"
Write-Host "[1/5] Descargando $ZipUrl ..."
Invoke-WebRequest -Uri $ZipUrl -OutFile $tmpZip

Write-Host "[2/5] Descomprimiendo en $PythonDir ..."
Expand-Archive -Path $tmpZip -DestinationPath $PythonDir -Force

# 2. Habilitar import site (editar pythonXX._pth)
$pth = Get-ChildItem -Path $PythonDir -Filter "python*._pth" | Select-Object -First 1
if (-not $pth) { throw "No se encontro el archivo ._pth del runtime embeddable" }
(Get-Content $pth.FullName) -replace "^#import site", "import site" | Set-Content $pth.FullName
Write-Host "[3/5] 'import site' habilitado en $($pth.Name)"

# 3. Instalar pip
$getPip = Join-Path $env:TEMP "get-pip.py"
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip
$pyExe = Join-Path $PythonDir "python.exe"
& $pyExe $getPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw "Fallo la instalacion de pip" }
Write-Host "[4/5] pip instalado en el runtime embebido"

# 4. Instalar dependencias del proyecto
$req = Join-Path $RepoRoot "requirements.txt"
& $pyExe -m pip install --no-warn-script-location -r $req
if ($LASTEXITCODE -ne 0) { throw "Fallo pip install -r requirements.txt" }

# 5. Sanity check
& $pyExe -c "import fastapi, uvicorn, httpx; print('OK: deps verificadas')"
if ($LASTEXITCODE -ne 0) { throw "Sanity check de dependencias fallo" }

Write-Host "[5/5] Runtime embebido listo en $PythonDir"
Write-Host "Siguiente paso: npm run dist  (electron-builder empaqueta desktop/python/)"
