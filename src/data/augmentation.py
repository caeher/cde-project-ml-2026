# -*- coding: utf-8 -*-
"""
Generación de ejemplos sintéticos para el dataset v2 (b2).

MOTIVACIÓN
----------
La auditoría de los modelos entrenados sobre el dataset v1 detectó tres huecos de
cobertura que el modelo no puede resolver por arquitectura, solo por datos:

1. **Atajo del emoji.** El 90% de los textos con emoji del corpus pertenecen a
   `Lenguaje Ofensivo`. El modelo aprendió «hay emoji → ofensivo» en lugar del
   significado de cada emoji. Un `❤️` en un texto amable lo empuja a ofensivo.

2. **Emojis de ataque nunca vistos.** 🔫 🔪 ⚰️ 🐒 🧼 🐷 tienen CERO apariciones en
   el corpus, pese a que el catálogo del proyecto los documenta como vehículo de
   odio o amenaza.

3. **Amenazas ofuscadas.** «Te voy a m4t4r» se clasifica como ofensivo, no como
   amenaza: hay abundantes groserías deformadas en el corpus pero casi ninguna
   amenaza deformada.

4. **Sesgo dialectal.** El 43% de frases inofensivas con jerga salvadoreña se
   marcan como tóxicas, frente al 0% de sus equivalentes en español estándar.

REGLAS METODOLÓGICAS (no negociables)
-------------------------------------
- Los sintéticos entran **solo en `train`**. Nunca en `val` ni `test`, porque eso
  inflaría las métricas y las haría incomparables con la evaluación v1.
- Cada fila lleva `origen` y `plantilla_id` para trazabilidad completa.
- Se deduplica contra el corpus real y contra sí misma.
- Semilla fija.
"""
from __future__ import annotations

import itertools
import random

import pandas as pd

from src.data.lexicon_emojis import (CATALOGO, EMOJIS_NEUTROS, EMOJIS_OFENSIVOS,
                                     construir_catalogo)

SEED = 42

# =====================================================================
# A. NO TÓXICO CON EMOJI  — rompe el atajo «emoji ⇒ ofensivo»
# =====================================================================
NT_BASES = [
    "Feliz cumpleaños hermano, que la pases bien",
    "Muchas felicidades por tu graduación",
    "Qué alegre verte de nuevo después de tanto tiempo",
    "Gracias por la ayuda de ayer, se lo agradezco",
    "Buenos días a todos, que tengan bonito día",
    "Excelente el trabajo que hicieron en el proyecto",
    "Ya llegamos bien a la casa, gracias por preguntar",
    "Nos vemos mañana en la reunión entonces",
    "Qué rico estuvo el almuerzo de hoy",
    "Felicidades a la selección por el partido de ayer",
    "Me encantó la exposición del museo",
    "Vamos a la playa el fin de semana si querés",
    "Mi mamá cumple años hoy y le hicimos pastel",
    "El concierto estuvo increíble, valió la pena",
    "Se ve bien bonito el paisaje desde aquí",
    "Ya salieron las notas y me fue bien",
    "Gracias a todos por venir a la actividad",
    "Que Dios los bendiga a todos hoy",
    "Vamos a comer pupusas al mercado el domingo",
    "Qué bueno que ya te sentís mejor de salud",
    "Le quedó preciosa la decoración de la casa",
    "Muy buena la charla de esta mañana",
    "Ya casi es fin de semana, ánimo",
    "El equipo jugó muy bien todo el partido",
    "Felicitaciones por el nuevo trabajo",
]

# =====================================================================
# B. NO TÓXICO CON JERGA SALVADOREÑA — rompe el atajo dialectal
# =====================================================================
NT_JERGA = [
    "Qué onda maje, todo tranquilo por aquí",
    "Puchica, se me pasó la hora de la cita",
    "A huevo que sí, ahí nos vemos entonces",
    "Qué chivo te quedó el carro, felicidades",
    "Vaya pues, cabal a las tres nos vemos",
    "Ese cerote es mi mejor amigo desde la escuela",
    "Está bien vergón el lugar, se los recomiendo",
    "No sea bicho y ayudeme con esto porfa",
    "Mi cipote ya cumplió los quince años",
    "Qué verga maje, qué alegre verte de nuevo",
    "Andaba bien pedo pero llegó bien a la casa",
    "Ese bayunco no sabe ni manejar pero es buena gente",
    "Vamos a chambear temprano mañana",
    "Qué tuanis quedó la fiesta anoche",
    "Ahí le dejo el pisto que le debía maje",
    "Estuvo bien chiva la pelicula que vimos",
    "No sea codo y convide de esa comida",
    "Qué paja tan buena la que contó el profe",
    "Vaya maje, no se me raje ahora",
    "Ya casi está el guaro para el convivio",
    "Andá traeme unas minutas a la esquina",
    "Ese chero siempre llega tarde pero llega",
    "Qué chuco quedó el patio con la lluvia",
    "Puchica qué bonito amaneció hoy",
    "Vamos a jugar chibola en la cancha",
]

# =====================================================================
# C. DISCURSO DE ODIO CON EMOJI DEL CATÁLOGO
# =====================================================================
ODIO_PLANTILLAS = [
    ("Estos {grupo} no deberían estar aquí {emoji}", "Xenofobia"),
    ("Los {grupo} solo vienen a quitarnos el trabajo {emoji}", "Xenofobia"),
    ("Miren a los {grupo} como se comportan {emoji}", "Estigmatización nacional"),
    ("Todos los {grupo} son iguales {emoji}", "Estigmatización cultural"),
    ("Que devuelvan a todos los {grupo} a su país {emoji}", "Xenofobia"),
    ("Los {grupo} son una plaga en este país {emoji}", "Aporofobia"),
    ("{emoji} así son todos los {grupo}", "Estigmatización cultural"),
    ("No se puede esperar más de los {grupo} {emoji}", "Estigmatización nacional"),
    ("Los {grupo} nos están invadiendo {emoji}", "Xenofobia"),
    ("Qué asco dan los {grupo} {emoji}", "Estigmatización cultural"),
]

# El emoji debe ser SEMÁNTICAMENTE COHERENTE con el grupo atacado. Emparejar
# 🧼🇮🇱 (antisemita) con «venezolanos» produciría ejemplos incoherentes que
# enseñarían asociaciones falsas.
GRUPO_EMOJIS = {
    "nicaragüenses":  ["🐀", "🪳", "🐕", "🚽", "🌑"],
    "hondureños":     ["🐀", "🪳", "🐒🇭🇳", "🚽"],
    "venezolanos":    ["🐀", "🪳", "🐒🇻🇪", "🚽🧻"],
    "haitianos":      ["🐒", "🌑", "🐀", "🥷"],
    "migrantes":      ["🐀", "🪳", "🚽", "🧹", "🐕"],
    "indígenas":      ["👨‍🌾🐒", "🐒", "🦶"],
    "judíos":         ["🧼🇮🇱", "🧃", "🇮🇱🤢", "🙋‍♂️"],
    "musulmanes":     ["🤮🙈", "🚽"],
    "argentinos":     ["🐒🇦🇷", "🐀"],
    "mexicanos":      ["🐒🇲🇽", "🦶", "🌑"],
    "gordos":         ["🐷", "🐋", "🐋🚫", "🐖"],
    "viejos":         ["👴💀", "👴👻", "⚰️"],
    "pobres":         ["🐀", "🐕", "🪳", "🚽", "😈📕"],
}

ODIO_CUERPO = [
    ("Esa gente {emoji} no merece los mismos derechos que nosotros", "Estigmatización cultural"),
    ("Mientras más lejos estén esos {emoji} mejor para todos", "Xenofobia"),
    ("Ya está bueno de aguantar a esos {emoji} en el barrio", "Aporofobia"),
    ("Se creen mucho pero son puros {emoji}", "Estigmatización cultural"),
    ("No entiendo cómo los dejan entrar, son {emoji}", "Xenofobia"),
    ("Puros {emoji} son los que llegan a este país", "Xenofobia"),
    ("Con esos {emoji} no se puede convivir", "Estigmatización cultural"),
]

# =====================================================================
# F. NO TÓXICO MENCIONANDO NACIONALIDADES — corrige el sobreetiquetado
#    detectado en la auditoría: mencionar un país NO es discurso de odio.
# =====================================================================
NT_NACIONALIDAD = [
    "El mensaje de Messi para los hinchas argentinos después de la final",
    "Los nicaragüenses que viven aquí trabajan muy duro",
    "Mi vecina es hondureña y cocina delicioso",
    "La selección mexicana jugó bastante bien ayer",
    "Trabajo con dos venezolanos y son excelentes compañeros",
    "La comida peruana es de las mejores del mundo",
    "Se enfrentan Argentina y Brasil en la semifinal",
    "Los migrantes aportan bastante a la economía del país",
    "Mi profesor es colombiano y explica muy bien",
    "La comunidad judía celebró su festividad este fin de semana",
    "El equipo argentino salió campeón del torneo",
    "Hay muchos salvadoreños viviendo en Estados Unidos",
    "La cultura indígena de la zona es muy rica",
    "Ese restaurante hondureño tiene buena sazón",
    "Los ecuatorianos ganaron el partido de anoche",
    "Vinieron unos compañeros mexicanos al congreso",
    "El presidente se reunió con la delegación española",
    "Mi cuñado es guatemalteco y es buena gente",
    "En el barrio viven varias familias nicaragüenses",
    "El documental habla sobre la migración centroamericana",
    "Messi con Infantino después de terminar el partido",
    "Terminó el mundial y quedaron todos contentos",
    "Los jugadores de ese equipo dieron una gran final",
    "Hoy juega la selección y vamos a verla en familia",
]

# =====================================================================
# D. AMENAZAS CON EMOJI Y CON OFUSCACIÓN
# =====================================================================
AMENAZA_BASES_EMOJI = [
    ("Te espero afuera", "Amenaza Directa"),
    ("Ya sabés dónde vivís", "Amenaza Implícita"),
    ("Un día de estos te toca", "Amenaza Implícita"),
    ("Vas a ver lo que te va a pasar", "Amenaza Directa"),
    ("Hay que darles piso a todos esos", "Incitación a la Violencia"),
    ("Ojalá se muera pronto ese maldito", "Deseo de Daño"),
    ("Que lo agarren y lo desaparezcan", "Incitación a la Violencia"),
    ("Bien hecho que lo mataron, uno menos", "Celebración de Violencia"),
    ("Te voy a buscar y ya sabés qué pasa", "Amenaza Directa"),
    ("A esos hay que limpiarlos del país", "Incitación a la Violencia"),
    ("Se merece que le pase algo feo", "Deseo de Daño"),
    ("Andá con cuidado en la calle vos", "Amenaza Implícita"),
    ("Ya te tenemos ubicado, esperá nomás", "Amenaza Directa"),
    ("Que se los lleven a todos de una vez", "Incitación a la Violencia"),
    ("Ojalá le pase lo mismo a la familia", "Deseo de Daño"),
    ("Bien merecido lo que le hicieron", "Celebración de Violencia"),
    ("Si te veo en la calle no respondo", "Amenaza Directa"),
    ("A ese hay que darle su merecido ya", "Incitación a la Violencia"),
    ("Que se pudran todos esos malditos", "Deseo de Daño"),
    ("No vas a llegar a fin de mes vos", "Amenaza Implícita"),
    ("Hay que sacarlos a la fuerza de aquí", "Incitación a la Violencia"),
    ("Que alguien le dé lo que se merece", "Incitación a la Violencia"),
    ("Ojalá se lo lleven pronto", "Deseo de Daño"),
    ("Uno menos que estorba en este país", "Celebración de Violencia"),
    ("Ya está marcado ese maje", "Amenaza Implícita"),
    ("Te vas a arrepentir de lo que dijiste", "Amenaza Directa"),
]
EMOJIS_AMENAZA = ["🔫", "🔪", "⚰️", "💀", "🪦", "💣", "🧹", "🔫🔪", "⚰️💀"]

# Ofuscación aplicada a verbos de amenaza
AMENAZA_BASE = [
    ("Te voy a {v}", "Amenaza Directa"),
    ("Lo van a {v} a ese", "Amenaza Directa"),
    ("Hay que {v} a todos esos", "Incitación a la Violencia"),
    ("Ojalá lo {v}", "Deseo de Daño"),
    ("Alguien debería {v} a ese tipo", "Incitación a la Violencia"),
    ("Te van a {v} si seguís así", "Amenaza Directa"),
]
VERBOS_OFUSCADOS = {
    "matar": ["matar", "m4t4r", "m*tar", "mat4r", "ma7ar", "matarte", "m4tar"],
    "quemar": ["quemar", "qu3m4r", "qu*mar", "quem4r"],
    "golpear": ["golpear", "g0lp34r", "golp*ar", "g0lpear"],
    "reventar": ["reventar", "r3v3nt4r", "rev*ntar"],
}
EUFEMISMOS_SV = [
    ("Te voy a dar piso", "Amenaza Directa"),
    ("Le van a dar cuello a ese", "Amenaza Directa"),
    ("Ya sabés lo que te puede pasar", "Amenaza Implícita"),
    ("Lo van a mandar a dormir", "Amenaza Directa"),
    ("A ese ya le tienen el cajón listo", "Amenaza Implícita"),
    ("Se lo van a llevar los cheros", "Amenaza Implícita"),
    ("Hay que darles su merecido a esos", "Incitación a la Violencia"),
    ("Que lo pongan a descansar de una vez", "Amenaza Implícita"),
    ("Le van a apagar la luz a ese maje", "Amenaza Implícita"),
    ("Ya está en la lista ese", "Amenaza Implícita"),
]

# =====================================================================
# E. LENGUAJE OFENSIVO CON EMOJI
# =====================================================================
OFENSIVO_BASES = [
    ("Qué pendejo es este tipo", "Insulto Directo"),
    ("No sabe ni lo que dice el maje", "Insulto Directo"),
    ("Puras babosadas las que escribe", "Tono Agresivo"),
    ("Este gobierno es un desastre completo", "Crítica Institucional"),
    ("Qué mierda de servicio dan aquí", "Palabras Obscenas"),
    ("Ya cállese que no sabe nada", "Tono Agresivo"),
    ("Sos bien tonto de verdad", "Insulto Directo"),
    ("Qué payasada la de ese equipo", "Crítica Fuerte"),
    ("Este maje habla pura paja siempre", "Insulto Directo"),
    ("Qué idiota el que escribió eso", "Insulto Directo"),
    ("Me vale verga lo que opines", "Palabras Obscenas"),
    ("Callate ya que hartás con lo mismo", "Tono Agresivo"),
    ("Puro show barato el de esa gente", "Crítica Fuerte"),
    ("Qué asco de administración tienen", "Crítica Institucional"),
    ("No jodás con esas babosadas otra vez", "Tono Agresivo"),
    ("Sos un imbécil si creés eso", "Insulto Directo"),
    ("Qué basura de servicio al cliente", "Palabras Obscenas"),
    ("Este cerote no entiende razones", "Insulto Directo"),
    ("Puras mentiras las que dicen ahí", "Crítica Fuerte"),
    ("Qué vergüenza de equipo el de ayer", "Crítica Fuerte"),
    ("Ese tipo es un payaso de verdad", "Insulto Directo"),
    ("Ya me tienen hasta la madre con eso", "Palabras Obscenas"),
    ("Qué pereza leer tanta estupidez", "Tono Agresivo"),
    ("No sirven para nada los de esa oficina", "Crítica Institucional"),
    ("Qué mierda de respuesta me dieron", "Palabras Obscenas"),
    ("Andá a molestar a otro lado maje", "Tono Agresivo"),
    ("Puro bla bla y nada de acción", "Crítica Fuerte"),
    ("Este bicho no sabe ni escribir", "Insulto Directo"),
]


def _plantilla_id(cat, i):
    return f"{cat}-{i:04d}"


# =====================================================================
# COLOCACIÓN DEL EMOJI
# =====================================================================
# En el corpus real los emojis aparecen al inicio el 12% de las veces, en medio
# el 22% y al final el 66%. Si todos los sintéticos los llevan al final, el
# modelo puede aprender «emoji en posición final» como pista posicional en lugar
# del significado del emoji: sería sustituir un atajo espurio por otro.
POS_REAL = [("inicio", 0.12), ("medio", 0.22), ("final", 0.66)]


def insertar_emoji(texto: str, emo: str, rnd: random.Random) -> str:
    """Coloca el emoji reproduciendo la distribución posicional del corpus real."""
    r = rnd.random()
    acum = 0.0
    pos = "final"
    for nombre, prob in POS_REAL:
        acum += prob
        if r <= acum:
            pos = nombre
            break

    if pos == "inicio":
        return f"{emo} {texto}"
    if pos == "final":
        return f"{texto} {emo}"

    palabras = texto.split()
    if len(palabras) < 4:
        return f"{texto} {emo}"
    corte = rnd.randint(2, len(palabras) - 2)
    return " ".join(palabras[:corte] + [emo] + palabras[corte:])


MIN_POR_EMOJI = 8   # apariciones mínimas para que el modelo pueda aprender uno


def generar(seed: int = SEED) -> pd.DataFrame:
    """
    Genera el conjunto sintético.

    Criterio de diseño: **más contextos por emoji, no más emojis distintos.**
    Un emoji visto dos veces no se aprende. Se garantiza un mínimo de
    MIN_POR_EMOJI apariciones para cada emoji del catálogo, repartidas entre
    plantillas y posiciones distintas.
    """
    rnd = random.Random(seed)
    filas = []
    cat = construir_catalogo()
    emo_odio = cat[cat.clase_asociada == "Discurso de Odio"].emoji.tolist()

    def add(texto, clase, sub, origen, pid):
        filas.append(dict(texto=texto, clase=clase, subclase=sub,
                          origen=origen, plantilla_id=pid))

    # ---------------------------------------------- A: No Tóxico + emoji
    i = 0
    for base in NT_BASES:
        for emo in rnd.sample(EMOJIS_NEUTROS, 5):
            i += 1
            add(insertar_emoji(base, emo, rnd), "No Tóxico", "N/A",
                "sintetico_emoji_notoxico", _plantilla_id("NT-EMO", i))

    # ---------------------------------------------- B: No Tóxico + jerga
    i = 0
    for base in NT_JERGA:
        i += 1
        add(base, "No Tóxico", "N/A", "sintetico_jerga_notoxico", _plantilla_id("NT-JER", i))
        for emo in rnd.sample(EMOJIS_NEUTROS, 3):
            i += 1
            add(insertar_emoji(base, emo, rnd), "No Tóxico", "N/A",
                "sintetico_jerga_notoxico", _plantilla_id("NT-JER", i))

    # ------------------------- F: No Tóxico mencionando nacionalidades
    i = 0
    for base in NT_NACIONALIDAD:
        i += 1
        add(base, "No Tóxico", "N/A", "sintetico_nacionalidad_notoxico",
            _plantilla_id("NT-NAC", i))
        for emo in rnd.sample(EMOJIS_NEUTROS, 3):
            i += 1
            add(insertar_emoji(base, emo, rnd), "No Tóxico", "N/A",
                "sintetico_nacionalidad_notoxico", _plantilla_id("NT-NAC", i))

    # ---------------------------------------------- C: Discurso de Odio
    i = 0
    for (plant, sub), (grupo, emojis) in itertools.product(ODIO_PLANTILLAS, GRUPO_EMOJIS.items()):
        if rnd.random() > 0.75:
            continue
        i += 1
        base = plant.replace(" {emoji}", "").replace("{emoji} ", "").format(grupo=grupo)
        add(insertar_emoji(base, rnd.choice(emojis), rnd), "Discurso de Odio", sub,
            "sintetico_emoji_odio", _plantilla_id("OD-EMO", i))
    # Plantillas sin grupo explícito: solo emojis de deshumanización genérica.
    emo_genericos = ["🐀", "🪳", "🐕", "🚽", "🚽🧻", "🐷", "🐒", "🌑", "🥷", "🐖", "🐁"]
    for plant, sub in ODIO_CUERPO:
        for emo in emo_genericos:
            i += 1
            add(plant.format(emoji=emo), "Discurso de Odio", sub,
                "sintetico_emoji_odio", _plantilla_id("OD-EMO", i))

    # ---------------------------------------------- D1: Amenazas + emoji
    i = 0
    for base, sub in AMENAZA_BASES_EMOJI:
        for emo in rnd.sample(EMOJIS_AMENAZA, 5):
            i += 1
            add(insertar_emoji(base, emo, rnd), "Amenazas/Violencia", sub,
                "sintetico_emoji_amenaza", _plantilla_id("AM-EMO", i))

    # ---------------------------------------------- D2: Amenazas ofuscadas
    i = 0
    for plant, sub in AMENAZA_BASE:
        for _, variantes in VERBOS_OFUSCADOS.items():
            for v in variantes:
                i += 1
                add(plant.format(v=v), "Amenazas/Violencia", sub,
                    "sintetico_amenaza_ofuscada", _plantilla_id("AM-OFU", i))
    for txt, sub in EUFEMISMOS_SV:
        i += 1
        add(txt, "Amenazas/Violencia", sub, "sintetico_amenaza_ofuscada",
            _plantilla_id("AM-OFU", i))
        for emo in rnd.sample(EMOJIS_AMENAZA, 2):
            i += 1
            add(insertar_emoji(txt, emo, rnd), "Amenazas/Violencia", sub,
                "sintetico_amenaza_ofuscada", _plantilla_id("AM-OFU", i))

    # ---------------------------------------------- E: Lenguaje Ofensivo
    i = 0
    for base, sub in OFENSIVO_BASES:
        for emo in rnd.sample(EMOJIS_OFENSIVOS, 4):
            i += 1
            add(insertar_emoji(base, emo, rnd), "Lenguaje Ofensivo", sub,
                "sintetico_emoji_ofensivo", _plantilla_id("OF-EMO", i))

    df = pd.DataFrame(filas).drop_duplicates(subset="texto").reset_index(drop=True)

    # ------------------------------------------------------------------
    # Relleno: ningún emoji del catálogo debe quedar por debajo del mínimo.
    # ------------------------------------------------------------------
    import emoji as _emo
    from collections import Counter

    def contar(d):
        c = Counter()
        for s in d.texto:
            for e in _emo.emoji_list(str(s)):
                c[e["emoji"]] += 1
        return c

    # Bases sin grupo explícito: compatibles con cualquier emoji de
    # deshumanización. Las plantillas con {grupo} solo se usan si el emoji
    # corresponde a ese grupo, para no repetir la incoherencia semántica.
    BASES_ODIO_GENERICAS = [p.replace(" {emoji}", "").replace("{emoji} ", "")
                            for p, _ in ODIO_CUERPO]
    EMOJI_A_GRUPOS = {}
    for grupo, emojis in GRUPO_EMOJIS.items():
        for e in emojis:
            EMOJI_A_GRUPOS.setdefault(e, []).append(grupo)

    def bases_para(emo, clase):
        if clase == "Discurso de Odio":
            grupos = EMOJI_A_GRUPOS.get(emo)
            if grupos:
                # Solo plantillas del grupo al que ese emoji pertenece
                return [p.replace(" {emoji}", "").replace("{emoji} ", "").format(grupo=g)
                        for p, _ in ODIO_PLANTILLAS for g in grupos] + BASES_ODIO_GENERICAS
            return BASES_ODIO_GENERICAS
        if clase == "Amenazas/Violencia":
            return [b for b, _ in AMENAZA_BASES_EMOJI]
        if clase == "Lenguaje Ofensivo":
            return [b for b, _ in OFENSIVO_BASES]
        return NT_BASES + NT_JERGA + NT_NACIONALIDAD

    SUB = {"Discurso de Odio": "Estigmatización cultural",
           "Amenazas/Violencia": "Amenaza Directa",
           "Lenguaje Ofensivo": "Tono Agresivo", "No Tóxico": "N/A"}

    objetivo = {}
    for e in cat.emoji:
        objetivo[e] = cat[cat.emoji == e].clase_asociada.iloc[0]
    for e in EMOJIS_NEUTROS:
        objetivo[e] = "No Tóxico"
    for e in EMOJIS_OFENSIVOS:
        objetivo[e] = "Lenguaje Ofensivo"

    extra, j = [], 0
    cuenta = contar(df)
    vistos = set(df.texto)
    for e, clase in objetivo.items():
        faltan = MIN_POR_EMOJI - cuenta.get(e, 0)
        bases = bases_para(e, clase)
        intentos = 0
        while faltan > 0 and intentos < 60:
            intentos += 1
            t = insertar_emoji(rnd.choice(bases), e, rnd)
            if t in vistos:
                continue
            vistos.add(t)
            j += 1
            extra.append(dict(texto=t, clase=clase, subclase=SUB[clase],
                              origen="sintetico_relleno_emoji",
                              plantilla_id=_plantilla_id("RELL", j)))
            faltan -= 1

    if extra:
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)
        df = df.drop_duplicates(subset="texto").reset_index(drop=True)

    df["Plataforma"] = [rnd.choice(["X", "Facebook"]) for _ in range(len(df))]
    return df


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    d = generar()
    print(f"generados: {len(d)}")
    print(d.groupby(["clase", "origen"]).size().to_string())
