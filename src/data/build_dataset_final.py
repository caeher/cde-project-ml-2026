# -*- coding: utf-8 -*-
"""Constructor ÚNICO del dataset final (plan de mejora, fase 0). Sustituye a build_dataset_v5/v6/v7/v8.

Salidas:
  data/dataset/{train,val,test,test_adversarial}.csv + metadata.json
      train = base sin octubre + casos difíciles + hilos del POOL con etiquetas de consenso (y etiquetas blandas p0..p3)
  data/evaluation/frozen_bank/{migrantes,externo2,militares,xenofobia}.csv + MANIFEST.json (SHA-256)
      el banco NUNCA entra a entrenamiento ni a selección.
Reglas:
  - se quita la publicación original de cada hilo (primera fila por hilo), que no es una respuesta;
  - se excluyen textos sin consenso (label = -1);
  - aborta si algún texto de train coincide (crudo o normalizado) con val, test, batería o cualquier conjunto del banco;
  - `--selftest` comprueba que el constructor detecta una fuga insertada a propósito.
Etiquetas blandas: fracción de anotadores independientes que votó cada clase (2 o 3 votos).
"""
import hashlib, json, re, sys, unicodedata
from pathlib import Path
import numpy as np, pandas as pd

RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar, normalizar_agresivo  # noqa: E402

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
H = RAIZ / "data/annotation/threads"
BANCO_HILOS = {"militares_pandilleros", "xenofobia_federico"}  # del consenso externo 3 y 4; migrantes y externo 2 son sus propios archivos


def clave(s):
    s = unicodedata.normalize("NFKC", str(s)).lower(); s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"@\w+", " ", s); s = re.sub(r"[^\w\s]", " ", s); return re.sub(r"\s+", " ", s).strip()


def claves(textos): return set(map(clave, textos)) | {clave(normalizar(str(t))) for t in textos}


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def votos(df, cols):
    v = df[cols].apply(pd.to_numeric, errors="coerce"); out = np.zeros((len(df), 4))
    for c in cols:
        for k in range(4): out[:, k] += (v[c].values == k)
    n = out.sum(1, keepdims=True); n[n == 0] = 1; return out / n


def tabla(archivo, col_texto, cols_voto, quitar_op=True):
    d = pd.read_csv(H / "labels" / archivo)
    d = d.sort_values("ID").copy(); d["texto"] = d[col_texto]; p = votos(d, cols_voto)
    for k in range(4): d[f"p{k}"] = p[:, k]
    d["label"] = d["consenso"]
    if quitar_op:
        d = d[d.groupby("hilo").cumcount() > 0]  # quita la publicación original (primera fila de cada hilo)
    return d[d.label >= 0][["hilo", "texto", "label", "p0", "p1", "p2", "p3"]].reset_index(drop=True)


def verificar(train, val, test, adv, banco):
    """Comprobación dura: ningún texto de train (crudo o normalizado) puede estar en val, test, batería ni banco."""
    kt = claves(train.texto_original)
    for n, t in [("val", val.texto_original), ("test", test.texto_original), ("bateria", adv.texto)] + [(k, v.texto) for k, v in banco.items()]:
        s = kt & claves(t); assert not s, f"FUGA train/{n}: {len(s)} textos"


def construir(salida_train=True, pool_extra=None):
    t1 = tabla("consenso_1155.csv", "texto_original", ["label", "ag", "d"])
    t2 = tabla("consenso_nuevos.csv", "texto", ["a", "b", "d"])
    t3 = tabla("consenso_externo3.csv", "texto", ["a", "b", "d"])
    t4 = tabla("consenso_externo4.csv", "texto", ["a", "b", "d"])
    t5 = tabla("consenso_externo2.csv", "texto", ["a", "b", "d"])
    t6 = tabla("consenso_migrantes.csv", "texto", ["a", "b", "d"])
    extra = [tabla(f.name, "texto", ["a", "b", "d"], quitar_op=False) for f in sorted((H / "labels").glob("consenso_fase1_r*.csv"))]  # fase 1 del plan: la publicación original ya se quitó al preparar los lotes
    todo = pd.concat([t1, t2, t3, t4] + extra, ignore_index=True)
    banco = {"militares": todo[todo.hilo == "militares_pandilleros"], "xenofobia": todo[todo.hilo == "xenofobia_federico"], "externo2": t5, "migrantes": t6}
    pool = todo[~todo.hilo.isin(BANCO_HILOS)].copy()
    if pool_extra is not None: pool = pd.concat([pool, pool_extra], ignore_index=True)
    V4 = RAIZ / "data/history/v1.3.1"; V5 = RAIZ / "data/history/v1.4.0"
    base = pd.read_csv(V5 / "train.csv"); base = base[base.origen != "real_hilo"].copy()  # base sin octubre + casos difíciles
    val, test, adv = (pd.read_csv(V4 / f) for f in ["val.csv", "test.csv", "test_adversarial.csv"])
    prohibidas = claves(val.texto_original) | claves(test.texto_original) | claves(adv.texto)
    for b in banco.values(): prohibidas |= claves(b.texto)
    choca = pool.texto.map(lambda t: bool(claves([t]) & prohibidas)); retiradas = int(choca.sum()); pool = pool[~choca]
    filas = [{"ID": f"HF-{i:05d}", "Plataforma": "X", "texto_original": r.texto, "texto_modelo": normalizar(r.texto), "texto_agresivo": normalizar_agresivo(r.texto),
              "clase": CLASES[int(r.label)], "label": int(r.label), "origen": "real_hilo", "plantilla_id": r.hilo, "validado": "CONSENSO",
              "p0": r.p0, "p1": r.p1, "p2": r.p2, "p3": r.p3} for i, r in enumerate(pool.itertuples(), 1)]
    train = pd.concat([base, pd.DataFrame(filas)], ignore_index=True)
    verificar(train, val, test, adv, banco)
    return train, val, test, adv, banco, pool, retiradas


def main():
    if "--selftest" in sys.argv:
        base = construir()[-1]
        t1 = tabla("consenso_externo4.csv", "texto", ["a", "b", "d"]); x = t1[t1.hilo == "xenofobia_federico"].iloc[:2].copy(); x["hilo"] = "lgbt_bandera"
        tr, val, te, adv, banco, pool, ret = construir(pool_extra=x)
        ok1 = ret == base + len(x) and not (claves(x.texto) & claves(tr.texto_original))
        print("SELFTEST 1 (un texto del banco camuflado como hilo del pool se RETIRA y se cuenta):", "OK" if ok1 else "FALLÓ", f"(retiradas {base} -> {ret})")
        mal = pd.concat([tr, tr.iloc[:1].assign(texto_original=banco["migrantes"].texto.iloc[0])], ignore_index=True)
        try:
            verificar(mal, val, te, adv, banco); print("SELFTEST 2 (la comprobación dura aborta ante una fuga en train): FALLÓ")
        except AssertionError as e:
            print("SELFTEST 2 (la comprobación dura aborta ante una fuga en train): OK ->", e)
        return
    train, val, test, adv, banco, pool, retiradas = construir()
    out = RAIZ / "data/dataset"; out.mkdir(exist_ok=True); bd = RAIZ / "data/evaluation/frozen_bank"; bd.mkdir(exist_ok=True)
    train.to_csv(out / "train.csv", index=False, encoding="utf-8")
    for f, d in [("val.csv", val), ("test.csv", test), ("test_adversarial.csv", adv)]: d.to_csv(out / f, index=False, encoding="utf-8")
    man = {"test_oficial": {"archivo": "data/dataset/test.csv", "sha256": sha(out / "test.csv"), "n": len(test)}}
    for k, b in banco.items():
        f = bd / f"{k}.csv"; b.rename(columns={"texto": "texto_original"}).to_csv(f, index=False, encoding="utf-8-sig")
        man[k] = {"archivo": f"data/evaluation/frozen_bank/{k}.csv", "sha256": sha(f), "n": len(b), "clases": {CLASES[c]: int((b.label == c).sum()) for c in range(4)}}
    (bd / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    hil = train[train.origen == "real_hilo"]
    meta = {"train_total": len(train), "base_y_casos": int((train.origen != "real_hilo").sum()), "filas_hilos_pool": len(hil), "hilos_en_pool": sorted(hil.plantilla_id.unique().tolist()),
            "pool_por_clase": {CLASES[c]: int((hil.label == c).sum()) for c in range(4)}, "train_por_clase": {CLASES[c]: int((train.label == c).sum()) for c in range(4)},
            "retiradas_por_coincidir_con_test_o_banco": retiradas, "banco_n": {k: len(v) for k, v in banco.items()},
            "verificacion": "0 textos de train en val, test, batería ni banco congelado (crudo y normalizado)"}
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"); print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
