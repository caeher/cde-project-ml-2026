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
from src import paths as P  # noqa: E402
from src.features.normalization import normalizar, normalizar_agresivo  # noqa: E402

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
H = P.THREADS
BANCO_HILOS = {"militares_pandilleros", "xenofobia_federico"}  # del consenso externo 3 y 4; migrantes y externo 2 son sus propios archivos


def clave(s):
    s = unicodedata.normalize("NFKC", str(s)).lower(); s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"@\w+", " ", s); s = re.sub(r"[^\w\s]", " ", s); return re.sub(r"\s+", " ", s).strip()


from functools import lru_cache


@lru_cache(maxsize=None)
def _ck(t): return clave(t), clave(normalizar(str(t)))  # caché: el mismo texto se compara varias veces (mismo resultado, más rápido)


def claves(textos):
    out = set()
    for t in textos: out.update(_ck(t) if isinstance(t, str) else (clave(t), clave(normalizar(str(t)))))
    return out


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


# Política de la ronda 3 (dataset v1.9.0), fijada antes de entrenar: el volumen nuevo es sobre todo No Tóxico/Ofensivo, así que se
# conservan TODAS las Amenazas y el Odio y se limita lo demás por hilo para no ahogar las clases raras. Reproducible (semilla fija).
RONDA3 = {"max_nt_por_hilo": 40, "max_of_por_hilo": 25, "max_achis": 80, "semilla": 2027}
MEXICO = re.compile(r"m[eé]xico|cdmx|cruz azul|mariachi|veracruz|tri mayor|guadalajara|monterrey|chivas|liga mx|nuevo le[oó]n|am[eé]rica femenil|pumas|andaluc[ií]a|espa[nñ]a", re.I)


def ronda3(politica=RONDA3):
    """Filas con consenso de la ronda 3 (consenso_ronda3.csv) bajo la política anterior. Jerga: se excluye pais_dudoso=1 y textos con marcas de México/España,
    y «achis» (57 % de la jerga y no solo salvadoreño) se limita a max_achis. Devuelve (tabla como la de tabla(), resumen)."""
    cols = ["hilo", "texto", "label", "p0", "p1", "p2", "p3"]
    f = H / "labels" / "consenso_ronda3.csv"
    if not f.exists(): return pd.DataFrame(columns=cols), {}
    d = pd.read_csv(f, encoding="utf-8-sig", dtype={"ID": str}); d = d[d.consenso >= 0].copy()
    part = particion()
    if part:  # dataset v2.0.0: los hilos y textos de jerga reservados para val_hilos/test_hilos no entrenan
        d = d[~d.hilo.isin(part["val_hilos"] + part["test_hilos"]) & ~d.ID.isin(part["jerga_val_ids"] + part["jerga_test_ids"])].copy()
    p = votos(d, ["a", "b", "d"])
    for k in range(4): d[f"p{k}"] = p[:, k]
    d["label"] = d.consenso.astype(int)
    jerga = pd.concat([pd.read_csv(x, encoding="utf-8-sig", dtype=str) for x in sorted((P.X_THREADS / "phase3_jerga").glob("*.csv"))], ignore_index=True)
    es_j = d.hilo.str.startswith("busqueda_")
    excl = es_j & (d.ID.isin(jerga[jerga.pais_dudoso == "1"].ID) | d.texto.str.contains(MEXICO))
    s = politica["semilla"]; partes = []
    for _, g in d[~es_j].groupby("hilo"):
        partes.append(g[g.label >= 2])
        for c, tope in ((0, politica["max_nt_por_hilo"]), (1, politica["max_of_por_hilo"])):
            h = g[g.label == c]; partes.append(h.sample(min(len(h), tope), random_state=s))
    j = d[es_j & ~excl]; ach = j[j.hilo == "busqueda_achis"]
    partes.append(pd.concat([j[j.hilo != "busqueda_achis"], ach.sample(min(len(ach), politica["max_achis"]), random_state=s)]))
    r = pd.concat(partes, ignore_index=True)
    res = {"politica": politica, "con_consenso": len(d), "incluidas": len(r), "por_clase": {CLASES[c]: int((r.label == c).sum()) for c in range(4)},
           "jerga_excluidas_pais_o_mexico": int(excl.sum()), "jerga_incluidas": int(r.hilo.str.startswith("busqueda_").sum()),
           "jerga_NT_Ofensivo": [int(((r.label == c) & r.hilo.str.startswith("busqueda_")).sum()) for c in (0, 1)]}
    return r[cols].reset_index(drop=True), res


def particion():
    """Partición por hilos v2.0.0 (src/data/particion_v2.py). Vacía si el archivo no existe (reproduce v1.9.0)."""
    f = P.DATASET / "particion_hilos.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def reserva_v2():
    """val_hilos y test_hilos: textos de los hilos reservados + jerga reservada, solo con consenso A = B (las etiquetas más confiables)."""
    part = particion()
    if not part: return None, None
    d = pd.read_csv(H / "labels" / "consenso_ronda3.csv", encoding="utf-8-sig", dtype={"ID": str}); d = d[(d.consenso >= 0) & (d.a == d.b)].copy()
    p = votos(d, ["a", "b", "d"])
    for k in range(4): d[f"p{k}"] = p[:, k]
    d["label"] = d.consenso.astype(int); cols = ["ID", "hilo", "grupo", "texto", "label", "p0", "p1", "p2", "p3"]
    sel = lambda hil, ids: d[d.hilo.isin(hil) | d.ID.isin(ids)][cols].rename(columns={"texto": "texto_original"}).reset_index(drop=True)
    return sel(part["val_hilos"], part["jerga_val_ids"]), sel(part["test_hilos"], part["jerga_test_ids"])


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
    r3, res3 = ronda3()
    pool = pd.concat([pool, r3], ignore_index=True)  # al final: los ID HF-xxxxx de las filas anteriores no cambian
    if pool_extra is not None: pool = pd.concat([pool, pool_extra], ignore_index=True)
    construir.resumen_ronda3 = res3
    V4 = P.history("1.3.1"); V5 = P.history("1.4.0")
    base = pd.read_csv(V5 / "train.csv"); base = base[base.origen != "real_hilo"].copy()  # base sin octubre + casos difíciles
    val, test, adv = (pd.read_csv(V4 / f) for f in ["val.csv", "test.csv", "test_adversarial.csv"])
    prohibidas = claves(val.texto_original) | claves(test.texto_original) | claves(adv.texto)
    for b in banco.values(): prohibidas |= claves(b.texto)
    vh, th = reserva_v2()
    if vh is not None:  # sin duplicados entre conjuntos de evaluación; luego nada de ellos puede entrar a train
        ev = claves(val.texto_original) | claves(test.texto_original) | claves(adv.texto)
        for b in banco.values(): ev |= claves(b.texto)
        th = th[~th.texto_original.map(lambda t: bool(claves([t]) & ev))].reset_index(drop=True)
        vh = vh[~vh.texto_original.map(lambda t: bool(claves([t]) & (ev | claves(th.texto_original))))].reset_index(drop=True)
        prohibidas |= claves(vh.texto_original) | claves(th.texto_original)
        banco_v = dict(banco, val_hilos=vh.rename(columns={"texto_original": "texto"}), test_hilos=th.rename(columns={"texto_original": "texto"}))
    else:
        banco_v = banco
    choca = pool.texto.map(lambda t: bool(claves([t]) & prohibidas)); retiradas = int(choca.sum()); pool = pool[~choca]
    filas = [{"ID": f"HF-{i:05d}", "Plataforma": "X", "texto_original": r.texto, "texto_modelo": normalizar(r.texto), "texto_agresivo": normalizar_agresivo(r.texto),
              "clase": CLASES[int(r.label)], "label": int(r.label), "origen": "real_hilo", "plantilla_id": r.hilo, "validado": "CONSENSO",
              "p0": r.p0, "p1": r.p1, "p2": r.p2, "p3": r.p3} for i, r in enumerate(pool.itertuples(), 1)]
    train = pd.concat([base, pd.DataFrame(filas)], ignore_index=True)
    verificar(train, val, test, adv, banco_v)
    construir.reserva = (vh, th)
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
    if "--dry" in sys.argv:  # no escribe nada: muestra la composición que tendría el dataset
        print(json.dumps({"train_total": len(train), "train_por_clase": {CLASES[c]: int((train.label == c).sum()) for c in range(4)},
                          "ronda3": construir.resumen_ronda3, "retiradas": retiradas}, ensure_ascii=False, indent=2)); return
    out = P.DATASET; out.mkdir(exist_ok=True); bd = P.FROZEN_BANK; bd.mkdir(exist_ok=True)
    train.to_csv(out / "train.csv", index=False, encoding="utf-8", lineterminator="\r\n")
    for f, d in [("val.csv", val), ("test.csv", test), ("test_adversarial.csv", adv)]: d.to_csv(out / f, index=False, encoding="utf-8", lineterminator="\r\n")
    man = {"test_oficial": {"archivo": (out / "test.csv").relative_to(RAIZ).as_posix(), "sha256": sha(out / "test.csv"), "n": len(test)}}
    for k, b in banco.items():
        f = bd / f"{k}.csv"; b.rename(columns={"texto": "texto_original"}).to_csv(f, index=False, encoding="utf-8-sig", lineterminator="\r\n")
        man[k] = {"archivo": f.relative_to(RAIZ).as_posix(), "sha256": sha(f), "n": len(b), "clases": {CLASES[c]: int((b.label == c).sum()) for c in range(4)}}
    vh, th = construir.reserva
    if vh is not None:
        for n, x in [("val_hilos", vh), ("test_hilos", th)]:
            f = out / f"{n}.csv"; x.to_csv(f, index=False, encoding="utf-8-sig", lineterminator="\r\n")
            man[n] = {"archivo": f.relative_to(RAIZ).as_posix(), "sha256": sha(f), "n": len(x), "hilos": sorted(x.hilo.unique().tolist()),
                      "clases": {CLASES[c]: int((x.label == c).sum()) for c in range(4)}}
    (bd / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8", newline="\r\n")
    hil = train[train.origen == "real_hilo"]
    meta = {"version": P.DATASET_VERSION, "train_total": len(train), "base_y_casos": int((train.origen != "real_hilo").sum()), "filas_hilos_pool": len(hil), "hilos_en_pool": sorted(hil.plantilla_id.unique().tolist()),
            "pool_por_clase": {CLASES[c]: int((hil.label == c).sum()) for c in range(4)}, "train_por_clase": {CLASES[c]: int((train.label == c).sum()) for c in range(4)},
            "retiradas_por_coincidir_con_test_o_banco": retiradas, "banco_n": {k: len(v) for k, v in banco.items()}, "ronda3": construir.resumen_ronda3,
            "verificacion": "0 textos de train en val, test, val_hilos, test_hilos, batería ni banco congelado (crudo y normalizado)",
            "evaluacion_v2": {k: man[k] for k in ("val_hilos", "test_hilos") if k in man}}
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\r\n"); print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
