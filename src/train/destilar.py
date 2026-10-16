# -*- coding: utf-8 -*-
"""Fase 4 del plan: destilar el ensamble ganador en UN solo RoBERTuito.

Profesor: promedio de probabilidades de los componentes (carpetas models/<v>/semilla_*/modelo) con la temperatura del manifest.
Estudiante: un RoBERTuito (misma receta que el candidato) entrenado con
    L = alfa * T^2 * KL(profesor_T || estudiante_T) + (1 - alfa) * CE(etiqueta dura, con etiquetas blandas de anotadores si existen)
sobre data/dataset_final/train.csv (+ textos sin etiquetar opcionales con la etiqueta blanda del profesor, solo regularización).
El banco congelado NO se usa. Selección del punto de parada: F1-macro en val oficial.

Uso: python src/train/destilar.py --profesor models/v3.3.0 --out models/v3.4.0 [--sin_etiquetar ruta.csv:columna]
Salida: <out>/semilla_<s>/modelo (formato que carga app/api/main.py sin manifest) + <out>/metricas_destilacion.json
"""
import argparse, json, random, shutil, sys, time
from pathlib import Path
import numpy as np, pandas as pd, torch
from torch import nn
from sklearn.metrics import f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, EarlyStoppingCallback,
                          Trainer, TrainingArguments)

RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar  # noqa: E402

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
BASE = "pysentimiento/robertuito-base-cased"; D = RAIZ / "data/dataset_final"


def f1m(y, p): return f1_score(y, p, average="macro", zero_division=0)
def softmax(x): e = np.exp(x - x.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)


def probs_profesor(ruta, textos):
    """Probabilidades del ensamble (sin calibrar; la temperatura se aplica después con el manifest)."""
    from src.evaluation.combinar_modelos import probs_propio
    man = RAIZ / ruta / "manifest.json"
    comp = json.loads(man.read_text(encoding="utf-8"))["componentes"] if man.exists() else [Path(ruta).name]
    return np.mean([probs_propio(f"models/{c}", textos) for c in comp], 0), (json.loads(man.read_text(encoding="utf-8"))["temperatura"] if man.exists() else 1.0)


class DS(torch.utils.data.Dataset):
    def __init__(self, enc, y, blando=None, w=None): self.enc, self.y, self.b, self.w = enc, np.asarray(y), blando, w
    def __len__(self): return len(self.y)
    def __getitem__(self, i):
        it = {k: v[i] for k, v in self.enc.items()}; it["labels"] = int(self.y[i])
        if self.b is not None: it["blando"] = self.b[i].astype(np.float32)
        if self.w is not None: it["peso_muestra"] = float(self.w[i])
        return it


class Colador(DataCollatorWithPadding):
    def __call__(self, feats):
        b_ = [f.pop("blando") for f in feats] if "blando" in feats[0] else None
        w_ = [f.pop("peso_muestra") for f in feats] if "peso_muestra" in feats[0] else None
        b = super().__call__(feats)
        if b_ is not None: b["blando"] = torch.tensor(np.stack(b_))
        if w_ is not None: b["peso_muestra"] = torch.tensor(w_, dtype=torch.float)
        return b


class TrainerDestilado(Trainer):
    def __init__(self, *a, alfa=0.7, T=2.0, pesos_clase=None, **k):
        super().__init__(*a, **k); self.alfa, self.T, self.pc = alfa, T, pesos_clase

    def compute_loss(self, model, inputs, return_outputs=False, **kw):
        y = inputs.pop("labels"); b = inputs.pop("blando", None); w = inputs.pop("peso_muestra", None)
        out = model(**inputs); z = out.logits; dev = z.device
        ce = nn.functional.cross_entropy(z, y, weight=self.pc.to(dev) if self.pc is not None else None, reduction="none")
        if b is not None:
            b = b.to(dev); kl = (b * (torch.log(b.clamp_min(1e-8)) - nn.functional.log_softmax(z / self.T, -1))).sum(-1) * self.T ** 2
            l = self.alfa * kl + (1 - self.alfa) * ce
        else: l = ce
        w = w.to(dev) if w is not None else torch.ones_like(l)
        loss = (l * w).sum() / w.sum().clamp_min(1e-8)
        return (loss, out) if return_outputs else loss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profesor", default="models/v3.3.0"); ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42]); ap.add_argument("--alfa", type=float, default=0.7); ap.add_argument("--T", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=5.73e-05); ap.add_argument("--epocas", type=int, default=6); ap.add_argument("--wd", type=float, default=0.0176)
    ap.add_argument("--warmup", type=float, default=0.093); ap.add_argument("--batch", type=int, default=32); ap.add_argument("--peso_hilos", type=float, default=1.0)
    ap.add_argument("--peso_clase_extra", type=float, default=1.0); ap.add_argument("--sin_etiquetar", default=None, help="ruta.csv:columna (pseudo-etiquetas del profesor)")
    ap.add_argument("--peso_sin_etiquetar", type=float, default=0.5); a = ap.parse_args()
    out = RAIZ / a.out; out.mkdir(parents=True, exist_ok=True)
    tr, va, te = (pd.read_csv(D / f) for f in ["train.csv", "val.csv", "test.csv"])
    tok = AutoTokenizer.from_pretrained(BASE); enc = lambda s: tok([str(t) for t in s], truncation=True, max_length=128)
    # --- soft labels del profesor sobre train (texto_original -> normalizar dentro de probs_propio)
    cache = out / "profesor_probs_train.npy"
    textos = tr.texto_original.tolist(); extra_t = []
    if a.sin_etiquetar:
        ruta, col = a.sin_etiquetar.rsplit(":", 1); extra_t = pd.read_csv(RAIZ / ruta)[col].dropna().astype(str).tolist()
    if cache.exists() and len(np.load(cache)) == len(textos) + len(extra_t): P = np.load(cache); T_prof = json.loads((out / "profesor.json").read_text())["T"]
    else:
        P, T_prof = probs_profesor(a.profesor, textos + extra_t); np.save(cache, P); (out / "profesor.json").write_text(json.dumps({"T": T_prof, "profesor": a.profesor}))
    z = np.log(np.clip(P, 1e-12, 1)); soft = softmax(z / (T_prof * a.T))        # profesor calibrado y suavizado
    # mezcla con etiquetas blandas de anotadores donde existen (filas real_hilo)
    pk = tr[["p0", "p1", "p2", "p3"]].values if "p0" in tr.columns else None
    if pk is not None:
        ok = ~np.isnan(pk).any(1) & (pk.sum(1) > 0)
        s_tr = soft[:len(tr)].copy(); s_tr[ok] = 0.5 * s_tr[ok] + 0.5 * pk[ok]; soft = np.vstack([s_tr, soft[len(tr):]]) if len(extra_t) else s_tr
    origen = tr.origen.astype(str); w_tr = np.where(origen.isin(["real_hilo", "caso_dificil"]), a.peso_hilos, np.where(origen.eq("real"), 1.0, 0.75))
    cnt = np.bincount(tr.label.values, minlength=4); pc = torch.tensor(len(tr) / (4 * cnt), dtype=torch.float); pc[2:] *= a.peso_clase_extra
    X = tr.texto_modelo.astype(str).tolist() + [normalizar(t) for t in extra_t]
    y = np.concatenate([tr.label.values, soft[len(tr):].argmax(1) if len(extra_t) else np.zeros(0, int)])
    w = np.concatenate([w_tr, np.full(len(extra_t), a.peso_sin_etiquetar)])
    d_tr = DS(enc(X), y, soft, w); d_va = DS(enc(va.texto_modelo), va.label.values); d_te = DS(enc(te.texto_modelo), te.label.values)
    print(f"estudiante: {len(y)} filas ({len(extra_t)} sin etiquetar) | profesor {a.profesor} T={T_prof} | alfa {a.alfa} T_dest {a.T}", flush=True)
    res = {}
    for s in a.seeds:
        ds = out / f"semilla_{s}"
        if (ds / "modelo").exists(): print("ya estaba", s); continue
        random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s); t0 = time.time()
        m = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=4, id2label=dict(enumerate(CLASES)), label2id={c: i for i, c in enumerate(CLASES)})
        ta = TrainingArguments(output_dir=str(out / f"_tmp_s{s}"), num_train_epochs=a.epocas, learning_rate=a.lr, per_device_train_batch_size=a.batch, per_device_eval_batch_size=32,
                               warmup_steps=max(1, int(a.warmup * a.epocas * len(y) / a.batch)), weight_decay=a.wd, eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
                               metric_for_best_model="f1_macro", greater_is_better=True, save_total_limit=1, logging_steps=100, report_to=[], seed=s, disable_tqdm=True,
                               remove_unused_columns=False, fp16=torch.cuda.is_available(), dataloader_pin_memory=False)
        t = TrainerDestilado(model=m, args=ta, train_dataset=d_tr, eval_dataset=d_va, data_collator=Colador(tok), alfa=a.alfa, T=a.T, pesos_clase=pc,
                             compute_metrics=lambda e: {"f1_macro": f1m(e.label_ids, e.predictions.argmax(-1))}, callbacks=[EarlyStoppingCallback(early_stopping_patience=2)])
        t.train(); ds.mkdir(parents=True, exist_ok=True)
        pv, pt = (softmax(t.predict(d).predictions.astype(np.float64)) for d in (d_va, d_te))
        np.save(ds / "probs_val.npy", pv); np.save(ds / "probs_test.npy", pt)
        res[s] = {"f1_val": f1m(va.label.values, pv.argmax(1)), "f1_test": f1m(te.label.values, pt.argmax(1)), "minutos": round((time.time() - t0) / 60, 1)}
        t.save_model(str(ds / "modelo")); tok.save_pretrained(str(ds / "modelo")); shutil.rmtree(out / f"_tmp_s{s}", ignore_errors=True)
        print(f"semilla {s}:", res[s], flush=True); del m, t; torch.cuda.empty_cache()
    (out / "metricas_destilacion.json").write_text(json.dumps({"config": vars(a), "semillas": res}, ensure_ascii=False, indent=2, default=float))


if __name__ == "__main__":
    main()
