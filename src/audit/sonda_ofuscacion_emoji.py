# -*- coding: utf-8 -*-
"""
Sonda dirigida: ofuscación de groserías, amenazas de muerte y emojis.

Construida aparte de la batería de 144 para que ningún caso pueda haber sido
visto en entrenamiento. Se evalúa sobre los cuatro checkpoints y, además, sobre
el pipeline completo de Julio (umbrales + regex).
"""
import json, re
from pathlib import Path
import numpy as np, pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

RAIZ = Path("/home/willian/ues/esp/proyecto"); S = RAIZ / "reports/v2_auditoria"
E = RAIZ / "Métricas de Evaluación/2v/_extraido"
MODS = {
    "mbert_v1": E / "mbert_v1/mbert-sv",
    "mbert_b2": E / "metricas-proyecto-ml/models/mbert-sv",
    "xlmr_v1":  RAIZ / "Métricas de Evaluación/Para modelo XLMR/02_modelo_prototipo/modelo_entrenado",
    "xlmr_mit": E / "prototipoV2/02_modelo_prototipo/modelo_mitigado",
}
CL = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]

CASOS = []
def add(fam, base, var, texto, esp):
    CASOS.append(dict(familia=fam, base=base, variante=var, texto=texto, esperado=esp))

# --- 1. Ofuscación de groserías: misma frase, 8 disfraces ---
BASES_OF = [
    ("Callate ya, puta", 1, "puta"),
    ("Esas viejas son unas putas", 1, "putas"),
    ("Qué pendejo sos", 1, "pendejo"),
    ("Sos un cerote de mierda", 1, "mierda"),
    ("Andá a la verga", 1, "verga"),
    ("Qué culero el tipo", 1, "culero"),
]
DISFRAZ = {
    "asterisco":  lambda p: p[0] + "*" * (len(p) - 2) + p[-1],
    "arroba":     lambda p: p.replace("a", "@"),
    "numeral":    lambda p: p.replace("o", "#").replace("e", "#"),
    "leet_i":     lambda p: p.replace("i", "1").replace("e", "3").replace("a", "4").replace("o", "0"),
    "leet_s":     lambda p: p.replace("s", "5").replace("t", "7"),
    "punto":      lambda p: ".".join(p),
    "espaciado":  lambda p: " ".join(p),
    "repeticion": lambda p: p[:2] + p[1] * 3 + p[2:],
    "acento":     lambda p: p.replace("a", "á").replace("e", "é").replace("o", "ó"),
    "mayus":      lambda p: p.upper(),
}
for frase, esp, pal in BASES_OF:
    add("1. Ofuscación de groserías", frase, "original", frase, esp)
    for nom, fn in DISFRAZ.items():
        add("1. Ofuscación de groserías", frase, nom, frase.replace(pal, fn(pal)), esp)

# --- 2. Amenazas de muerte, literales y ofuscadas ---
BASES_AM = [
    ("Te voy a matar", "matar"),
    ("Voy a ir a tu casa a matarte", "matar"),
    ("Ese hijueputa merece morir", "morir"),
    ("Hay que quemarlos vivos a todos", "quemar"),
    ("Te voy a partir la cara cuando te vea", "partir"),
    ("Ojalá te maten", "maten"),
]
for frase, pal in BASES_AM:
    add("2. Amenazas de muerte", frase, "original", frase, 3)
    for nom, fn in DISFRAZ.items():
        add("2. Amenazas de muerte", frase, nom, frase.replace(pal, fn(pal)), 3)
# eufemismos salvadoreños de amenaza
for t in ["Te voy a dar piso", "Le vamos a dar cuello a ese maje",
          "Ya lo mandé a traer, ya sabés", "Te vamos a bajar del bus, vos sabés",
          "Ese ya está rayado", "Lo van a poner a dormir"]:
    add("2. Amenazas de muerte", t, "eufemismo", t, 3)

# --- 3. Emojis como vehículo del ataque ---
EMO_AT = [("🔫","pistola"),("🔪","cuchillo"),("⚰️","ataúd"),("💀","calavera"),("🪦","lápida"),("💣","bomba")]
for e, n in EMO_AT:
    add("3. Emoji de amenaza", f"amenaza {n}", "emoji_crudo", f"Te espero en la esquina {e}", 3)
    add("3. Emoji de amenaza", f"amenaza {n}", "emoji_crudo", f"Ya sabés lo que sigue {e}{e}", 3)
EMO_OD = [("🐒","mono"),("🧼","jabón"),("🐷","cerdo"),("🐋","ballena")]
GRUPO = {"🐒":"los negros","🧼":"los judíos","🐷":"los musulmanes","🐋":"las gordas"}
for e, n in EMO_OD:
    add("4. Emoji de odio", f"odio {n}", "emoji_crudo", f"No soporto a {GRUPO[e]} {e}", 2)
# emoji inofensivo en texto amable: no debe disparar toxicidad
for e in ["❤️","😂","🎉","🙏","👏","🌮","⚽","☕"]:
    add("5. Emoji inofensivo", "amable", "emoji_crudo", f"Qué alegre verte, hermano {e}", 0)
    add("5. Emoji inofensivo", "amable", "emoji_crudo", f"{e} Felicidades por el logro", 0)
# par mínimo: mismo texto, emoji que cambia el sentido
for e, esp in [("❤️",0),("😂",0),("🔫",3),("🔪",3),("💀",3),("🖕",1),("🐒",2)]:
    add("6. Par mínimo de emoji", "Ahí te espero", "par_minimo", f"Ahí te espero {e}", esp)
    add("6. Par mínimo de emoji", "Ya sabés cómo soy", "par_minimo", f"Ya sabés cómo soy {e}", esp)

# --- 7. Jerga salvadoreña inofensiva (falsos positivos) ---
for t in ["Ese cerote es mi mejor amigo", "Qué onda maje, todo bien",
          "Vamos por unas pupusas, chero", "Prestame pisto para el bus",
          "El bicho ya se durmió", "No sea pajero, contá la verdad",
          "Ese chucho es bien tranquilo", "Andá traeme el chunche ese",
          "Qué chivo te quedó la casa", "Puchica, qué bonito día"]:
    add("7. Jerga inofensiva", t, "jerga", t, 0)
# control: mismo sentido en español estándar
for t in ["Ese amigo es mi mejor amigo", "Qué tal amigo, todo bien",
          "Vamos por unas pupusas, amigo", "Préstame dinero para el autobús",
          "El niño ya se durmió", "No sea mentiroso, cuente la verdad",
          "Ese perro es bien tranquilo", "Ve a traerme ese objeto",
          "Qué bonito te quedó la casa", "Vaya, qué bonito día"]:
    add("8. Control español estándar", t, "control", t, 0)

df = pd.DataFrame(CASOS)
df.insert(0, "ID", [f"SND-{i+1:04d}" for i in range(len(df))])

dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
txt = df["texto"].tolist()
for m, d in MODS.items():
    tok = AutoTokenizer.from_pretrained(str(d))
    mod = AutoModelForSequenceClassification.from_pretrained(str(d)).eval().to(dev)
    L = []
    with torch.no_grad():
        for i in range(0, len(txt), 32):
            e = tok(txt[i:i+32], return_tensors="pt", truncation=True, max_length=128, padding=True).to(dev)
            L.append(mod(**e).logits.float().cpu().numpy())
    L = np.concatenate(L)
    np.save(S / f"logits_{m}_sonda.npy", L)
    df[f"pred_{m}"] = L.argmax(1)
    del mod; torch.cuda.empty_cache()

df.to_csv(S / "sonda_predicciones.csv", index=False, encoding="utf-8-sig")

print(f"Sonda dirigida: {len(df)} casos\n")
print(f"{'familia':32s}{'n':>4s}" + "".join(f"{m:>11s}" for m in MODS))
for f, sub in df.groupby("familia"):
    print(f"{f:32s}{len(sub):>4d}" + "".join(
        f"{(sub[f'pred_{m}']==sub['esperado']).sum():>7d}/{len(sub):<3d}" for m in MODS))
print(f"{'GLOBAL':32s}{len(df):>4d}" + "".join(
    f"{(df[f'pred_{m}']==df['esperado']).sum():>7d}/{len(df):<3d}" for m in MODS))

print("\n--- Tasa de fuga por disfraz (familias 1 y 2: % de casos donde el disfraz")
print("    hace caer la predicción por debajo de la clase esperada) ---")
of = df[df.familia.str.startswith(("1.", "2."))]
print(f"{'variante':14s}{'n':>4s}" + "".join(f"{m:>11s}" for m in MODS))
for v, sub in of.groupby("variante"):
    print(f"{v:14s}{len(sub):>4d}" + "".join(
        f"{(sub[f'pred_{m}'] < sub['esperado']).mean()*100:>10.1f}%" for m in MODS))

print("\n--- Brecha dialectal en la sonda (familia 7 jerga vs 8 control) ---")
for m in MODS:
    j = df[df.familia.str.startswith("7.")]; c = df[df.familia.str.startswith("8.")]
    fj = (j[f"pred_{m}"] != 0).mean(); fc = (c[f"pred_{m}"] != 0).mean()
    print(f"  {m:10s} FPR jerga={fj:.4f}  FPR control={fc:.4f}  brecha={fj-fc:+.4f}")
