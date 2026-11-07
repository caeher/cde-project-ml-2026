# -*- coding: utf-8 -*-
"""Puente entre Argilla y los formatos que el repo ya tiene (plan: docs/improvement/PLAN_mBERT.md, sección 3).

No tiene lógica de dataset: solo sube textos a Argilla y baja las respuestas a archivos que el repo ya sabe leer.

Tareas:
  validacion  Validación humana del test principal (prioridad A). A ciegas: sin sugerencias y sin la etiqueta LLM.
              Muestra fijada de antemano: todo Odio y Amenazas de test_hilos + val_hilos, más 300 No Tóxico y 300 Ofensivo
              estratificados por hilo (semilla 2026).
              bajar → data/annotation/threads/labels/validacion_humana.csv (ID,conjunto,hilo,label_llm,h1,h2,label_humano).
              Ese archivo NO lo lee build_dataset_final.py: no puede entrar al train. Lo usa comparar_v2.py --humano.
  desempate   Los textos sin_consenso de la ronda 3 y los consenso_c de Odio y Amenazas (prioridad B).
              bajar → blind/ronda3/lote_R3C_H01.csv (ID,texto) + salida_R3C_H01c.csv (ID,label).
              La respuesta humana entra como **C** (solo cuando los dos humanos coinciden) y consolidar_ronda3.py vuelve a
              decidir por mayoría de 3 sin cambiar código. El lote R3C_H01 se lee después de R3C_00x, así que C humano
              reemplaza a C LLM en esos textos. A y B (LLM) no se tocan.
  ronda4      Textos nuevos (--entrada CSV con ID,texto[,hilo]) con sugerencias de modelos (prioridad C).
              Orden: primero los textos donde los modelos discrepan. Argilla admite una sugerencia por pregunta: se sugiere el
              primer modelo de --sugerir y las predicciones de todos van en metadatos (pred_<modelo>).
              bajar → blind/ronda4/lote_<L>.csv + salida_<L>{a,b,c}.csv, un archivo por anotador humano.

Uso:
  python src/data/threads/argilla_io.py subir --tarea validacion
  python src/data/threads/argilla_io.py subir --tarea desempate
  python src/data/threads/argilla_io.py subir --tarea ronda4 --entrada nuevos.csv --sugerir mbert_v2 v3.4.0
  python src/data/threads/argilla_io.py bajar --tarea validacion|desempate|ronda4 [--lote R4_001]
  python src/data/threads/argilla_io.py muestra            # solo imprime la muestra de validación (no conecta)

Credenciales en .env (no se versiona): ARGILLA_API_URL, ARGILLA_API_KEY. Workspace: sv (o ARGILLA_WORKSPACE).
"""
import argparse, os, sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]  # mismo orden que el repo
SEMILLA = 2026
N_NT, N_OF = 300, 300
DATASETS = {"validacion": "sv_validacion_v2", "desempate": "sv_desempate_r3"}
LOTE_DESEMPATE = "R3C_H01"


# ---------------------------------------------------------------- muestras
def estratificada(df, n, semilla):
    """n filas repartidas en proporción al tamaño de cada hilo (orden aleatorio dentro del hilo, luego por fracción de rango)."""
    if len(df) <= n: return df
    d = df.sample(frac=1, random_state=semilla).copy()
    d["_f"] = (d.groupby("hilo").cumcount() + 0.5) / d.groupby("hilo").hilo.transform("size")
    return d.sort_values("_f", kind="stable").head(n).drop(columns="_f")


def muestra_validacion():
    leer = lambda f: pd.read_csv(P.DATASET / f"{f}.csv", encoding="utf-8-sig", dtype={"ID": str})
    d = pd.concat([leer("test_hilos").assign(conjunto="test_hilos"), leer("val_hilos").assign(conjunto="val_hilos")], ignore_index=True)
    assert not d.ID.duplicated().any(), "IDs repetidos entre test_hilos y val_hilos"
    m = pd.concat([d[d.label.isin([2, 3])], estratificada(d[d.label == 0], N_NT, SEMILLA), estratificada(d[d.label == 1], N_OF, SEMILLA)])
    return m[["ID", "conjunto", "hilo", "texto_original", "label"]].rename(columns={"texto_original": "texto", "label": "label_llm"}).sort_values("ID").reset_index(drop=True)


def muestra_desempate():
    c = pd.read_csv(P.THREAD_LABELS / "ronda3_consolidado.csv", encoding="utf-8-sig", dtype={"ID": str})
    m = c[(c.estado == "sin_consenso") | ((c.estado == "consenso_c") & c.consenso.isin([2, 3]))]
    return m[["ID", "hilo", "texto"]].assign(conjunto="desempate").sort_values("ID").reset_index(drop=True)


# ---------------------------------------------------------------- Argilla
def cliente():
    import argilla as rg
    try:
        from dotenv import load_dotenv; load_dotenv(RAIZ / ".env")
    except ImportError:
        pass
    url, key = os.getenv("ARGILLA_API_URL"), os.getenv("ARGILLA_API_KEY")
    if not url or not key: sys.exit("Faltan ARGILLA_API_URL / ARGILLA_API_KEY en .env")
    return rg, rg.Argilla(api_url=url, api_key=key), os.getenv("ARGILLA_WORKSPACE", "sv")


def ajustes(rg, metadatos):
    return rg.Settings(
        guidelines=(RAIZ / "docs" / "guia_anotacion.md").read_text(encoding="utf-8"),
        fields=[rg.TextField(name="texto", title="Texto")],
        questions=[rg.LabelQuestion(name="label", title="Clase", labels={str(i): c for i, c in enumerate(CLASES)})],
        metadata=[rg.TermsMetadataProperty(name=m) for m in metadatos],
        distribution=rg.TaskDistribution(min_submitted=2))


def crear(rg, client, ws, nombre, metadatos):
    if client.datasets(name=nombre, workspace=ws) is not None:
        sys.exit(f"El dataset {nombre} ya existe en {ws}. Bórralo en Argilla o usa otro --lote.")
    ds = rg.Dataset(name=nombre, workspace=ws, settings=ajustes(rg, metadatos), client=client); ds.create(); return ds


def sugerencias(modelos, textos):
    """Probabilidades con el mismo cargador que comparar_v2.py (normalizar() + max_len 128)."""
    from src.models.inference import probs_propio
    return {m: probs_propio(str(P.MODELS / m), textos) for m in modelos}


def subir(a):
    rg, client, ws = cliente()
    if a.tarea in ("validacion", "desempate"):
        m = muestra_validacion() if a.tarea == "validacion" else muestra_desempate()
        ds = crear(rg, client, ws, DATASETS[a.tarea], ["hilo", "conjunto"])
        recs = [rg.Record(id=r.ID, fields={"texto": str(r.texto)}, metadata={"hilo": str(r.hilo), "conjunto": r.conjunto}) for r in m.itertuples()]
    else:
        if not a.entrada or not a.sugerir: sys.exit("ronda4 necesita --entrada CSV y --sugerir modelo [modelo ...]")
        m = pd.read_csv(a.entrada, encoding="utf-8-sig", dtype={"ID": str})
        if "hilo" not in m: m["hilo"] = ""
        pr = sugerencias(a.sugerir, m.texto.astype(str).tolist())
        preds = np.stack([pr[k].argmax(1) for k in a.sugerir], 1)
        m["discrepan"] = (preds != preds[:, :1]).any(1); m["_conf"] = pr[a.sugerir[0]].max(1)
        orden = m.sort_values(["discrepan", "_conf"], ascending=[False, True]).index  # primero discrepancias y luego baja confianza
        ds = crear(rg, client, ws, f"sv_ronda4_{a.lote}", ["hilo", "discrepan"] + [f"pred_{k}" for k in a.sugerir])
        p0 = pr[a.sugerir[0]]; recs = []
        for i in orden:
            r = m.loc[i]; j = m.index.get_loc(i)
            meta = {"hilo": str(r.hilo), "discrepan": "si" if r.discrepan else "no", **{f"pred_{k}": CLASES[int(preds[j, q])] for q, k in enumerate(a.sugerir)}}
            recs.append(rg.Record(id=r.ID, fields={"texto": str(r.texto)}, metadata=meta,
                                  suggestions=[rg.Suggestion("label", str(int(p0[j].argmax())), score=float(p0[j].max()), agent=a.sugerir[0], type="model")]))
    ds.records.log(recs)
    print(f"{len(recs)} registros subidos a {ds.name} (workspace {ws}).")


def respuestas(client, ws, nombre):
    """DataFrame ID,user,label con las respuestas enviadas (submitted)."""
    ds = client.datasets(name=nombre, workspace=ws)
    if ds is None: sys.exit(f"No existe el dataset {nombre} en {ws}")
    filas, textos = [], {}
    for r in ds.records(with_responses=True):
        textos[str(r.id)] = r.fields["texto"]
        try: resp = r.responses["label"]
        except KeyError: resp = []
        for x in resp or []:
            if getattr(x.status, "value", x.status) == "submitted":
                filas.append((str(r.id), str(x.user_id), int(x.value)))
    return pd.DataFrame(filas, columns=["ID", "user", "label"]), textos


def votos(df, n=3):
    """Ancho: una columna por voto (h1, h2, …), ordenados por user_id dentro de cada texto."""
    df = df.sort_values(["ID", "user"]); df["k"] = df.groupby("ID").cumcount()
    w = df[df.k < n].pivot(index="ID", columns="k", values="label")
    w.columns = [f"h{k + 1}" for k in w.columns]
    for k in range(n):
        if f"h{k + 1}" not in w: w[f"h{k + 1}"] = np.nan
    return w.astype("Int64")


def bajar(a):
    _, client, ws = cliente()
    if a.tarea == "validacion":
        df, _ = respuestas(client, ws, DATASETS["validacion"]); w = votos(df, 2)
        m = muestra_validacion().drop(columns="texto").set_index("ID").join(w, how="left")
        h1, h2 = m.h1.astype("float").fillna(-1).astype(int), m.h2.astype("float").fillna(-2).astype(int)
        m["label_humano"] = np.where(h1 == h2, h1, -1)
        dst = P.THREAD_LABELS / "validacion_humana.csv"
        m.reset_index()[["ID", "conjunto", "hilo", "label_llm", "h1", "h2", "label_humano"]].to_csv(dst, index=False, encoding="utf-8-sig")
        print(f"{dst}: {len(m)} textos, {int((m.h1.notna() & m.h2.notna()).sum())} con 2 votos, {int((m.label_humano >= 0).sum())} con acuerdo humano")
    elif a.tarea == "desempate":
        df, tx = respuestas(client, ws, DATASETS["desempate"]); w = votos(df, 2)
        ok = w[(w.h1.astype("float").fillna(-1) == w.h2.astype("float").fillna(-2)).values]
        B = P.THREADS / "blind" / "ronda3"
        pd.DataFrame({"ID": list(tx), "texto": list(tx.values())}).sort_values("ID").to_csv(B / f"lote_{LOTE_DESEMPATE}.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame({"ID": ok.index, "label": ok.h1.astype(int).values}).to_csv(B / f"salida_{LOTE_DESEMPATE}c.csv", index=False)
        print(f"lote_{LOTE_DESEMPATE}: {len(tx)} textos; {len(ok)} con acuerdo humano → salida_{LOTE_DESEMPATE}c.csv. "
              f"Sin acuerdo humano: {len(w) - len(ok)} (conservan la C del LLM). Siguiente: consolidar_ronda3.py")
    else:
        df, tx = respuestas(client, ws, f"sv_ronda4_{a.lote}"); w = votos(df, 3)
        B = P.THREADS / "blind" / "ronda4"; B.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"ID": list(tx), "texto": list(tx.values())}).sort_values("ID").to_csv(B / f"lote_{a.lote}.csv", index=False, encoding="utf-8-sig")
        for k, s in zip(["h1", "h2", "h3"], "abc"):
            v = w[k].dropna()
            if len(v): pd.DataFrame({"ID": v.index, "label": v.astype(int).values}).to_csv(B / f"salida_{a.lote}{s}.csv", index=False)
        print(f"lote_{a.lote}: {len(tx)} textos, {len(w)} con al menos un voto → {B}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["subir", "bajar", "muestra"])
    ap.add_argument("--tarea", choices=["validacion", "desempate", "ronda4"], default="validacion")
    ap.add_argument("--entrada", help="ronda4: CSV con ID,texto[,hilo]")
    ap.add_argument("--sugerir", nargs="*", default=[], help="ronda4: carpetas de models/ (la primera da la sugerencia)")
    ap.add_argument("--lote", default="R4_001", help="ronda4: nombre del lote")
    a = ap.parse_args()
    if a.accion == "muestra":
        m = muestra_validacion() if a.tarea == "validacion" else muestra_desempate()
        print(m.groupby(["conjunto"] + (["label_llm"] if "label_llm" in m else [])).size().to_string(), f"\nTotal: {len(m)} · hilos: {m.hilo.nunique()}")
        return
    (subir if a.accion == "subir" else bajar)(a)


if __name__ == "__main__":
    main()
