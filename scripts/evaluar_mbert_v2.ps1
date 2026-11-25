# Comparación pareada oficial del mBERT v2 de Cristian (Hugging Face caeher/mbert-toxicidad-sv-v2, 3 semillas, dataset v2.0.0)
# contra v3.4.0 y v3.6.0 con los criterios de docs/improvement/Plan_v2_particion_hilos.md. Unos 5 minutos en GPU.
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"; $PY = ".venv\Scripts\python.exe"
if (-not (Test-Path "models/mbert_v2/semilla_2026/modelo/model.safetensors")) {
  & $PY -c "from huggingface_hub import snapshot_download; snapshot_download('caeher/mbert-toxicidad-sv-v2', local_dir='models/mbert_v2', allow_patterns=['semilla_*/modelo/*', '*.json', '*.md'])"
}
& $PY src/evaluation/comparar_v2.py v3.4.0 mbert_v2 v3.6.0-rc1-sel --salida mbert_v2_vs_v340_v360 *> runs/log_eval_mbert_v2.txt
Write-Host "Listo: reports/improvement/mbert_v2_vs_v340_v360.md"
