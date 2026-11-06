# Arranca el prototipo local: API (puerto 8000) + panel Streamlit (puerto 8501). Uso: .\scripts\arrancar_demo.ps1
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$py = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    throw "No se encontró .venv; ejecutar: python -m venv .venv ; .venv\Scripts\pip install -r requirements.txt"
}

$runs = Join-Path $raiz "runs"
if (-not (Test-Path $runs)) { New-Item -ItemType Directory -Path $runs | Out-Null }
$logApi = Join-Path $runs "demo-api.log"

function Test-PuertoLibre([int]$Puerto) {
    $enUso = Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue
    if ($enUso) {
        throw "El puerto $Puerto ya está en uso (PID $($enUso[0].OwningProcess)). Cierra ese proceso o usa otro puerto."
    }
}

function Show-LogTail([string]$Path, [int]$Lineas = 40) {
    if (Test-Path $Path) {
        Write-Host "--- Últimas líneas de $Path ---" -ForegroundColor Yellow
        Get-Content $Path -Tail $Lineas -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
    }
}

function Wait-ApiSalud([int]$MaxSegundos = 30) {
    $deadline = (Get-Date).AddSeconds($MaxSegundos)
    while ((Get-Date) -lt $deadline) {
        if ($script:apiProc -and $script:apiProc.HasExited) {
            Show-LogTail $logApi
            throw "La API terminó con código $($script:apiProc.ExitCode). Revisa runs/demo-api.log"
        }
        try {
            $r = Invoke-RestMethod "http://127.0.0.1:8000/salud" -TimeoutSec 3
            if ($r.estado -eq "ok") { return $true }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

Set-Location $raiz
Test-PuertoLibre -Puerto 8000

Write-Host "Iniciando API en http://127.0.0.1:8000 (log: runs/demo-api.log) ..."
if (Test-Path $logApi) { Remove-Item $logApi -Force }

$env:PRELOAD_DEFAULT = "0"
$script:apiProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList @("/c", "`"$py`" -m uvicorn app.api.main:app --port 8000 --log-level info >> `"$logApi`" 2>&1") `
    -PassThru `
    -WindowStyle Hidden `
    -WorkingDirectory $raiz

try {
    if (-not (Wait-ApiSalud -MaxSegundos 45)) {
        Show-LogTail $logApi
        throw "La API no respondió en /salud tras 45 s. Revisa runs/demo-api.log"
    }
    Write-Host "API en línea. Descargando/cargando modelo (primera vez puede tardar varios minutos) ..."
    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/clasificar" `
        -ContentType "application/json" `
        -Body '{"texto":"hola maje"}' `
        -TimeoutSec 600 | Out-Null

    Write-Host "API lista. Abriendo panel en http://localhost:8501 (Ctrl+C para cerrar todo)"
    Write-Host "Interfaz HTML alternativa: http://127.0.0.1:8000/"
    & $py -m streamlit run app/ui/app.py --server.port 8501
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Show-LogTail $logApi
    exit 1
} finally {
    if ($script:apiProc -and -not $script:apiProc.HasExited) {
        Stop-Process -Id $script:apiProc.Id -Force -ErrorAction SilentlyContinue
    }
}
