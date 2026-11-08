# Comparación pareada oficial de los modelos del equipo entrenados con el dataset v2.0.0, con el mismo evaluador y criterios
# (docs/improvement/Plan_v2_particion_hilos.md):
#   mBERT v2 de Cristian  (Hugging Face caeher/mbert-toxicidad-sv-v2, ensamble de 3 semillas)
#   XLM-R large de Julio  (Hugging Face TheArbite/xlmr-large-v2-hate-speech-sv, 1 modelo)
# contra v3.4.0 (referencia) y v3.6.0 (API). Unos 10 minutos en GPU (descarga ~4 GB la primera vez).
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"; $PY = ".venv\Scripts\python.exe"
if (-not (Test-Path "models/mbert_v2/semilla_2026/modelo/model.safetensors")) {
  & $PY -c "from huggingface_hub import snapshot_download; snapshot_download('caeher/mbert-toxicidad-sv-v2', local_dir='models/mbert_v2', allow_patterns=['semilla_*/modelo/*', '*.json', '*.md'])"
}
if (-not (Test-Path "models/xlmr_large_v2/semilla_42/modelo/model.safetensors")) {
  & $PY -c "from huggingface_hub import snapshot_download; snapshot_download('TheArbite/xlmr-large-v2-hate-speech-sv', local_dir='models/xlmr_large_v2/semilla_42/modelo')"
}
& $PY src/evaluation/comparar_v2.py v3.4.0 mbert_v2 xlmr_large_v2 v3.6.0-rc1-sel --salida equipo_v2_comparacion *> runs/log_eval_equipo_v2.txt
Get-Content runs/log_eval_equipo_v2.txt -Tail 40
Write-Host "Listo: reports/improvement/equipo_v2_comparacion.md"
