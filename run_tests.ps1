# Script para ejecutar la suite de pruebas completa de Granite Blog Writer v3.0

Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "   EJECUTANDO SUITE COMPLETA DE PRUEBAS - GRANITE BLOG WRITER v3.0" -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

$candidatePython = @(
    "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
    (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
)

$py = $null
foreach ($cand in $candidatePython) {
    if ($cand -and (Test-Path $cand)) {
        $py = $cand
        break
    }
}

if (-not $py) {
    Write-Host "[ERROR] No se encontro Python para ejecutar las pruebas." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Utilizando interprete: $py" -ForegroundColor Green
Write-Host ""

& $py -m pytest tests/ -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================================================" -ForegroundColor Green
    Write-Host "   [OK] TODAS LAS PRUEBAS PASARON EXITOSAMENTE (0 FALLOS)" -ForegroundColor Green
    Write-Host "=========================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "=========================================================================" -ForegroundColor Red
    Write-Host "   [ERROR] ALGUNAS PRUEBAS FALLARON (Codigo de salida: $LASTEXITCODE)" -ForegroundColor Red
    Write-Host "=========================================================================" -ForegroundColor Red
    exit $LASTEXITCODE
}
