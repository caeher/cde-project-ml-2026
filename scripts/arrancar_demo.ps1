# Arranca el prototipo local: API (puerto 8000) + panel Streamlit (puerto 8501). Uso: .\scripts\arrancar_demo.ps1
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$py = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "No se encontró .venv; ejecutar: python -m venv .venv ; .venv\Scripts\pip install -r requirements.txt" }
Set-Location $raiz
Write-Host "Iniciando API en http://127.0.0.1:8000 ..."
$api = Start-Process -FilePath $py -ArgumentList "-m","uvicorn","app.api.main:app","--port","8000" -PassThru -WindowStyle Minimized
try {
    for ($i = 0; $i -lt 60; $i++) {
        try { $s = Invoke-RestMethod "http://127.0.0.1:8000/salud" -TimeoutSec 2; break } catch { Start-Sleep -Seconds 2 }
    }
    # primera consulta: carga los modelos y calienta
    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/predecir" -ContentType "application/json" -Body '{"texto":"hola"}' | Out-Null
    Write-Host "API lista. Abriendo panel en http://localhost:8501 (Ctrl+C para cerrar todo)"
    & $py -m streamlit run app/ui/app.py --server.port 8501
} finally {
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}
