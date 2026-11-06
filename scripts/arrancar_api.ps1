# Solo API FastAPI (primer plano). UI: http://127.0.0.1:8000/  Uso: .\scripts\arrancar_api.ps1
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$py = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    throw "No se encontró .venv; ejecutar: python -m venv .venv ; .venv\Scripts\pip install -r requirements.txt"
}

$enUso = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($enUso) {
    throw "El puerto 8000 ya está en uso (PID $($enUso[0].OwningProcess))."
}

Set-Location $raiz
$env:PRELOAD_DEFAULT = "0"
Write-Host "API en http://127.0.0.1:8000/ (PRELOAD_DEFAULT=0; primera clasificación descarga el modelo)"
& $py -m uvicorn app.api.main:app --port 8000
