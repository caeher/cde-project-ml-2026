# Dataset v2.0.0 (plan: docs/improvement/Plan_v2_particion_hilos.md). UNA tarea de GPU a la vez; cada paso se salta si ya terminó.
#  0) val_v2 = val oficial + val_hilos                                  -> runs/val_v2.csv
#  1) profesor: receta B (Optuna) x 3 semillas sobre dataset v2.0.0     -> models/candB_v2
#  2) temperatura del profesor en val_v2                               -> models/profV2/manifest.json
#  3) destilación T 1, alfa 0.5, receta B, 3 semillas                  -> models/v3.6.0-rc1
#  4) semilla del estudiante por F1 en val_v2                          -> models/v3.6.0-rc1-sel
#  5) comparación con los criterios del plan                           -> reports/improvement/v360_candidatos.md
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"
$PY = ".venv\Scripts\python.exe"; $D = "data/dataset"; $LOG = "runs/log_pipeline_v360.txt"
Add-Type -Namespace W -Name P -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[W.P]::SetThreadExecutionState([uint32]"0x80000001") | Out-Null   # no suspender mientras corre
function Log($m) { $l = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m"; Write-Host $l; Add-Content $LOG $l -Encoding utf8 }
function Run($desc, $logfile, [string[]]$a) {
  Log "INICIO $desc"; & $PY @a *> $logfile
  if ($LASTEXITCODE -ne 0) { Log "ERROR en $desc (codigo $LASTEXITCODE), ver $logfile"; exit 1 }; Log "FIN $desc"
}
Log "=== pipeline v3.6.0 (dataset v2.0.0) ==="
& $PY -c "import json;m=json.load(open('data/dataset/metadata.json',encoding='utf-8'));print('dataset',m['version'],m['train_total'])" *>> $LOG

# 0) val_v2
if (-not (Test-Path "runs/val_v2.csv")) {
  Run "val_v2" "runs/log_val_v2.txt" @("-c", @'
import sys, pandas as pd; sys.path.insert(0, '.')
from src.features.normalization import normalizar
v = pd.read_csv('data/dataset/val.csv')[['ID', 'texto_original', 'texto_modelo', 'label']]
h = pd.read_csv('data/dataset/val_hilos.csv', encoding='utf-8-sig')
h = pd.DataFrame({'ID': h.ID, 'texto_original': h.texto_original, 'texto_modelo': h.texto_original.map(normalizar), 'label': h.label})
pd.concat([v, h], ignore_index=True).to_csv('runs/val_v2.csv', index=False, encoding='utf-8'); print('val_v2', len(v) + len(h))
'@)
}

# 1) profesor
$B = (Get-Content runs/mejor_b.args -Raw).Trim().Split(" ")
if (-not (Test-Path "models/candB_v2/metricas.json")) {
  Run "profesor candB_v2 (3 semillas)" "runs/log_candB_v2.txt" (@("src/train/entrenar_v5.py", "--train", "$D/train.csv", "--val", "runs/val_v2.csv", "--test", "$D/test.csv",
      "--adv", "$D/test_adversarial.csv", "--seeds", "42", "1337", "2026", "--peso_nuevos", "0", "--guardar_modelos", "--out", "models/candB_v2") + $B)
}

# 2) temperatura del profesor
if (-not (Test-Path "models/profV2/manifest.json")) {
  Run "temperatura profesor" "runs/log_profV2.txt" @("-c", @'
import sys, json, glob, numpy as np, pandas as pd, pathlib; sys.path.insert(0, '.')
from src.evaluation.comparar_fase3 import temperatura
pv = np.mean([np.load(f) for f in sorted(glob.glob('models/candB_v2/semilla_*/probs_val.npy'))], 0)
T = temperatura(pv, pd.read_csv('runs/val_v2.csv').label.values); pathlib.Path('models/profV2').mkdir(exist_ok=True)
json.dump({'version': 'profV2', 'descripcion': 'Profesor dataset 2.0.0: receta B x 3 semillas', 'componentes': ['candB_v2'], 'temperatura': round(T, 3), 'dataset': '2.0.0'}, open('models/profV2/manifest.json', 'w'), indent=2)
print('T =', T)
'@)
}

# 3) destilación
if (-not (Test-Path "models/v3.6.0-rc1/metricas_destilacion.json")) {
  Run "destilación v3.6.0-rc1 (3 semillas)" "runs/log_v360rc1.txt" (@("src/train/destilar.py", "--profesor", "models/profV2", "--out", "models/v3.6.0-rc1",
      "--val", "runs/val_v2.csv", "--seeds", "42", "1337", "2026", "--alfa", "0.5", "--T", "1") + $B)
}

# 4) selección de semilla por F1 en val_v2
if (-not (Test-Path "models/v3.6.0-rc1-sel/manifest_sel.json")) {
  Run "selección de semilla" "runs/log_sel_v360.txt" @("-c", @'
import json, shutil, pathlib
m = json.load(open('models/v3.6.0-rc1/metricas_destilacion.json', encoding='utf-8'))['semillas']
s = max(m, key=lambda k: m[k]['f1_val']); dst = pathlib.Path(f'models/v3.6.0-rc1-sel/semilla_{s}/modelo')
shutil.copytree(f'models/v3.6.0-rc1/semilla_{s}/modelo', dst, dirs_exist_ok=True)
json.dump({'semilla': s, 'regla': 'max F1 en val_v2', 'semillas': m}, open('models/v3.6.0-rc1-sel/manifest_sel.json', 'w'), indent=2); print('semilla elegida', s, m[s])
'@)
}

# 5) comparación final (una sola medición)
Run "comparación final" "runs/log_comparacion_v360.txt" @("src/evaluation/comparar_v2.py", "v3.4.0", "profV2", "v3.6.0-rc1-sel", "--solo-banco", "profR3", "v3.5.0-rc1-sel", "mbert-sv", "--salida", "v360_candidatos")
Log "=== FIN pipeline v3.6.0 ==="
