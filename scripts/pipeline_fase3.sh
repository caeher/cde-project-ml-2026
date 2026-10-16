#!/bin/bash
# Fase 3-5 encadenada, UNA tarea de GPU a la vez. Espera a que termine Optuna y luego: candidato A -> B -> C -> comparación -> destilación -> sesgos.
cd "$(dirname "$0")/.."; PY=.venv/Scripts/python.exe; D=data/dataset
while [ ! -f reports/improvement/optuna_cv_hilo.json ]; do sleep 30; done
echo "[$(date +%T)] Optuna listo"
$PY - <<'P'
import json; r=json.load(open('reports/improvement/optuna_cv_hilo.json',encoding='utf-8')); m=r['mejor']
open('runs/mejor_b.args','w').write(f"--lr {m['lr']} --epocas {m['epocas']} --wd {m['wd']} --warmup {m['warmup']} --peso_hilos {m['peso_hilos']} --peso_clase_extra {m['peso_clase_extra']}")
P
COM="--train $D/train.csv --val $D/val.csv --test $D/test.csv --adv $D/test_adversarial.csv --seeds 42 1337 2026 --peso_nuevos 0 --guardar_modelos"
echo "[$(date +%T)] candidato A"; $PY src/train/entrenar_v5.py $COM --peso_hilos 1.0 --out models/candA > runs/log_candA.txt 2>&1
echo "[$(date +%T)] candidato B"; $PY src/train/entrenar_v5.py $COM $(cat runs/mejor_b.args) --out models/candB > runs/log_candB.txt 2>&1
mkdir -p models/candC; echo '{"version":"candC","descripcion":"Ensamble de A y B (10 modelos)","componentes":["candA","candB"],"temperatura":1.0}' > models/candC/manifest.json
echo "[$(date +%T)] comparación"; $PY src/evaluation/comparar_fase3.py v3.3.0 candA candB candC > runs/log_comparacion_fase3.txt 2>&1
echo "[$(date +%T)] FIN fase 3"
