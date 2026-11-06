# Ronda 3 (plan: docs/improvement/Plan_ronda3_amenazas_jerga.md). UNA tarea de GPU a la vez; cada paso se salta si ya terminó.
#  0) mBERT-SV de Cristian (Hugging Face caeher/mbert-sv) -> evaluado contra v3.4.0
#  1) profesor: receta B (Optuna) x 3 semillas sobre dataset v1.9.0  -> models/candB_r3
#  2) temperatura del profesor en val                                -> models/profR3/manifest.json
#  3) destilación T 1, alfa 0.5, receta B, 3 semillas                -> models/v3.5.0-rc1
#  4) semilla del estudiante elegida por F1 de val oficial           -> models/v3.5.0-rc1-sel
#  5) comparación con los criterios del plan                         -> reports/improvement/v350_candidatos.md
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"
$PY = ".venv\Scripts\python.exe"; $D = "data/dataset"; $LOG = "runs/log_pipeline_v350.txt"
Add-Type -Namespace W -Name P -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[W.P]::SetThreadExecutionState([uint32]"0x80000001") | Out-Null   # no suspender mientras corre
function Log($m) { $l = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m"; Write-Host $l; Add-Content $LOG $l -Encoding utf8 }
function Run($desc, $logfile, [string[]]$a) {
  Log "INICIO $desc"; & $PY @a *> $logfile
  if ($LASTEXITCODE -ne 0) { Log "ERROR en $desc (codigo $LASTEXITCODE), ver $logfile"; exit 1 }; Log "FIN $desc"
}
Log "=== pipeline v3.5.0 ==="
& $PY -c "import torch;print('GPU:', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')" *>> $LOG

# 0) mBERT de Cristian
if (-not (Test-Path "models/mbert-sv/semilla_42/modelo/model.safetensors")) {
  Run "descarga mbert-sv" "runs/log_descarga_mbert.txt" @("-c", "from huggingface_hub import snapshot_download; snapshot_download('caeher/mbert-sv', local_dir='models/mbert-sv/semilla_42/modelo')")
}
if (-not (Test-Path "reports/improvement/mbert_sv_vs_v340.md")) {
  Run "evaluación mbert-sv" "runs/log_eval_mbert.txt" @("src/evaluation/comparar_v350.py", "v3.4.0", "mbert-sv", "--salida", "mbert_sv_vs_v340")
}

# 1) profesor
$B = (Get-Content runs/mejor_b.args -Raw).Trim().Split(" ")
if (-not (Test-Path "models/candB_r3/metricas.json")) {
  Run "profesor candB_r3 (3 semillas)" "runs/log_candB_r3.txt" (@("src/train/entrenar_v5.py", "--train", "$D/train.csv", "--val", "$D/val.csv", "--test", "$D/test.csv",
      "--adv", "$D/test_adversarial.csv", "--seeds", "42", "1337", "2026", "--peso_nuevos", "0", "--guardar_modelos", "--out", "models/candB_r3") + $B)
}

# 2) temperatura del profesor
if (-not (Test-Path "models/profR3/manifest.json")) {
  Run "temperatura profesor" "runs/log_profR3.txt" @("-c", @'
import sys, json, glob, numpy as np, pandas as pd, pathlib; sys.path.insert(0, '.')
from src.evaluation.comparar_fase3 import temperatura
pv = np.mean([np.load(f) for f in sorted(glob.glob('models/candB_r3/semilla_*/probs_val.npy'))], 0)
T = temperatura(pv, pd.read_csv('data/dataset/val.csv').label.values); pathlib.Path('models/profR3').mkdir(exist_ok=True)
json.dump({'version': 'profR3', 'descripcion': 'Profesor ronda 3: receta B x 3 semillas, dataset 1.9.0', 'componentes': ['candB_r3'], 'temperatura': round(T, 3), 'dataset': '1.9.0'}, open('models/profR3/manifest.json', 'w'), indent=2)
print('T =', T)
'@)
}

# 3) destilación
if (-not (Test-Path "models/v3.5.0-rc1/metricas_destilacion.json")) {
  Run "destilación v3.5.0-rc1 (3 semillas)" "runs/log_v350rc1.txt" (@("src/train/destilar.py", "--profesor", "models/profR3", "--out", "models/v3.5.0-rc1",
      "--seeds", "42", "1337", "2026", "--alfa", "0.5", "--T", "1") + $B)
}

# 4) selección de semilla por F1 de val oficial
if (-not (Test-Path "models/v3.5.0-rc1-sel/manifest_sel.json")) {
  Run "selección de semilla" "runs/log_sel_v350.txt" @("-c", @'
import json, shutil, pathlib
m = json.load(open('models/v3.5.0-rc1/metricas_destilacion.json', encoding='utf-8'))['semillas']
s = max(m, key=lambda k: m[k]['f1_val']); dst = pathlib.Path(f'models/v3.5.0-rc1-sel/semilla_{s}/modelo')
shutil.copytree(f'models/v3.5.0-rc1/semilla_{s}/modelo', dst, dirs_exist_ok=True)
json.dump({'semilla': s, 'regla': 'max F1 val oficial', 'semillas': m}, open('models/v3.5.0-rc1-sel/manifest_sel.json', 'w'), indent=2); print('semilla elegida', s, m[s])
'@)
}

# 5) comparación final (una sola medición)
Run "comparación final" "runs/log_comparacion_v350.txt" @("src/evaluation/comparar_v350.py", "v3.4.0", "v3.5.0-rc1-sel", "profR3", "--salida", "v350_candidatos")
Log "=== FIN pipeline v3.5.0 ==="
