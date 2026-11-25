# -*- coding: utf-8 -*-
"""Auditoría de limpieza del dataset vigente (solo lectura). Uso: python src/data/auditar_dataset.py
Salida: reports/final/auditoria_dataset.md y .json
Comprueba: tamaños y composición, duplicados internos, conflictos de etiqueta, fugas exactas y casi exactas
(clave normalizada y n-gramas de 8 palabras) entre train y val/test/batería/banco/sonda, IDs repetidos,
plantillas sintéticas compartidas entre splits e hilos del banco presentes en train."""
import json, re, sys, unicodedata
from pathlib import Path
import pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402

def clave(t):
    t = unicodedata.normalize("NFKD", str(t).lower()); t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"https?://\S+|@\w+", " ", t); return re.sub(r"[^a-z0-9ñ]+", " ", t).strip()
def ngr(t, n=8):
    w = clave(t).split(); return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}

D, B = P.DATASET, P.FROZEN_BANK
tr, va, te = (pd.read_csv(D / f) for f in ["train.csv", "val.csv", "test.csv"])
adv = pd.read_csv(D / "test_adversarial.csv").rename(columns={"texto": "texto_original"})
bk = pd.concat([pd.read_csv(B / f"{k}.csv").assign(banco=k) for k in ["migrantes", "externo2", "militares", "xenofobia"]], ignore_index=True)
pr = pd.read_csv(P.AFFECTIVE_PROBE).rename(columns={"texto": "texto_original"})
vh, th = (pd.read_csv(D / f"{k}.csv", encoding="utf-8-sig") for k in ("val_hilos", "test_hilos")) if (D / "val_hilos.csv").exists() else (None, None)
conj = {"val": va, "test": te, "bateria": adv, "banco": bk, "sonda": pr, **({"val_hilos": vh, "test_hilos": th} if vh is not None else {})}
R, L = {}, ["# Auditoría de limpieza del dataset v1.9.0", ""]

# 1. composición
R["tamanos"] = {k: len(v) for k, v in {"train": tr, **conj}.items()}
R["clases"] = {k: v.label.value_counts().sort_index().to_dict() for k, v in {"train": tr, "val": va, "test": te, "banco": bk}.items()}
real = tr.origen.isin(["real", "real_hilo", "caso_dificil"])
R["origen_train"] = {"real_etapa1": int((tr.origen == "real").sum()), "real_hilo": int((tr.origen == "real_hilo").sum()),
                     "caso_dificil": int((tr.origen == "caso_dificil").sum()), "sintetico": int((~real).sum())}
R["plataforma_train"] = tr.Plataforma.value_counts().to_dict(); R["validado_train"] = tr.validado.value_counts().to_dict()
R["origen_val_test"] = {"val": va.origen.value_counts().to_dict(), "test": te.origen.value_counts().to_dict()}

# 2. duplicados internos y conflictos
ktr = tr.texto_original.map(clave)
R["dup_exactos_train"] = int(tr.texto_original.duplicated().sum()); R["dup_normalizados_train"] = int(ktr.duplicated().sum())
g = tr.assign(k=ktr).groupby("k").label.nunique(); R["conflictos_etiqueta_train"] = int((g > 1).sum())
R["ejemplos_conflicto"] = tr.assign(k=ktr)[ktr.isin(g[g > 1].index)].sort_values("texto_original")[["texto_original", "label", "origen"]].head(12).values.tolist()
R["ids_repetidos_train"] = int(tr.ID.dropna().duplicated().sum())

# 3. fugas
Ktr, Etr = set(ktr), set(tr.texto_original.astype(str))
G = set().union(*[ngr(t) for t in tr.texto_original])
R["fugas"] = {}
for n, d in conj.items():
    t = d.texto_original.astype(str)
    R["fugas"][n] = {"exactas": int(t.isin(Etr).sum()), "normalizadas": int(t.map(clave).isin(Ktr).sum()),
                     "ngrama8": int(t.map(lambda x: bool(ngr(x) & G)).sum()), "n": len(d)}
R["fugas"]["val_vs_test"] = int(te.texto_original.map(clave).isin(set(va.texto_original.map(clave))).sum())
R["ids_train_en_val_test"] = int(tr.ID.isin(set(va.ID) | set(te.ID)).sum())
pl = lambda d: set(d.plantilla_id.dropna().astype(str))
R["plantillas_compartidas"] = {"train_val": sorted(pl(tr) & pl(va))[:20], "train_test": sorted(pl(tr) & pl(te))[:20]}
R["hilos_banco_en_train"] = sorted(set(bk.hilo.astype(str)) & pl(tr))
if vh is not None: R["hilos_eval_v2_en_train"] = sorted((set(vh.hilo) | set(th.hilo)) - {h for h in set(vh.hilo) | set(th.hilo) if str(h).startswith("busqueda_")} & pl(tr)); R["val_hilos_vs_test_hilos"] = int(th.texto_original.map(clave).isin(set(vh.texto_original.map(clave))).sum())
R["ejemplos_ngrama_test"] = te[te.texto_original.map(lambda x: bool(ngr(x) & G))].texto_original.head(5).tolist()
R["ejemplos_ngrama_banco"] = bk[bk.texto_original.map(lambda x: bool(ngr(x) & G))].texto_original.head(5).tolist()

(RAIZ / "reports/final").mkdir(parents=True, exist_ok=True)
(RAIZ / "reports/final/auditoria_dataset.json").write_text(json.dumps(R, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
