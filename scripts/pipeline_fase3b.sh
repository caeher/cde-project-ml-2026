#!/bin/bash
# Continuación: espera a que A termine su 3.ª semilla (2026), detiene su 4.ª, entrena B (3 semillas), crea C y compara.
cd "$(dirname "$0")/.."; PY=.venv/Scripts/python.exe; D=data/dataset
while [ ! -f models/candA/semilla_2026/modelo/config.json ]; do sleep 15; done
sleep 20; powershell -c "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'candA' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
rm -rf models/candA/_tmp_s7 models/candA/_tmp_s99; echo "[$(date +%T)] A (3 semillas) listo; candidato B"
$PY src/train/entrenar_v5.py --train $D/train.csv --val $D/val.csv --test $D/test.csv --adv $D/test_adversarial.csv --seeds 42 1337 2026 --peso_nuevos 0 --guardar_modelos $(cat runs/mejor_b.args) --out models/candB > runs/log_candB.txt 2>&1
mkdir -p models/candC; echo '{"version":"candC","descripcion":"Ensamble de A y B (6 modelos)","componentes":["candA","candB"],"temperatura":1.0}' > models/candC/manifest.json
echo "[$(date +%T)] B listo; comparación"; $PY src/evaluation/comparar_fase3.py v3.3.0 candA candB candC > runs/log_comparacion_fase3.txt 2>&1
echo "[$(date +%T)] FIN fase 3"
