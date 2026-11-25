# -*- coding: utf-8 -*-
"""Fase 2 del plan: optimización de hiperparámetros con Optuna y VALIDACIÓN CRUZADA POR HILO (2 pliegues).
Cada prueba entrena 2 modelos (1 semilla): en cada pliegue se EXCLUYEN del entrenamiento todos los hilos de ese pliegue
y se evalúa en ellos; la métrica es el F1-macro de las predicciones agrupadas de ambos pliegues. El banco congelado NO se toca.
Espacio: lr, épocas, warmup, weight decay, peso de las filas de hilos, multiplicador de peso de clase para Odio+Amenazas.
Uso: python src/train/optuna_cv_hilo.py --pruebas 12"""
import argparse, json, subprocess, sys, time
from pathlib import Path
import numpy as np, pandas as pd, optuna
from sklearn.metrics import f1_score
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402
D = P.DATASET; OUT = P.RUNS / "optuna"; PY = sys.executable


def pliegues(tr):
    hil = tr[tr.origen == "real_hilo"]
    r = hil.groupby("plantilla_id").agg(n=("label", "size"), od=("label", lambda x: int((x == 2).sum())), am=("label", lambda x: int((x == 3).sum())))
    r["peso"] = r.od * 3 + r.am * 3 + r.n * 0.2; r = r.sort_values("peso", ascending=False); f = [[], []]; s = [0, 0]
    for h, row in r.iterrows():
        i = int(np.argmin(s)); f[i].append(h); s[i] += row.peso
    return f


def correr(params, fold_hilos, tag):
    tr = pd.read_csv(D / "train.csv"); ho = tr[tr.plantilla_id.isin(fold_hilos) & (tr.origen == "real_hilo")]
    ent = tr.drop(ho.index); d = OUT / tag; d.mkdir(parents=True, exist_ok=True)
    ent.to_csv(d / "train.csv", index=False); ho.to_csv(d / "holdout.csv", index=False)
    cmd = [PY, str(RAIZ / "src/train/entrenar_v5.py"), "--peso_nuevos", "0", "--seeds", "42", "--out", str(d / "run"), "--train", str(d / "train.csv"),
           "--val", str(D / "val.csv"), "--test", str(D / "test.csv"), "--adv", str(D / "test_adversarial.csv"), "--extra", f"ho={d / 'holdout.csv'}:texto_original",
           "--lr", str(params["lr"]), "--epocas", str(params["epocas"]), "--wd", str(params["wd"]), "--warmup", str(params["warmup"]),
           "--peso_hilos", str(params["peso_hilos"]), "--peso_clase_extra", str(params["peso_clase_extra"])]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p = np.load(d / "run/semilla_42/probs_extra_ho.npy").argmax(1); return ho.label.values, p


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pruebas", type=int, default=12); a = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    f = pliegues(pd.read_csv(D / "train.csv")); (OUT / "pliegues.json").write_text(json.dumps(f, ensure_ascii=False, indent=1)); print("pliegues:", [len(x) for x in f], flush=True)

    def objetivo(t):
        p = dict(lr=t.suggest_float("lr", 1e-5, 8e-5, log=True), epocas=t.suggest_int("epocas", 3, 6), wd=t.suggest_float("wd", 1e-3, 0.05, log=True),
                 warmup=t.suggest_float("warmup", 0.03, 0.15), peso_hilos=t.suggest_float("peso_hilos", 0.5, 3.0), peso_clase_extra=t.suggest_float("peso_clase_extra", 1.0, 2.0))
        t0 = time.time(); ys, ps = [], []
        for i, hs in enumerate(f):
            y, pr = correr(p, hs, f"t{t.number:02d}_f{i}"); ys.append(y); ps.append(pr)
        y, pr = np.concatenate(ys), np.concatenate(ps); fm = f1_score(y, pr, average="macro", labels=[0, 1, 2, 3], zero_division=0)
        rec = [float((pr[y == c] == c).mean()) for c in range(4)]; t.set_user_attr("recall", rec); t.set_user_attr("minutos", round((time.time() - t0) / 60, 1))
        print(f"prueba {t.number:02d}  F1-macro CV-hilo {fm:.4f}  recall {[round(x, 3) for x in rec]}  {p}", flush=True); return fm
    est = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=7), study_name="cv_hilo",
                              storage=f"sqlite:///{(OUT / 'estudio.db').as_posix()}", load_if_exists=True)  # reanudable tras una suspensión del equipo
    if not est.trials:
        est.enqueue_trial(dict(lr=5.73e-5, epocas=6, wd=0.0176, warmup=0.0929, peso_hilos=1.0, peso_clase_extra=1.0))  # receta actual como referencia
    hechas = len([t for t in est.trials if t.state.name == "COMPLETE"])
    est.optimize(objetivo, n_trials=max(0, a.pruebas - hechas))
    res = dict(mejor=est.best_params, f1_cv=est.best_value, referencia=sorted(est.trials, key=lambda t: t.number)[0].value, pruebas=[dict(n=t.number, f1=t.value, params=t.params, recall=t.user_attrs.get("recall")) for t in est.trials])
    (P.REPORTS_IMPROVEMENT / "optuna_cv_hilo.json").write_text(json.dumps(res, ensure_ascii=False, indent=2)); print("MEJOR:", res["mejor"], "F1", round(res["f1_cv"], 4), "| referencia (receta actual):", round(res["referencia"], 4))
if __name__ == "__main__":
    main()
