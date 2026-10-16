# -*- coding: utf-8 -*-
"""Evalúa modelos públicos de odio/toxicidad en español, solos y COMBINADOS con el modelo propio.

Diseño sin fuga:
  - Stacker (regresión logística, C = 1, fijo) se entrena SOLO con val oficial (459) + hilos CECOT y Miss (439, consenso),
    que el modelo propio de referencia (v3.1.0) no vio al entrenar.
  - Se evalúa en conjuntos que NADIE vio: test oficial (460), hilo de migrantes (307, consenso), test externo 2 (fútbol, política,
    seguridad en El Salvador, consenso), más la prueba de vulgaridad afectiva.

CRITERIO DE ADOPCIÓN, fijado antes de ver resultados (referencia = v3.1.0 solo):
  (1) F1-macro sobre migrantes + externo 2 (agrupados) mejora con IC 95 % pareado que no cruza el cero;
  (2) test oficial: sin regresión significativa (McNemar p >= 0.05 si baja);
  (3) vulgaridad afectiva: >= 17/20 afectivas → No Tóxico y >= 16/18 insultos detectados.
Modelos externos (zero-shot, sin reentrenar): pysentimiento/robertuito-hate-speech, Hate-speech-CNERG/dehatebert-mono-spanish,
JonatanGk/roberta-base-bne-finetuned-hate-speech-offensive-spanish, bgonzalezbustamante/bert-spanish-toxicity.
"""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m, ic_delta  # noqa: E402
import app.api.main as M  # noqa: E402

EXT = ["pysentimiento/robertuito-hate-speech", "Hate-speech-CNERG/dehatebert-mono-spanish",
       "JonatanGk/roberta-base-bne-finetuned-hate-speech-offensive-spanish", "bgonzalezbustamante/bert-spanish-toxicity"]
CACHE = RAIZ / "runs/ext"; CACHE.mkdir(exist_ok=True, parents=True)
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def conjuntos():
    H = RAIZ / "data/hilos_reales"; V = RAIZ / "data/dataset_v6"; S = {}
    v = pd.read_csv(V / "val.csv"); S["val"] = (v.texto_original.tolist(), v.label.values)
    t = pd.read_csv(V / "test.csv"); S["test"] = (t.texto_original.tolist(), t.label.values)
    c = pd.read_csv(H / "etiquetas/consenso_1155.csv"); c = c[(c.consenso >= 0) & c.hilo.isin(["cecot", "miss_el_salvador"])]
    S["cm"] = (c.texto_original.tolist(), c.consenso.values)
    m = pd.read_csv(H / "test_externo_migrantes.csv"); S["mig"] = (m.texto_original.tolist(), m.label.values)
    e = pd.read_csv(H / "etiquetas/consenso_externo2.csv"); e = e[e.consenso >= 0]; S["ext2"] = (e.texto.tolist(), e.consenso.values)
    p = pd.read_csv(RAIZ / "data/hard_cases/probe_vulgaridad_afectiva_SOLO_EVALUAR.csv"); S["afec"] = (p.texto.tolist(), p.label.values)
    return S


@torch.no_grad()
def probs_ext(mid, textos):
    tok = AutoTokenizer.from_pretrained(mid); m = AutoModelForSequenceClassification.from_pretrained(mid).to(DEV).eval(); out = []
    multi = m.config.problem_type == "multi_label_classification"
    for i in range(0, len(textos), 32):
        enc = tok([str(t) for t in textos[i:i + 32]], return_tensors="pt", truncation=True, max_length=128, padding=True).to(DEV)
        lg = m(**enc).logits; out.append((torch.sigmoid(lg) if multi else torch.softmax(lg, -1)).cpu().numpy())
    return np.vstack(out)


@torch.no_grad()
def probs_propio(ruta, textos):
    from src.features.normalization import normalizar
    M._modelos.clear(); M.MODELOS = Path(ruta); M._cargar()
    tx = [normalizar(str(t)) for t in textos]; orden = np.argsort([len(t) for t in tx]); out = np.zeros((len(tx), 4))  # por lotes y ordenado por longitud: mismo resultado, mucho más rápido
    for i in range(0, len(tx), 64):
        idx = orden[i:i + 64]; enc = M._tok([tx[j] for j in idx], truncation=True, max_length=128, padding=True, return_tensors="pt").to(M._dev)
        out[idx] = np.mean([torch.softmax(m(**enc).logits.double(), -1).cpu().numpy() for m in M._modelos], 0)
    return out


def cache(nombre, fn):
    f = CACHE / (re.sub(r"[^\w.-]", "_", nombre) + ".npy")
    if f.exists(): return np.load(f)
    a = fn(); np.save(f, a); return a


def main():
    S = conjuntos(); print({k: len(v[1]) for k, v in S.items()})
    P = {}
    for ruta in ["models/v3.0.0", "models/v3.1.0", "models/v3.2.0-rc1"]:
        for k, (tx, _) in S.items(): P[(Path(ruta).name, k)] = cache(f"{Path(ruta).name}__{k}", lambda: probs_propio(ruta, tx))
    for mid in EXT:
        for k, (tx, _) in S.items(): P[(mid.split("/")[1], k)] = cache(f"{mid.split('/')[1]}__{k}", lambda: probs_ext(mid, tx))
    nombres_ext = [m.split("/")[1] for m in EXT]

    print("\n== 1. Cada modelo público SOLO (zero-shot), AUROC sobre test + migrantes + externo 2 ==")
    y = np.concatenate([S[k][1] for k in ["test", "mig", "ext2"]])
    for n in ["v3.1.0"] + nombres_ext:
        p = np.vstack([P[(n, k)] for k in ["test", "mig", "ext2"]])
        if n == "v3.1.0": tox, odio = 1 - p[:, 0], p[:, 2]
        elif n.startswith("robertuito"): tox, odio = np.maximum(p[:, 1], p[:, 2]), p[:, 0]
        elif n.startswith("dehatebert"): tox, odio = p[:, 1], p[:, 1]
        elif n.startswith("roberta-base-bne"): tox, odio = 1 - p[:, 2], p[:, 0]
        else: tox, odio = p[:, 1], p[:, 1]
        print(f"  {n:<42} AUROC tóxico (1-3 vs 0): {roc_auc_score(y > 0, tox):.3f} · AUROC odio (2 vs resto): {roc_auc_score(y == 2, odio):.3f}")

    def feat(version, ext, k):
        cols = [np.log(np.clip(P[(version, k)], 1e-6, 1))] + [P[(e, k)] for e in ext]; return np.hstack(cols)
    Xtr_sets = ["val", "cm"]; ytr = np.concatenate([S[k][1] for k in Xtr_sets])
    combos = {"v3.1.0 solo": ("v3.1.0", []), "v3.1.0 + robertuito-hate": ("v3.1.0", nombres_ext[:1]),
              "v3.1.0 + 4 modelos públicos": ("v3.1.0", nombres_ext), "solo 4 públicos (sin propio)": (None, nombres_ext)}
    pred = {}
    for nom, (ver, ex) in combos.items():
        if nom == "v3.1.0 solo":
            pred[nom] = {k: P[("v3.1.0", k)].argmax(1) for k in ["val", "test", "cm", "mig", "ext2", "afec"]}; continue
        f = (lambda k: feat(ver, ex, k)) if ver else (lambda k: np.hstack([P[(e, k)] for e in ex]))
        clf = LogisticRegression(C=1.0, max_iter=2000).fit(np.vstack([f(k) for k in Xtr_sets]), ytr)
        pred[nom] = {k: clf.predict(f(k)) for k in ["val", "test", "cm", "mig", "ext2", "afec"]}
    # ensambles propios sin entrenar (promedio de probabilidades)
    for nom, vs in {"promedio v3.1.0 + v3.2.0-rc1": ["v3.1.0", "v3.2.0-rc1"], "promedio v3.0.0 + v3.1.0 + v3.2.0-rc1": ["v3.0.0", "v3.1.0", "v3.2.0-rc1"]}.items():
        pred[nom] = {k: np.mean([P[(v, k)] for v in vs], 0).argmax(1) for k in ["val", "test", "cm", "mig", "ext2", "afec"]}

    print("\n== 2. Combinaciones (stacker entrenado con val + CECOT/Miss; evaluado en conjuntos no vistos) ==")
    yt, ym, ye = S["test"][1], S["mig"][1], S["ext2"][1]; yp = np.concatenate([ym, ye]); ref = pred["v3.1.0 solo"]
    refp = np.concatenate([ref["mig"], ref["ext2"]]); R = {}
    for nom, pr in pred.items():
        pp = np.concatenate([pr["mig"], pr["ext2"]])
        lo, hi, _ = ic_delta(yp, refp, pp); m1 = mcnemar(ref["test"] == yt, pr["test"] == yt); af = S["afec"][1]
        a_ok, i_ok = int((pr["afec"][af == 0] == 0).sum()), int((pr["afec"][af == 1] != 0).sum())
        R[nom] = dict(f1_test=f1m(yt, pr["test"]), f1_mig=f1m(ym, pr["mig"]), f1_ext2=f1m(ye, pr["ext2"]), f1_pool=f1m(yp, pp), d_pool=f1m(yp, pp) - f1m(yp, refp),
                      ic=[lo, hi], p_test=float(m1["p_exacta"]), afect=a_ok, ins=i_ok)
        print(f"  {nom:<40} test {R[nom]['f1_test']:.4f} | mig {R[nom]['f1_mig']:.4f} | ext2 {R[nom]['f1_ext2']:.4f} | agrupado {R[nom]['f1_pool']:.4f} (Δ {R[nom]['d_pool']:+.4f} [{lo:+.3f},{hi:+.3f}]) | afectivas {a_ok}/20 insultos {i_ok}/18")
    print("\nCRITERIO (1) mejora agrupada con IC>0 · (2) test sin regresión significativa · (3) afectivas>=17 e insultos>=16:")
    for nom, r in R.items():
        if nom == "v3.1.0 solo": continue
        ok1, ok2, ok3 = r["ic"][0] > 0, not (r["p_test"] < 0.05 and r["f1_test"] < R["v3.1.0 solo"]["f1_test"]), r["afect"] >= 17 and r["ins"] >= 16
        print(f"  {nom:<40} (1) {'sí' if ok1 else 'NO'} · (2) {'sí' if ok2 else 'NO'} · (3) {'sí' if ok3 else 'NO'} -> {'ADOPTAR' if ok1 and ok2 and ok3 else 'no adoptar'}")
        R[nom]["adoptar"] = bool(ok1 and ok2 and ok3)
    (RAIZ / "reports/combinacion_modelos.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
