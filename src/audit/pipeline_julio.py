# -*- coding: utf-8 -*-
"""
Reimplementación del pipeline de 4 niveles de Julio (Prototipo V2) tal como
queda especificado en config_umbrales.json + estadisticas3.ipynb, y prueba de
evadibilidad del filtro de expresiones regulares.
"""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix

RAIZ = Path("/home/willian/ues/esp/proyecto"); S = RAIZ / "reports/v2_auditoria"
MIT = RAIZ / "Métricas de Evaluación/2v/_extraido/prototipoV2/02_modelo_prototipo/modelo_mitigado"
CFG = json.loads((MIT / "config_umbrales.json").read_text())
U = CFG["umbrales"]
UMBRALES = [U["No_Tóxico"], U["Lenguaje_Ofensivo"], U["Discurso_de_Odio"], U["Amenazas_o_Violencia"]]
PATRONES = [re.compile(p, re.IGNORECASE) for p in CFG["patrones_afectivos_jerga"]]
CL = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]


def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)


def nivel2_umbrales(P):
    """Cascada tal como está escrita en estadisticas3.ipynb: AV -> DO -> LO -> NT."""
    out = []
    for p in P:
        if p[3] >= UMBRALES[3]:   out.append(3)
        elif p[2] >= UMBRALES[2]: out.append(2)
        elif p[1] >= UMBRALES[1]: out.append(1)
        else:                     out.append(0)
    return np.array(out)


def nivel3_regex(pred, textos):
    """Reasigna a No Tóxico todo lo clasificado como Ofensivo que case un patrón."""
    out = pred.copy(); tocados = []
    for i, (p, t) in enumerate(zip(pred, textos)):
        if p == 1 and any(rx.search(t) for rx in PATRONES):
            out[i] = 0; tocados.append(i)
    return out, tocados


@torch.no_grad()
def logits(textos, tok, mod, dev, bs=32):
    o = []
    for i in range(0, len(textos), bs):
        enc = tok(textos[i:i+bs], return_tensors="pt", truncation=True, max_length=128, padding=True).to(dev)
        o.append(mod(**enc).logits.float().cpu().numpy())
    return np.concatenate(o, 0)


def main():
    test = pd.read_csv(RAIZ / "data/dataset_b2/test.csv"); test.columns=[c.lstrip("﻿") for c in test.columns]
    adv  = pd.read_csv(RAIZ / "data/dataset_b2/test_adversarial.csv"); adv.columns=[c.lstrip("﻿") for c in adv.columns]
    y = test["label"].values

    Pt = softmax(np.load(S / "logits_xlmr_mit_test.npy"))
    txt = test["texto_modelo"].astype(str).tolist()

    n1 = Pt.argmax(1)
    n2 = nivel2_umbrales(Pt)
    n3, tocados = nivel3_regex(n2, txt)

    print("=== PIPELINE DE JULIO SOBRE test.csv (n=460) ===")
    print(f"{'nivel':42s} {'F1-macro':>9s} {'Acc':>8s}")
    for nom, p in [("1. argmax del modelo mitigado", n1),
                   ("2. + umbrales por clase", n2),
                   ("3. + filtro regex", n3)]:
        print(f"{nom:42s} {f1_score(y,p,average='macro',zero_division=0):9.4f} {accuracy_score(y,p):8.4f}")
    print(f"\nregex tocó {len(tocados)} textos del test")

    # FPR binario y por jerga en cada nivel
    print(f"\n{'nivel':42s} {'FPR bin':>8s} {'FPR jerga':>10s} {'FPR nojerga':>12s}")
    jer = (test["n_jerga"] > 0).values
    for nom, p in [("1. argmax", n1), ("2. umbrales", n2), ("3. regex", n3)]:
        neg = y == 0
        fpr = (p[neg] != 0).mean()
        fj = (p[neg & jer] != 0).mean(); fn = (p[neg & ~jer] != 0).mean()
        print(f"{nom:42s} {fpr:8.4f} {fj:10.4f} {fn:12.4f}")

    # Recalls declarados
    print("\nRecall por clase (nivel 3) vs. lo publicado:")
    pub = {2: 0.8105, 3: 0.8072}
    for c in range(4):
        r = (n3[y == c] == c).mean()
        extra = f"   publicado {pub[c]:.4f}" if c in pub else ""
        print(f"  {CL[c]:20s} {r:.4f}{extra}")

    # ---------------- EVADIBILIDAD ----------------
    print("\n=== PRUEBA DE EVADIBILIDAD DEL FILTRO REGEX ===")
    tok = AutoTokenizer.from_pretrained(str(MIT))
    mod = AutoModelForSequenceClassification.from_pretrained(str(MIT)); mod.eval()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); mod.to(dev)

    # casos de amenaza: grupo C + amenazas del grupo G + amenazas reales del test
    amenazas = pd.concat([
        adv[(adv.grupo_de_prueba.str.startswith("C.")) & (adv.label_esperado == 3)][["texto_normalizado"]].rename(columns={"texto_normalizado":"t"}),
        adv[(adv.grupo_de_prueba.str.startswith("G.")) & (adv.label_esperado == 3)][["texto_normalizado"]].rename(columns={"texto_normalizado":"t"}),
    ], ignore_index=True)
    amenazas["fuente"] = ["C"]*11 + ["G"]*6
    reales = test[test.label == 3][["texto_modelo"]].rename(columns={"texto_modelo":"t"}).copy()
    reales["fuente"] = "test_real"
    amenazas = pd.concat([amenazas, reales], ignore_index=True)

    PREFIJOS = ["", "gracias, ", "qué onda, ", "todo bien, ", "te quiero pero ", "mi hermano, ", "buena onda, "]
    filas = []
    for pre in PREFIJOS:
        tx = [pre + t for t in amenazas["t"].tolist()]
        P = softmax(logits(tx, tok, mod, dev))
        p2 = nivel2_umbrales(P); p3, _ = nivel3_regex(p2, tx)
        for i, t in enumerate(tx):
            filas.append(dict(prefijo=pre or "(ninguno)", fuente=amenazas["fuente"][i],
                              texto=t, n1=int(P[i].argmax()), n2=int(p2[i]), n3=int(p3[i])))
    ev = pd.DataFrame(filas)
    ev.to_csv(S / "evadibilidad_julio.csv", index=False, encoding="utf-8-sig")

    print(f"\nCasos de amenaza evaluados: {len(amenazas)} (11 grupo C, 6 grupo G, {len(reales)} amenazas reales del test)")
    print(f"{'prefijo':16s} {'->NoTóxico n1':>14s} {'n2':>8s} {'n3 (final)':>12s} {'perdidas vs base':>18s}")
    base = (ev[ev.prefijo == "(ninguno)"]["n3"] == 0).sum()
    for pre in PREFIJOS:
        e = ev[ev.prefijo == (pre or "(ninguno)")]
        a, b, c = (e.n1 == 0).sum(), (e.n2 == 0).sum(), (e.n3 == 0).sum()
        print(f"{(pre or '(ninguno)'):16s} {a:>14d} {b:>8d} {c:>12d} {c-base:>+18d}")

    print("\nEjemplos de amenazas convertidas en No Tóxico por el prefijo «gracias, »:")
    g = ev[(ev.prefijo == "gracias, ") & (ev.n3 == 0)]
    bs = ev[(ev.prefijo == "(ninguno)")].reset_index(drop=True)
    for _, r in g.head(15).iterrows():
        print(f"  · {r['texto'][:78]}")
    print(f"\n(total {len(g)} de {len(amenazas)} amenazas neutralizadas con «gracias, »)")


if __name__ == "__main__":
    main()
