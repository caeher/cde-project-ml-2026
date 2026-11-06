# Evalúa el XLM-R de Julio (Hugging Face TheArbite/xlmr-hate-speech-sv) contra v3.4.0 y v3.5.0-rc1-sel.
# OJO: su test oficial está contaminado (319 de 460 textos del test oficial están en su train); solo el banco congelado y la sonda son válidos.
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"; $PY = ".venv\Scripts\python.exe"
if (-not (Test-Path "models/xlmr-julio-v4/semilla_42/modelo/model.safetensors")) {
  & $PY -c "from huggingface_hub import snapshot_download; snapshot_download('TheArbite/xlmr-hate-speech-sv', local_dir='models/xlmr-julio-v4/semilla_42/modelo')"
}
& $PY src/evaluation/comparar_v350.py v3.4.0 xlmr-julio-v4 v3.5.0-rc1-sel mbert-sv --salida modelos_equipo_vs_v340_v2 *> runs/log_eval_equipo_v2.txt
Write-Host "Listo: reports/improvement/modelos_equipo_vs_v340_v2.md"
