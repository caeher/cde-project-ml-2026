# -*- coding: utf-8 -*-
"""
Figuras analíticas del documento de la Etapa II.

Todas se dibujan sobre fondo blanco y con tipografía serif, porque el destino es
un documento impreso y no una pantalla. Las de la Etapa I se generaron con tema
oscuro y quedan grises sobre el papel; aquí se corrige.

Paleta categórica validada con el verificador de la guía de visualización
(separación para daltonismo y visión normal por encima del umbral en todos los
pares adyacentes). Los tres trabajos de color se mantienen separados: hues
categóricos para identidad, una sola rampa azul para magnitud y un par
azul-rojo con gris central para polaridad.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

RAIZ = Path(__file__).resolve().parents[2]
FIG = RAIZ / "reports/figures/etapa2"
FIG.mkdir(parents=True, exist_ok=True)
S, A = RAIZ / "reports/v3_resultados", RAIZ / "reports/v3_arquitectura"

# ── parámetros del sistema de diseño ────────────────────────────────────
SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
RAMPA_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
POLO_FRIO, POLO_CALIDO, NEUTRO = "#2a78d6", "#e34948", "#f0efec"
TINTA, TINTA_2, TENUE = "#0b0b0b", "#52514e", "#8a8880"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 9,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#d8d6d0", "axes.labelcolor": TINTA_2,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": "#eceae4", "grid.linewidth": 0.8,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})
PCT = FuncFormatter(lambda v, _: f"{v:.3f}")


def _titulo(ax, t, sub=None):
    ax.set_title(t, color=TINTA, fontsize=10.5, fontweight="bold", loc="left", pad=14 if sub else 8)
    if sub:
        ax.text(0, 1.015, sub, transform=ax.transAxes, color=TENUE, fontsize=8.2, va="bottom")


def _guardar(fig, nombre):
    ruta = FIG / f"{nombre}.png"
    fig.savefig(ruta)
    plt.close(fig)
    print(f"  {ruta.name}")
    return ruta


def leer(p):
    return json.loads(Path(p).read_text())


# ═══════════════════════════════════════════════════════ 1. tokenizador
def fig_tokenizador():
    import pandas as pd
    d = pd.read_csv(A / "tokenizadores.csv").sort_values("fertilidad")
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    y = np.arange(len(d))
    col = [SERIE[2] if m == "RoBERTuito" else (SERIE[1] if m == "mBERT" else "#c9d6e6")
           for m in d.modelo]
    ax.barh(y, d.fertilidad, color=col, height=0.62, zorder=3)
    for i, (f, u) in enumerate(zip(d.fertilidad, d.unk_total)):
        ax.text(f + 0.012, i, f"{f:.3f}", va="center", fontsize=8.4, color=TINTA)
        if u > 100:
            ax.text(f + 0.062, i, f"{u} tokens desconocidos", va="center",
                    fontsize=7.8, color="#c0392b")
    ax.set_yticks(y); ax.set_yticklabels(d.modelo, fontsize=8.6)
    ax.set_xlim(1.35, 2.02); ax.xaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.set_xlabel("subtokens por palabra (menor es mejor)")
    _titulo(ax, "Coste de leer el dialecto: fragmentación por tokenizador",
            "medido sobre las 2,144 publicaciones reales del corpus")
    return _guardar(fig, "fig01_tokenizador")


# ═══════════════════════════════════════════════ 2. tamaño vs desempeño
def fig_arquitecturas():
    b = [r for r in leer(A / "bakeoff.json") if "val_f1_macro" in r]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    x = np.array([r["params"] / 1e6 for r in b])
    y = np.array([r["val_f1_macro"] for r in b])
    nom = [r["alias"] for r in b]
    bonito = {"xlmr_base": "XLM-R base", "twitter_xlmr": "TwitterXLM-R",
              "robertuito": "RoBERTuito", "bertin": "BERTIN", "beto": "BETO",
              "mbert": "mBERT", "xlmr_large": "XLM-R large"}
    dominio = {"twitter_xlmr", "robertuito"}
    for xi, yi, n in zip(x, y, nom):
        es_dom = n in dominio
        ax.scatter(xi, yi, s=120 if es_dom else 80,
                   color=SERIE[2] if es_dom else "#b9c6d8",
                   edgecolor="white", linewidth=1.6, zorder=4)
        dy = 0.006 if n not in ("robertuito", "beto") else -0.011
        ax.annotate(bonito[n], (xi, yi), textcoords="offset points",
                    xytext=(0, 9 if dy > 0 else -15), ha="center",
                    fontsize=8.2, color=TINTA if es_dom else TINTA_2,
                    fontweight="bold" if es_dom else "normal")
    ax.set_xscale("log")
    ax.set_xticks([100, 200, 300, 500])
    ax.set_xticklabels(["100 M", "200 M", "300 M", "500 M"])
    ax.set_xlabel("parámetros del modelo (escala logarítmica)")
    ax.set_ylabel("F1-macro en validación")
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(0.745, 0.845); ax.set_xlim(85, 700)
    ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.text(0.98, 0.06, "verde: preentrenado sobre redes sociales",
            transform=ax.transAxes, ha="right", fontsize=8, color=SERIE[2])
    _titulo(ax, "Escalar no resuelve el problema; el dominio del preentrenamiento sí",
            "siete arquitecturas con hiperparámetros idénticos sobre el mismo corpus")
    return _guardar(fig, "fig02_arquitecturas")


# ══════════════════════════════════ 3. interacción datos × capacidad
def fig_ablacion():
    tw = {r["alias"]: r["val_f1_macro"] for r in leer(A / "ablacion_twitter_xlmr.json")}
    ro = {r["alias"]: r["val_f1_macro"] for r in leer(A / "ablacion_robertuito.json")}
    etiquetas = ["corpus\nanterior", "dirigido\npeso 1.0", "dirigido\npeso 0.5",
                 "dirigido\npeso 0.25", "dirigido\ndos fases"]
    claves = ["b2_base", "v3_peso1.0", "v3_peso0.5", "v3_peso0.25", "v3_dosfases"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(claves))
    for datos, nombre, color in ((tw, "TwitterXLM-R  (278 M)", SERIE[1]),
                                 (ro, "RoBERTuito  (109 M)", SERIE[0])):
        v = [datos.get(k) for k in claves]
        ax.plot(x, v, "-o", color=color, linewidth=2, markersize=8,
                markeredgecolor="white", markeredgewidth=1.6, label=nombre, zorder=4)
        ax.annotate(f"{v[0]:.4f}", (x[0], v[0]), textcoords="offset points",
                    xytext=(-8, -4), ha="right", fontsize=8.2, color=color)
        ax.annotate(f"{v[-1]:.4f}", (x[-1], v[-1]), textcoords="offset points",
                    xytext=(8, -4), ha="left", fontsize=8.2, color=color)
    ax.set_xticks(x); ax.set_xticklabels(etiquetas, fontsize=8.3)
    ax.set_xlim(-0.55, len(claves) - 0.28)
    ax.set_ylabel("F1-macro en validación"); ax.yaxis.set_major_formatter(PCT)
    ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.6, loc="center right")
    _titulo(ax, "Los mismos datos ayudan al modelo pequeño y perjudican al grande",
            "el corpus sintético desplaza a quien tiene capacidad para memorizar sus plantillas")
    return _guardar(fig, "fig03_ablacion")


# ═══════════════════════════════════════════════════════════ 4. HPO
def fig_hpo():
    h = leer(A / "hpo_robertuito_mejor.json")["historial"]
    h = sorted(h, key=lambda r: r["trial"])
    f1 = np.array([r["val_f1_macro"] for r in h])
    mejor = np.maximum.accumulate(f1)
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax.axhline(0.8272, color=TENUE, linewidth=1.2, linestyle=(0, (4, 3)), zorder=2)
    ax.text(len(f1) - 0.3, 0.8272, "configuración por defecto  0.8272",
            fontsize=8, color=TENUE, va="bottom", ha="right")
    ax.plot(range(len(f1)), mejor, color=SERIE[0], linewidth=2,
            label="mejor acumulado", zorder=3)
    ax.scatter(range(len(f1)), f1, s=52, color="#b9c6d8", edgecolor="white",
               linewidth=1.4, zorder=4, label="prueba individual")
    k = int(np.argmax(f1))
    ax.scatter([k], [f1[k]], s=120, color=SERIE[2], edgecolor="white",
               linewidth=1.8, zorder=5)
    ax.annotate(f"mejor: {f1[k]:.4f}", (k, f1[k]), textcoords="offset points",
                xytext=(6, 8), fontsize=8.6, color=SERIE[2], fontweight="bold")
    ax.set_xlabel("prueba"); ax.set_ylabel("F1-macro en validación")
    ax.yaxis.set_major_formatter(PCT); ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.4, loc="lower right")
    _titulo(ax, "Veinte pruebas de optimización sobre el conjunto de validación",
            "el test no participa en la búsqueda; el rango entre la mejor y la peor es de 0.055")
    return _guardar(fig, "fig04_hpo")


# ═════════════════════════════════════════════ 5. validación cruzada
def fig_cv():
    cv = leer(A / "validacion_cruzada.json")
    v = [p["f1_macro"] for p in cv["por_pliegue"]]
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    ax.axvspan(cv["media"] - cv["desv"], cv["media"] + cv["desv"],
               color="#e8f0fb", zorder=1)
    ax.axvline(cv["media"], color=SERIE[0], linewidth=2, zorder=3)
    ax.text(cv["media"], len(v) - 0.35, f"  media {cv['media']:.4f} ± {cv['desv']:.4f}",
            color=SERIE[0], fontsize=8.6, va="center", fontweight="bold")
    y = np.arange(len(v))
    ax.scatter(v, y, s=95, color=SERIE[0], edgecolor="white", linewidth=1.7, zorder=4)
    for i, val in enumerate(v):
        ax.text(val, i - 0.34, f"{val:.4f}", ha="center", fontsize=8, color=TINTA_2)
    ax.set_yticks(y); ax.set_yticklabels([f"pliegue {p['pliegue']}" for p in cv["por_pliegue"]],
                                         fontsize=8.6)
    ax.set_ylim(-0.8, len(v) - 0.2)
    ax.set_xlabel("F1-macro sobre el pliegue de evaluación (solo texto real)")
    ax.xaxis.set_major_formatter(PCT); ax.xaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    _titulo(ax, "Validación cruzada estratificada de cinco pliegues",
            "los ejemplos sintéticos solo entrenan; cada pliegue se evalúa sobre publicaciones reales")
    return _guardar(fig, "fig05_validacion_cruzada")


# ═════════════════════════════════════════ 6. comparación con intervalos
def fig_comparacion():
    e = leer(S / "ensemble.json"); f = leer(S / "evaluacion_v3_final.json")["test"]
    filas = [
        ("Ensemble (Etapa II)", e["test"]["f1_macro"], e["test"]["ic_lo"], e["test"]["ic_hi"], True),
        ("RoBERTuito individual", f["f1_macro"], f["ic_lo"], f["ic_hi"], True),
        ("TwitterXLM-R, corpus anterior", 0.8302, 0.7940, 0.8633, False),
        ("XLM-R v1 (Etapa I)", 0.8058, 0.7665, 0.8420, False),
        ("XLM-R mitigado", 0.7887, 0.7486, 0.8257, False),
        ("mBERT v1 (Etapa I)", 0.7777, 0.7363, 0.8144, False),
        ("mBERT B2", 0.7610, 0.7172, 0.7983, False),
    ][::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.axvline(0.80, color=POLO_CALIDO, linewidth=1.4, linestyle=(0, (4, 3)), zorder=2)
    ax.text(0.7985, -0.72, "meta 0.80", color=POLO_CALIDO, fontsize=8.4,
            va="center", ha="right", fontweight="bold")
    for i, (n, v, lo, hi, cumple) in enumerate(filas):
        c = SERIE[0] if cumple else "#b9c6d8"
        ax.plot([lo, hi], [i, i], color=c, linewidth=2.4, solid_capstyle="round", zorder=3)
        ax.scatter([v], [i], s=95, color=c, edgecolor="white", linewidth=1.7, zorder=4)
        ax.text(hi + 0.004, i, f"{v:.4f}", va="center", fontsize=8.3,
                color=TINTA if cumple else TINTA_2,
                fontweight="bold" if cumple else "normal")
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([n for n, *_ in filas], fontsize=8.6)
    ax.set_ylim(-1.1, len(filas) - 0.4)
    ax.set_xlabel("F1-macro sobre el conjunto de prueba, con intervalo bootstrap del 95 %")
    ax.xaxis.set_major_formatter(PCT); ax.set_xlim(0.70, 0.925)
    ax.xaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    _titulo(ax, "Solo los sistemas de la Etapa II superan la meta\ncon el intervalo entero",
            "azul: el extremo inferior del intervalo también supera 0.80")
    return _guardar(fig, "fig06_comparacion")


# ═════════════════════════════════════════════ 7. matriz de confusión
def fig_confusion():
    f = leer(S / "evaluacion_v3_final.json")["test"]
    m = np.array(f["matriz"], dtype=float)
    cl = ["No Tóxico", "Ofensivo", "Odio", "Amenazas"]
    pr = m / m.sum(1, keepdims=True)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("azul", ["#ffffff"] + RAMPA_AZUL)
    fig, ax = plt.subplots(figsize=(4.9, 4.3))
    ax.imshow(pr, cmap=cmap, vmin=0, vmax=1)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{int(m[i, j])}\n{pr[i, j]*100:.0f}%", ha="center", va="center",
                    fontsize=8.4, color="white" if pr[i, j] > 0.55 else TINTA,
                    fontweight="bold" if i == j else "normal")
    ax.set_xticks(range(4)); ax.set_xticklabels(cl, fontsize=8.3, rotation=20, ha="right")
    ax.set_yticks(range(4)); ax.set_yticklabels(cl, fontsize=8.3)
    ax.set_xlabel("clase predicha"); ax.set_ylabel("clase real")
    ax.set_xticks(np.arange(-.5, 4), minor=True); ax.set_yticks(np.arange(-.5, 4), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    _titulo(ax, "Matriz de confusión del modelo final",
            "conjunto de prueba, n = 460; el porcentaje es sobre la fila")
    return _guardar(fig, "fig07_confusion")


# ═══════════════════════════════════════════════════════ 8. equidad
def fig_equidad():
    br = leer(S / "fairness.json")["brechas"]
    br = [b for b in br if b["dFPR"] is not None and "emoji" not in b["par"].lower()]
    nombres = {"Plataforma X vs Plataforma Facebook": "X  vs  Facebook",
               "Con jerga salvadoreña vs Sin jerga": "jerga local  vs  español estándar",
               "Sarcasmo: sí vs Sarcasmo: no": "con sarcasmo  vs  sin sarcasmo",
               "Ironía: sí vs Ironía: no": "con ironía  vs  sin ironía",
               "Contexto político: sí vs Contexto político: no": "político  vs  no político"}
    br = sorted(br, key=lambda b: b["dF1"])
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    y = np.arange(len(br))
    v = [b["dF1"] for b in br]
    ax.barh(y, v, color=[POLO_CALIDO if x < 0 else POLO_FRIO for x in v],
            height=0.56, zorder=3)
    ax.axvline(0, color=TINTA_2, linewidth=1)
    for i, (b, x) in enumerate(zip(br, v)):
        ax.text(x + (0.012 if x > 0 else -0.012), i, f"{x:+.3f}",
                va="center", ha="left" if x > 0 else "right", fontsize=8.3, color=TINTA)
    ax.set_yticks(y); ax.set_yticklabels([nombres.get(b["par"], b["par"]) for b in br],
                                         fontsize=8.6)
    ax.set_xlabel("diferencia de F1-macro entre los dos subgrupos")
    ax.set_xlim(-0.36, 0.24); ax.xaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    _titulo(ax, "Dónde el sistema trata peor a unos textos que a otros",
            "rojo: el primer subgrupo rinde peor; las figuras retóricas son la brecha mayor")
    return _guardar(fig, "fig08_equidad")


# ══════════════════════════════════════════════════════ 9. robustez
def fig_robustez():
    import pandas as pd
    sd = pd.read_csv(RAIZ / "reports/v2_auditoria/sonda_predicciones.csv")
    p_v3 = np.load(S / "logits_v3_final_sonda.npy").argmax(1)
    modelos = [("Etapa II", p_v3, SERIE[0]),
               ("mBERT B2", np.load(RAIZ / "reports/v2_auditoria/logits_mbert_b2_sonda.npy").argmax(1), SERIE[1]),
               ("XLM-R v1", np.load(RAIZ / "reports/v2_auditoria/logits_xlmr_v1_sonda.npy").argmax(1), "#b9c6d8")]
    fams = sorted(sd.familia.unique())
    corto = {f: f.split(". ", 1)[1] for f in fams}
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = np.arange(len(fams)); h = 0.25
    for k, (nom, pred, col) in enumerate(modelos):
        tasa = [(pred[sd.familia == f].__eq__(sd.esperado[sd.familia == f]).mean()) for f in fams]
        ax.barh(y + (1 - k) * h, tasa, height=h - 0.04, color=col, label=nom, zorder=3)
        if k == 0:
            for i, t in enumerate(tasa):
                ax.text(t + 0.014, i + h, f"{t*100:.0f}%", va="center",
                        fontsize=7.8, color=TINTA)
    ax.set_yticks(y); ax.set_yticklabels([corto[f] for f in fams], fontsize=8.4)
    ax.set_xlim(0, 1.16); ax.set_xticks([0, .25, .5, .75, 1])
    ax.set_xticklabels(["0", "25 %", "50 %", "75 %", "100 %"])
    ax.set_xlabel("aciertos sobre la sonda dirigida de 204 casos")
    ax.xaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.4, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.16))
    _titulo(ax, "Robustez ante ofuscación, amenazas disfrazadas y emojis",
            "casos construidos después del entrenamiento de los modelos anteriores")
    return _guardar(fig, "fig09_robustez")


# ═══════════════════════════════════════════════════ 10. evadibilidad
def fig_evadibilidad():
    pre = ["(ninguno)", "gracias, ", "qué onda, ", "todo bien, ", "mi hermano, ", "buena onda, "]
    v3 = [3, 5, 5, 7, 5, 7]
    v2 = [1, 20, 19, 17, 21, 17]
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    x = np.arange(len(pre)); w = 0.36
    ax.bar(x - w / 2, v2, w - 0.03, color=SERIE[1], label="Prototipo anterior (con filtro de reglas)", zorder=3)
    ax.bar(x + w / 2, v3, w - 0.03, color=SERIE[0], label="Etapa II (sin reglas)", zorder=3)
    for xi, a, b in zip(x, v2, v3):
        ax.text(xi - w / 2, a + 0.6, str(a), ha="center", fontsize=8.2, color=TINTA)
        ax.text(xi + w / 2, b + 0.6, str(b), ha="center", fontsize=8.2, color=TINTA)
    ax.set_xticks(x); ax.set_xticklabels([f"«{p.strip(', ')}»" if p != "(ninguno)" else p for p in pre],
                                         fontsize=8.4)
    ax.set_ylabel("amenazas reclasificadas como No Tóxico\n(de 100)")
    ax.set_ylim(0, 25); ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.4, loc="upper left")
    _titulo(ax, "Una palabra bastaba para desactivar la moderación del prototipo anterior",
            "cien amenazas precedidas de un marcador afectivo")
    return _guardar(fig, "fig10_evadibilidad")


# ═══════════════════════════════════════════════════ 11. calibración
def fig_calibracion():
    import pandas as pd
    te = pd.read_csv(RAIZ / "data/dataset_v3/test.csv")
    te.columns = [c.lstrip("﻿") for c in te.columns]
    L = np.load(S / "logits_v3_final_test.npy")
    P = np.exp(L - L.max(-1, keepdims=True)); P /= P.sum(-1, keepdims=True)
    conf, pred, y = P.max(1), P.argmax(1), te.label.values
    bins = np.linspace(0.25, 1.0, 7)
    cx, cy, n = [], [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.sum() >= 5:
            cx.append(conf[m].mean()); cy.append((pred[m] == y[m]).mean()); n.append(m.sum())
    fig, ax = plt.subplots(figsize=(4.9, 4.1))
    ax.plot([0.25, 1], [0.25, 1], color=TENUE, linewidth=1.2, linestyle=(0, (4, 3)),
            zorder=2, label="calibración perfecta")
    ax.plot(cx, cy, "-o", color=SERIE[0], linewidth=2, markersize=8,
            markeredgecolor="white", markeredgewidth=1.5, zorder=4, label="modelo final")
    for a, b, k in zip(cx, cy, n):
        ax.annotate(f"n={k}", (a, b), textcoords="offset points", xytext=(7, -10),
                    fontsize=7.4, color=TENUE)
    ax.set_xlim(0.25, 1.02); ax.set_ylim(0.25, 1.02)
    ax.set_xlabel("confianza declarada"); ax.set_ylabel("acierto observado")
    ax.xaxis.set_major_formatter(PCT); ax.yaxis.set_major_formatter(PCT)
    ax.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.2, loc="upper left")
    _titulo(ax, "El modelo se declara más seguro de lo que acierta",
            "error de calibración esperado 0.1214")
    return _guardar(fig, "fig11_calibracion")


# ═══════════════════════════════════ 12. el atajo sintáctico
def fig_atajo():
    """Antes y después del contrapeso, sobre la sonda de construcción."""
    fam = ["p(amenaza) en\nfrases inocuas", "p(amenaza) en\namenazas reales"]
    antes, despues = [0.532, 1.000], [0.016, 1.000]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    x = np.arange(2); w = 0.34
    ax.bar(x - w / 2, antes, w - 0.03, color=SERIE[1], label="antes del contrapeso", zorder=3)
    ax.bar(x + w / 2, despues, w - 0.03, color=SERIE[0], label="después", zorder=3)
    for xi, a, b in zip(x, antes, despues):
        ax.text(xi - w / 2, a + 0.02, f"{a:.1%}", ha="center", fontsize=8.4, color=TINTA)
        ax.text(xi + w / 2, b + 0.02, f"{b:.1%}", ha="center", fontsize=8.4, color=TINTA)
    ax.set_xticks(x); ax.set_xticklabels(fam, fontsize=8.8)
    ax.set_ylim(0, 1.16); ax.set_yticks([0, .25, .5, .75, 1])
    ax.set_yticklabels(["0", "25 %", "50 %", "75 %", "100 %"])
    ax.set_ylabel("probabilidad media de Amenazas/Violencia")
    ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.4, loc="upper left")
    _titulo(ax, "El contrapeso separa la construcción del verbo que la completa",
            "sonda de 24 frases inocuas y 10 amenazas que comparten portador")
    return _guardar(fig, "fig12_atajo")


TODAS = [fig_tokenizador, fig_arquitecturas, fig_ablacion, fig_hpo, fig_cv,
         fig_comparacion, fig_confusion, fig_equidad, fig_robustez,
         fig_evadibilidad, fig_calibracion, fig_atajo]

if __name__ == "__main__":
    print("figuras generadas:")
    for f in TODAS:
        f()
