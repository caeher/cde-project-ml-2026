# -*- coding: utf-8 -*-
"""Prueba de humo con 500 mensajes inventados (10 hilos x 50 respuestas).

Las etiquetas son MIS etiquetas por intención al escribir cada plantilla, no un gold standard:
sirven para ver comportamiento en hilos nuevos, no para reportar F1 oficial.
Se descarta cualquier mensaje que coincida con train/val/test/batería.
Salidas: reports/improvement/prueba_hilos_500.csv y reports/improvement/prueba_hilos_500.md
"""
import random, re, sys, unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from app.api.main import predecir, CLASES  # noqa: E402

rnd = random.Random(2026)

TEMAS = [
    dict(n="Partido de la selección", post="¿Qué les pareció el partido de anoche de la Selección en el estadio Cuscatlán?",
         ev="el partido", persona="el árbitro", lugar="el estadio", grupo="los hondureños"),
    dict(n="Tráfico y buses", post="Otra vez 2 horas de tráfico por el bulevar. ¿Qué opinan del sistema de buses?",
         ev="el tráfico", persona="el motorista del bus", lugar="la terminal", grupo="las mujeres"),
    dict(n="Precio de la canasta", post="Subieron otra vez los frijoles y las pupusas. ¿Cómo la están librando?",
         ev="el aumento de precios", persona="el dueño de la tienda", lugar="el mercado", grupo="los venezolanos"),
    dict(n="Elecciones y gobierno", post="Se viene el debate sobre la reforma al presupuesto. ¿Qué piensan?",
         ev="el debate", persona="el diputado", lugar="la Asamblea", grupo="los gays"),
    dict(n="Remesas y migración", post="Las remesas siguen creciendo pero cada vez más gente se va del país. ¿Por qué será?",
         ev="la migración", persona="el coyote", lugar="la frontera", grupo="los migrantes"),
    dict(n="Lluvias e inundaciones", post="Con las lluvias de hoy se inundó media colonia. ¿Ya vieron los reportes?",
         ev="la tormenta", persona="el alcalde", lugar="la colonia", grupo="los indígenas"),
    dict(n="Seguridad y barrios", post="Dicen que bajó la delincuencia pero en mi zona sigue igual. ¿Ustedes qué ven?",
         ev="la seguridad", persona="el vecino", lugar="el barrio", grupo="los nicas"),
    dict(n="Mujeres en el trabajo", post="Salió el estudio sobre brecha salarial entre hombres y mujeres. ¿Qué opinan?",
         ev="el estudio", persona="el jefe", lugar="la oficina", grupo="las mujeres"),
    dict(n="Bitcoin y economía", post="Bitcoin cerró otra vez en rojo y el gobierno sigue comprando. ¿Vale la pena?",
         ev="el bitcoin", persona="el ministro", lugar="el banco", grupo="los extranjeros"),
    dict(n="Concierto y fiestas", post="Anunciaron el concierto del sábado en el Parque Cuscatlán. ¿Van a ir?",
         ev="el concierto", persona="el organizador", lugar="el parque", grupo="los gays"),
]

INS = ["pendejo", "inútil", "imbécil", "cerote", "baboso", "estúpido", "payaso", "sinvergüenza", "mamón", "patán"]
INSP = ["pendejos", "inútiles", "imbéciles", "cerotes", "babosos", "estúpidos", "payasos", "sinvergüenzas"]
DESC = ["una plaga", "una vergüenza", "basura", "una enfermedad", "lo peor", "un cáncer"]
CIERRE_NT = ["", "", "", " 🙂", " jaja", " saludos", " #ElSalvador", " 👍", "."]
CIERRE_OF = ["", "!", "!!!", " 🤡", " 💩", " jaja", "."]
CIERRE_OD = ["", ".", "!!", " 🤮", " asco", ""]
CIERRE_AM = ["", "!", "!!!", " 🔪", " 💀", " ya verán", "."]

NT = [
    "Alguien sabe a qué hora empieza {ev}?", "Qué chivo {ev}, lo disfruté un montón{c}", "Gracias por compartir, no sabía lo de {ev}",
    "Yo voy a matar el tiempo viendo cómo sigue {ev}{c}", "Me parece que {persona} podría explicar mejor lo de {ev}",
    "Opino distinto: {ev} fue más complicado de lo que dicen", "Les dejo la info completa sobre {ev} para que la lean con calma",
    "Voy a comer algo y ahorita les cuento qué tal {ev}", "Está difícil lo de {ev}, ojalá mejore pronto", "Hoy en {lugar} no se hablaba de otra cosa que de {ev}",
    "Estoy de acuerdo, hay que organizarse mejor con {ev}", "Qué puchica lo de {ev}, ni modo, a seguir adelante", "¿Alguien tiene fotos de {lugar} de hoy?",
    "Mi mamá dice que {ev} nunca había estado así{c}", "Te voy a mandar el link para que veás lo de {ev} mañana", "Pregunta sincera: ¿cómo afecta {ev} a las familias?",
    "Qué maje tan buena onda {persona}, la verdad nos ayudó con {ev}", "No tengo claro qué pasó con {ev}, ¿me explican?", "Buenos días a todos, a ver cómo amanece {ev} hoy{c}",
    "Ya mero llego a {lugar}, ahí nos vemos", "Me da pena lo de {ev}, mucha fuerza a todos los afectados", "Hay que ver las dos caras de {ev} antes de opinar",
    "El que no chambea no come, pero aun así {ev} nos afecta a todos", "Se me hace que {persona} está haciendo lo que puede con {ev}", "Voy a matar la curiosidad y buscar más datos sobre {ev}",
    "Qué bonito se ve {lugar} después de {ev}", "Compré boletos para ir a {lugar}, ¿alguien más va?",
]
OF = [
    "{PERSONA} es un {ins}, no sirve para nada", "Qué {ins} {persona}, siempre arruina {ev}{c}", "Cállate {ins}, nadie te preguntó", "Pura mierda {ev}, organizado por unos {insp}{c}",
    "Qué {ins} tan grande tu opinión sobre {ev}", "Eres un {ins} si crees eso de {ev}", "Puta madre con {ev}, qué desorden de {insp}", "Vos sos un {ins} y {persona} otro más{c}",
    "Qué asco de {ev}, todo lo hacen mal esos {insp}", "{PERSONA} es un {ins} corrupto, ya basta de tanta basura política", "Los de ese partido son unos {insp}, no engañan a nadie{c}",
    "Estás bien {ins}, andá a hablar de {ev} a otro lado", "Maldito {ins}, siempre con lo mismo de {ev}", "Qué hijo de puta {persona}, nos arruinó {ev}{c}",
    "Qué mierda de organización con {ev}, unos {insp}", "No seas {ins}, {ev} no es tan complicado", "Todo el que defiende a {persona} es un {ins}, así de simple",
    "Vaya {ins} el que escribió eso sobre {ev}",
]
OD = [
    "Los {grupo} son {desc}, que se vayan de {lugar}", "Típico de {grupo}, solo saben dar problemas con {ev}", "{GRUPO} no deberían tener derechos en este país{c}",
    "Qué asco {grupo}, son {desc} en {lugar}", "Por culpa de {grupo} pasa lo de {ev}, son {desc}", "Ya estamos hartos de {grupo}, deberían estar fuera de {lugar}{c}",
    "{GRUPO} nunca van a ser iguales a nosotros, son inferiores", "Dejen entrar a {grupo} y mire cómo queda {lugar}, puro desastre{c}", "No me vengan con {grupo}, esa gente es {desc}",
    "Están arruinando todo, esos {grupo} no son de aquí ni valen nada", "Lo de {ev} es culpa de {grupo}, siempre lo mismo, gente de mierda",
    "Solo {grupo} harían algo tan {desc} como lo de {ev}", "{GRUPO} son todos iguales, una plaga que hay que sacar de {lugar}",
]
AM = [
    "Voy a ir a buscar a {persona} y lo voy a dejar sin dientes{c}", "Ojalá le caiga un rayo a {persona}, que se muera{c}", "Te voy a matar si te vuelvo a ver en {lugar}{c}",
    "Hay que quemar {lugar} con todos adentro{c}", "M@ldito, te voy a partir la cara afuera de {lugar}", "Les voy a meter un balazo a esos {insp}{c}",
    "Si sigues hablando de {ev} te va a pasar algo, sé dónde vivís{c}", "A {persona} hay que colgarlo en {lugar} para que aprendan", "Ya van a ver, cuando los encuentre en {lugar} los mato a todos{c}",
    "Ojalá se mueran todos los que organizaron {ev}{c}", "Te voy a apuñalar, {ins}, ya verás{c}", "Pronto le llega su hora a {persona}, lo vamos a buscar a la casa{c}",
    "Vamos a ir con machetes a {lugar} a arreglar esto de {ev}", "Voy a ir a darte unos balazos por lo que dijiste de {ev}",
    "Qué bueno que murió, ojalá les pase lo mismo a todos los que hablan de {ev}", "Te voy a descuartizar si no cierras esa boca sobre {ev}",
]
BASE = {0: (NT, CIERRE_NT), 1: (OF, CIERRE_OF), 2: (OD, CIERRE_OD), 3: (AM, CIERRE_AM)}
MIX = [0] * 12 + [1] * 14 + [2] * 11 + [3] * 13  # 50 respuestas por hilo (24 % NT, 28 % OF, 22 % OD, 26 % AM)


def clave(s):
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"https?://\S+", " ", s); s = re.sub(r"@\w+", " ", s); s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def decorar(t, clase):
    r = rnd.random()
    if r < 0.07: t = t.upper()
    elif r < 0.12: t = t.lower()
    elif r < 0.15: t = t.replace("a", "4", 1) if clase in (1, 2) else t
    return t


def generar():
    usadas = set()
    ex = []
    for tema in TEMAS:
        orden = MIX[:]; rnd.shuffle(orden)
        for i, clase in enumerate(orden, 1):
            plantillas, cierres = BASE[clase]
            for _ in range(50):
                p = rnd.choice(plantillas)
                t = p.format(ev=tema["ev"], persona=tema["persona"], PERSONA=tema["persona"].capitalize(), lugar=tema["lugar"],
                             grupo=tema["grupo"], GRUPO=tema["grupo"].capitalize(), ins=rnd.choice(INS), insp=rnd.choice(INSP),
                             desc=rnd.choice(DESC), c=rnd.choice(cierres))
                t = decorar(t.strip(), clase)
                if clave(t) not in usadas: break
            else:
                continue
            usadas.add(clave(t))
            ex.append(dict(tema=tema["n"], pos=i, texto=t, esperado=clase))
    return pd.DataFrame(ex)


def main():
    df = generar()
    d = RAIZ / "data/history/v1.3.1"
    prohibidas = set()
    for f, c in [("train", "texto_original"), ("val", "texto_original"), ("test", "texto_original"), ("test_adversarial", "texto")]:
        prohibidas |= set(pd.read_csv(d / f"{f}.csv")[c].map(clave))
    solape = df.texto.map(clave).isin(prohibidas)
    print(f"generados {len(df)} · coinciden con train/val/test/batería: {int(solape.sum())}")
    df = df[~solape].reset_index(drop=True)
    res = [predecir(t) for t in df.texto]
    df["predicho"] = [r["label"] for r in res]
    df["confianza"] = [round(r["confianza"], 3) for r in res]
    df["ok"] = df.predicho == df.esperado
    df.to_csv(RAIZ / "reports/improvement/prueba_hilos_500.csv", index=False, encoding="utf-8-sig")
    print(f"mensajes evaluados: {len(df)}")
    return df


if __name__ == "__main__":
    main()
