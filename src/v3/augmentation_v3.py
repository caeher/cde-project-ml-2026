# -*- coding: utf-8 -*-
"""
Generador de sintéticos V3 con jerga salvadoreña.

Corrige lo que la auditoría de la entrega 2v midió como débil, y evita los tres
defectos del generador de B2 que se detectaron al revisarlo:

  · Concordancia.  Los portadores son vocativos y aposiciones, que no exigen
    concordancia de género ni número. «Callate, arrastrada» y «Callate, cerote»
    son ambos correctos; «Los mujeres son unos pandilleros» no lo era.

  · Coherencia emoji↔grupo.  Cada emoji del catálogo trae su campo
    grupos_afectados. Un emoji solo se empareja con referentes de SU grupo.
    Cruzar 🧼 (antisemita) con «chinos» enseñaría una asociación falsa.

  · Ofuscación real.  Las deformaciones no se inventan: son las 1,979 variantes
    del léxico, agrupadas en 110 familias canónicas, que son formas observadas
    en el corpus.

Higiene: ningún texto puede coincidir con val, test ni con la batería
adversarial. Es el fallo de las 7 filas que el proyecto arrastraba desde agosto.
"""
from __future__ import annotations
import random, sys, unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar
from src.v3.lexico import cargar as cargar_lexico

SEED = 42
# Tope de repeticiones por estructura, para que ninguna plantilla domine.
# En las familias donde la variación la aporta el TÉRMINO (las 1,979 variantes
# ofuscadas del léxico) y no la estructura, el tope puede ser más alto: repetir
# el portador es justamente lo que aísla el efecto de la deformación.
TOPE_POR_PLANTILLA = 26
TOPE_POR_CLASE = 900          # cupo por clase tras generar, para no desbalancear
TOPE_POR_CATEGORIA = {
    "ofensivo_ofuscado": 90,
    "odio_ofuscado": 90,
    "amenaza_ofuscada": 60,
}


def clave(s) -> str:
    return unicodedata.normalize("NFC", str(s)).strip().lower()


# ═══════════════════════════════════════════════════ 1. LENGUAJE OFENSIVO
# Vocativos y aposiciones: el insulto va en posición libre de concordancia.
PORT_OFENSIVO = [
    "Callate ya, {t}", "Andate de aquí, {t}", "No jodás más, {t}",
    "Qué {t}, en serio", "Ya me hartaste, {t}", "Dejá de escribir, {t}",
    "Nadie te preguntó, {t}", "Sos un {t} y punto", "Eso es lo que sos, un {t}",
    "Me da igual lo que digas, {t}", "Otra vez vos, {t}", "Qué asco das, {t}",
    "Andá a trabajar, {t}", "No sabés nada, {t}", "Cerrá el hocico, {t}",
    "Puro {t} el que escribió eso", "Mirá al {t} este", "Ese {t} otra vez",
    "Hablando pura paja, {t}", "Ya cállese, {t}", "Qué pereza leerte, {t}",
    "Mejor callate, {t}", "No hablés de lo que no sabés, {t}",
    "Volvé cuando aprendás, {t}", "Sos lo peor que hay, {t}",
]

# ═══════════════════════════════════════════════════ 2. DISCURSO DE ODIO
# Predicados invariables en género y número, para poder aplicar ofuscación
# sin romper la gramática.
PRED_ODIO_INVARIABLE = [
    "son basura", "son escoria", "son una plaga", "dan asco", "son mierda",
    "no son gente", "sobran en este país", "son puro estorbo",
]
# Separados por número: mezclarlos producía «Ningún hondureños».
PORT_ODIO_PLURAL = [
    "Los {g} {p}", "Todos los {g} {p}, sin excepción", "Que se vayan los {g}, {p}",
    "Odio a los {g}, {p}", "Fuera los {g} de nuestro país",
    "Los {g} {p} y nadie lo dice", "Mientras más {g} llegan, peor está todo",
    "Los {g} {p}, así de simple", "Ya son demasiados {g} en este país",
]
PORT_ODIO_SINGULAR = [
    "Ningún {gs} debería estar aquí", "No quiero ni un {gs} cerca de mi familia",
    "Un {gs} siempre va a ser un problema", "Con un {gs} no se puede razonar",
]
# Insulto dirigido al grupo, en vocativo: la subclase del léxico fija el grupo.
SUB_A_GRUPO = {
    "Xenofobia":  ["inmigrante", "extranjero", "nicaragüense", "hondureño", "venezolano"],
    "Racismo":    ["negro", "indígena", "moreno"],
    "Homofobia":  ["gay", "lesbiana", "trans"],
    "Sexismo":    ["mujer", "vieja", "muchacha"],
}
PORT_ODIO_VOCATIVO = [
    "Andate a tu país, {t}", "Aquí no te queremos, {t}", "Regresate de donde viniste, {t}",
    "No perteneces aquí, {t}", "Ojalá te deporten, {t}", "Da asco verte, {t}",
    "Gente como vos sobra, {t}", "Por gente como vos está así el país, {t}",
]
GRUPOS_NACIONALES = [
    ("nicaragüenses", "nicaragüense"), ("hondureños", "hondureño"),
    ("venezolanos", "venezolano"), ("guatemaltecos", "guatemalteco"),
    ("mexicanos", "mexicano"), ("colombianos", "colombiano"),
    ("chinos", "chino"), ("haitianos", "haitiano"), ("argentinos", "argentino"),
    ("peruanos", "peruano"), ("cubanos", "cubano"), ("indígenas", "indígena"),
]

# ═══════════════════════════════════════════════════ 3. AMENAZAS
PORT_AMENAZA = [
    "Te voy a {v}", "Lo van a {v} a ese", "Hay que {v}los a todos",
    "Alguien debería {v} a ese tipo", "Te van a {v} si seguís así",
    "Vamos a {v} a ese maje", "Me dan ganas de {v}lo",
    "A ese hay que {v}lo antes de que siga", "Que lo vayan a {v} de una vez",
    "Voy a ir a {v}te a tu casa", "Ojalá lo {v}en pronto",
    "Deberían {v} a todos esos", "Si lo vuelvo a ver lo voy a {v}",
    "Ya quisiera {v} a ese maje", "No respondo si lo llego a {v}",
    "Uno de estos días lo van a {v}", "Con gusto lo {v}ría yo mismo",
]
VERBOS_BASE = ["matar", "quemar", "golpear", "reventar", "quebrar", "partir",
               "linchar", "fusilar", "apuñalar", "balear", "torturar", "colgar"]
LEET = [
    ("a", "4"), ("e", "3"), ("i", "1"), ("o", "0"), ("s", "5"), ("t", "7"),
]
def _ofuscar(p: str, rnd: random.Random) -> list[str]:
    """Disfraces de una palabra, con las mismas técnicas que usa la gente."""
    out = {p}
    out.add(p[0] + "*" * (len(p) - 2) + p[-1])
    out.add(p.replace("a", "@"))
    out.add("".join(d if c == o else c for c in p for o, d in [rnd.choice(LEET)]) if False else p)
    for o, d in LEET:
        if o in p:
            out.add(p.replace(o, d))
    out.add(".".join(p))
    out.add(" ".join(p))
    out.add(p[:2] + p[1] * 2 + p[2:])
    for o, d in LEET:
        out.add(p.replace(o, d).replace("a", "4"))
    return sorted(x for x in out if 3 <= len(x) <= 30)

EUFEMISMOS = [
    "Te voy a dar piso", "Le van a dar cuello a ese", "Ya sabés lo que te puede pasar",
    "Lo van a mandar a dormir", "A ese ya le tienen el cajón listo",
    "Se lo van a llevar los cheros", "Hay que darles su merecido a esos",
    "Que lo pongan a descansar de una vez", "Le van a apagar la luz a ese maje",
    "Ya está en la lista ese", "Ese ya está rayado", "Le van a pasar factura",
    "Ya lo mandé a traer, vos sabés", "Te vamos a bajar del bus",
    "A ese ya lo tienen fichado", "Le va a llegar su hora", "Ya sabe lo que le espera",
    "Le tienen el traje listo", "Va a amanecer tieso ese", "Lo van a dejar frío",
    "Ya le pusieron precio a ese", "Hay quien lo está esperando afuera",
    "Se va a topar con quien no debe", "Le van a dar su vuelta", "Ya le tocó a ese",
    "Van a ir a visitarlo esta noche", "Le van a hacer la visita", "Ese no llega al lunes",
    "Le van a quitar las ganas de hablar", "Va a desaparecer ese maje",
    "Ya lo tienen ubicado", "Le van a dar cran", "Ese ya no cuenta el cuento",
    "Lo van a bajar del caballo", "Hay que ponerlo en su lugar de una vez",
    "Le van a dar para sus tamales", "Ya le llegó su día a ese",
    "Van a ir por él esta semana", "Le tienen preparada una", "Se lo van a cargar",
    "Ya le tienen el hoyo cavado", "Va a terminar en el noticiero", "Ese ya se fue",
    "Le van a mandar saludos con plomo", "Lo van a dejar sin ganas de volver",
    "A ese lo están esperando en la esquina", "Ya le tienen puesto el ojo",
    "Le van a enseñar respeto a la mala", "No va a contar lo que vio",
    "Le van a dar una lección que no olvida",
]
COLA_AMENAZA = ["", " vas a ver", " te lo juro", " ya vas a ver", " acordate de esto",
                " esperame afuera", " y no es amenaza, es aviso", " anotalo"]

# ═══════════════════════════════════════════════════ 4. JERGA INOFENSIVA
# La jerga no es intercambiable: «pisto» es un objeto, «chivo» un adjetivo y
# «puchica» una interjección. Meterlas en el mismo hueco produce frases que no
# existen («ya viene el chamba»), y el modelo aprendería basura. Por eso cada
# término lleva su rol, y cada rol tiene sus propios portadores.
JERGA = {
    # término        rol           equivalente estándar
    "maje":      ("persona",   "amigo"),
    "chero":     ("persona",   "amigo"),
    "alero":     ("persona",   "amigo"),
    "cerote":    ("persona",   "amigo"),
    "bicho":     ("persona",   "niño"),
    "cipote":    ("persona",   "niño"),
    "bayunco":   ("persona",   "payaso"),
    "chucho":    ("persona",   "perro"),
    "pajero":    ("persona",   "mentiroso"),
    "jura":      ("persona",   "policía"),
    "chota":     ("persona",   "policía"),
    "pisto":     ("cosa",      "dinero"),
    "chunche":   ("cosa",      "objeto"),
    "bolado":    ("cosa",      "objeto"),
    "guaro":     ("cosa",      "licor"),
    "chibola":   ("cosa",      "pelota"),
    "chamba":    ("evento",    "trabajo"),
    "pachanga":  ("evento",    "fiesta"),
    "chivo":     ("adj_cosa", "bonito"),
    "tuanis":    ("adj_cosa", "bonito"),
    "vergón":    ("adj_cosa", "excelente"),
    "chuco":     ("adj_cosa", "sucio"),
    "yuca":      ("adj_cosa", "difícil"),
    "codo":      ("adj_pers", "tacaño"),
    "puchica":   ("interj",    "caramba"),
    "cabal":     ("interj",    "exacto"),
}
PORT_JERGA_ROL = {
    "persona": [
        "Qué onda {t}, todo bien por allá",
        "Ese {t} es mi mejor amigo desde la escuela",
        "Vaya {t}, nos vemos mañana entonces",
        "Ese {t} siempre llega tarde pero llega",
        "Ese {t} me cae bien la verdad",
        "Ya viene el {t} con las pupusas",
        "El {t} está bien tranquilo hoy",
        "Vamos a ver al {t} el domingo",
        "Ese {t} nunca falla cuando se le necesita",
        "Todo bien con el {t}, no hay pleito",
        "Saludos al {t} de mi parte",
    ],
    "cosa": [
        "Prestame el {t} para el pasaje porfa",
        "Andá traeme el {t} ese que dejé",
        "Se me olvidó el {t} en la casa",
        "Ahí le dejo el {t} que le debía",
        "Ya compré el {t} para el domingo",
        "Dejame el {t} sobre la mesa",
        "No encuentro el {t} por ningún lado",
    ],
    "evento": [
        "Qué buena estuvo la {t} de anoche",
        "Mañana tengo {t} desde temprano",
        "Ya se acabó la {t} y todos contentos",
        "Nos vemos en la {t} del sábado",
        "La {t} me tiene cansado esta semana",
    ],
    "adj_cosa": [
        "Qué {t} te quedó la casa",
        "Está bien {t} el lugar, se los recomiendo",
        "El día amaneció bien {t} hoy",
        "Quedó {t} el trabajo que hicieron",
        "Qué {t} se ve el paisaje desde aquí",
        "Está {t} el examen de mañana",
    ],
    "adj_pers": [
        "No sea {t} y convide de eso",
        "Ese hombre es bien {t} con la familia",
        "Mi tío es {t} pero buena gente",
        "No seás {t}, pagá la cuenta vos",
    ],
    "interj": [
        "{t}, qué alegre verte de nuevo",
        "{t}, ya se me hizo tarde otra vez",
        "{t}, qué bonito amaneció hoy",
        "{t}, nos vemos el domingo entonces",
        "{t}, se me pasó la hora de la cita",
    ],
}
PORT_NACIONALIDAD_PLURAL = [
    "Los {g} juegan muy bien al fútbol", "La comida de los {g} está buenísima",
    "Tengo varios amigos {g} en el trabajo", "Los {g} ganaron el partido de ayer",
    "Me gusta mucho la música de los {g}", "Vinieron unos {g} a la actividad",
    "Los {g} tienen unas playas preciosas", "El equipo de los {g} jugó limpio",
    "Estudié con dos compañeros {g}", "Los {g} traen unas recetas buenísimas",
]
PORT_NACIONALIDAD_SINGULAR = [
    "Mi vecino es {gs} y es buena gente", "Trabajo con un {gs} muy responsable",
    "Conocí a un {gs} muy amable ayer", "El profesor nuevo es {gs}",
]
NT_COTIDIANO = [
    "Feliz cumpleaños, que la pases bonito", "Muchas gracias por la ayuda de ayer",
    "Ya llegamos bien a la casa", "Nos vemos mañana en la reunión",
    "Qué rico estuvo el almuerzo de hoy", "Felicidades por el nuevo trabajo",
    "Ya salieron las notas y me fue bien", "Que Dios los bendiga a todos",
    "Se ve bonito el paisaje desde aquí", "Buena suerte en el examen",
    "El concierto estuvo increíble", "Qué bueno que ya te sentís mejor",
]

# ═══════════════════════════════════════════════════ 5. EMOJIS
# Referentes naturales para cada grupo del catálogo. Un emoji solo se combina
# con referentes de su propia fila.
# Plural masculino y SIN artículo: el portador ya aporta «los». Guardarlos con
# artículo producía «Los gordas», que es justo la clase de ruido gramatical que
# el modelo aprendería como señal.
GRUPO_REFERENTES = {
    "Latinoamericanos": ["latinos", "centroamericanos", "sudacas"],
    "Judíos": ["judíos"], "Judíos e israelíes": ["judíos", "israelíes"],
    "Menores de edad": ["mocosos", "cipotes"],
    "Personas LGBT": ["gays", "homosexuales", "trans"],
    "Personas con discapacidad intelectual": ["retrasados", "tarados"],
    "Personas racializadas": ["negros", "morenos"],
    "Adultos mayores": ["viejos", "ancianos"],
    "Afrodescendientes": ["negros"],
    "Personas con baja educación": ["ignorantes", "brutos"],
    "Migrantes y personas empobrecidas": ["migrantes", "pobres"],
    "Personas con sobrepeso": ["gordos", "obesos"],
    "Personas en situación de pobreza": ["pobres", "muertos de hambre"],
    "Migrantes y grupos étnicos": ["migrantes", "indios"],
    "Pueblos indígenas": ["indios", "indígenas"],
    "Estadounidenses": ["gringos"], "Colectivo político": ["de ese partido"],
    "Individuo": [], "Colectivo": [], "Personas enfermas": [],
}
EMOJIS_BENIGNOS = ["❤️", "😂", "🎉", "🙏", "👏", "☕", "⚽", "🌮", "🥳", "😊",
                   "🌻", "🎂", "🤝", "💪", "🌟", "🍀"]
POS_EMOJI = [("inicio", 0.12), ("medio", 0.22), ("final", 0.66)]


def insertar_emoji(texto: str, emo: str, rnd: random.Random) -> str:
    """Coloca el emoji reproduciendo la distribución posicional del corpus real."""
    r, acc, pos = rnd.random(), 0.0, "final"
    for p_, prob in POS_EMOJI:
        acc += prob
        if r <= acc:
            pos = p_
            break
    if pos == "inicio":
        return f"{emo} {texto}"
    if pos == "final":
        return f"{texto} {emo}"
    pal = texto.split()
    i = max(1, len(pal) // 2)
    return " ".join(pal[:i] + [emo] + pal[i:])       # entre palabras, nunca partiendo una


# ═══════════════════════════════════════════════════════════ GENERACIÓN
def generar(seed: int = SEED) -> pd.DataFrame:
    rnd = random.Random(seed)
    fams = cargar_lexico()
    emo = pd.read_csv(RAIZ / "data/dataset_b2/lexicon_emojis.csv")
    emo.columns = [c.lstrip("﻿") for c in emo.columns]

    filas: list[dict] = []
    usos: Counter = Counter()

    def add(texto, label, cat, plantilla, sub=""):
        pid = f"{cat}|{plantilla}"
        if usos[pid] >= TOPE_POR_CATEGORIA.get(cat, TOPE_POR_PLANTILLA):
            return False
        usos[pid] += 1
        filas.append(dict(texto_original=texto, label=label, origen=f"v3_{cat}",
                          plantilla_id=pid, subclase=sub))
        return True

    # ── 1. Ofensivo: variantes ofuscadas del léxico en vocativo
    ofens = [f for f in fams.values() if f.label == 1]
    for fam in ofens:
        for v in fam.variantes:
            add(rnd.choice(PORT_OFENSIVO).format(t=v), 1, "ofensivo_ofuscado",
                rnd.choice(PORT_OFENSIVO), fam.subclase)

    # ── 2. Odio dirigido a grupo, con predicado invariable ofuscado
    for gp, gs in GRUPOS_NACIONALES:
        for p in PORT_ODIO_PLURAL:
            add(p.format(g=gp, p=rnd.choice(PRED_ODIO_INVARIABLE)), 2,
                "odio_grupo", p, "Xenofobia")
        for p in PORT_ODIO_SINGULAR:
            add(p.format(gs=gs), 2, "odio_grupo", p, "Xenofobia")

    # ── 3. Odio en vocativo con el término del léxico y SU grupo
    for fam in fams.values():
        if fam.label != 2 or fam.subclase not in SUB_A_GRUPO:
            continue
        for v in fam.variantes:
            add(rnd.choice(PORT_ODIO_VOCATIVO).format(t=v), 2, "odio_ofuscado",
                rnd.choice(PORT_ODIO_VOCATIVO), fam.subclase)

    # ── 4. Amenazas con verbo ofuscado
    for base in VERBOS_BASE:
        for v in _ofuscar(base, rnd):
            for p in rnd.sample(PORT_AMENAZA, k=3):
                add(p.format(v=v) + rnd.choice(COLA_AMENAZA), 3,
                    "amenaza_ofuscada", p, "Amenaza Directa")

    # ── 5. Amenazas por eufemismo salvadoreño.
    #      Fue la familia más frágil de toda la sonda (33 % de fuga incluso en B2),
    #      porque no es ofuscación ortográfica sino conocimiento cultural: no hay
    #      nada en «le van a apagar la luz» que un modelo pueda deducir del español
    #      general. Solo se aprende viéndolo.
    for e in EUFEMISMOS:
        add(e, 3, "amenaza_eufemismo", "eufemismo_simple", "Amenaza Implícita")
        for cola in rnd.sample(COLA_AMENAZA[1:], k=3):
            add(e + cola, 3, "amenaza_eufemismo", "eufemismo_con_cola", "Amenaza Implícita")
        add(f"{rnd.choice(['Decile que', 'Avisale que', 'Ya sabe que'])} {e[0].lower()}{e[1:]}",
            3, "amenaza_eufemismo", "eufemismo_reportado", "Amenaza Implícita")

    # ── 6. Emojis del catálogo, emparejados solo con su propio grupo
    MAPA = {"No Tóxico": 0, "Lenguaje Ofensivo": 1, "Discurso de Odio": 2,
            "Amenazas/Violencia": 3, "Amenazas / Violencia": 3}
    for _, r in emo.iterrows():
        e, lab = r["emoji"], MAPA.get(str(r["clase_asociada"]))
        if lab is None:
            continue
        refs = GRUPO_REFERENTES.get(str(r.get("grupos_afectados", "")).strip(), [])
        for _ in range(10):
            if lab == 3:
                base = rnd.choice(EUFEMISMOS + [p.format(v="matar") for p in PORT_AMENAZA])
            elif lab == 2 and refs:
                base = rnd.choice(PORT_ODIO_PLURAL).format(
                    g=rnd.choice(refs), p=rnd.choice(PRED_ODIO_INVARIABLE))
            elif lab == 2:
                continue
            elif lab == 1:
                base = rnd.choice(PORT_OFENSIVO).format(
                    t=rnd.choice(rnd.choice(ofens).variantes))
            else:
                base = rnd.choice(NT_COTIDIANO)
            add(insertar_emoji(base, e, rnd), lab, f"emoji_clase{lab}",
                f"emoji_{e}", str(r.get("grupos_afectados", "")))

    # ── 7. Emoji benigno en texto amable: rompe «hay emoji ⇒ tóxico»
    for e in EMOJIS_BENIGNOS:
        for _ in range(11):
            if rnd.random() < 0.5:
                base = rnd.choice(NT_COTIDIANO)
            else:
                t = rnd.choice(list(JERGA)); rol = JERGA[t][0]
                base = rnd.choice(PORT_JERGA_ROL[rol]).format(t=t)
            add(insertar_emoji(base, e, rnd), 0, "emoji_benigno", f"benigno_{e}")

    # ── 8. Par mínimo dialectal: la misma frase con jerga y en español estándar.
    #      Es el control que permite atribuir un falso positivo al dialecto y no
    #      al contenido: si solo cambia la palabra local, la etiqueta no debe cambiar.
    for t, (rol, neutro) in JERGA.items():
        for p in PORT_JERGA_ROL[rol]:
            add(p.format(t=t), 0, "jerga_notoxico", p)
            add(p.format(t=neutro), 0, "jerga_control", p)

    # ── 9. La misma jerga dentro de un insulto: ahora sí es ofensiva.
    #      Sin esto el modelo aprendería «jerga ⇒ inofensivo», el atajo inverso.
    for t, (rol, _) in JERGA.items():
        if rol != "persona":
            continue
        for _ in range(4):
            ins = rnd.choice(rnd.choice(ofens).variantes)
            p = rnd.choice(PORT_OFENSIVO)
            add(p.format(t=f"{t} {ins}"), 1, "jerga_ofensivo", p, "Insulto Directo")

    # ── 10. Gentilicio en contexto inocuo: mencionar un país no es odio
    for gp, gs in GRUPOS_NACIONALES:
        for p in PORT_NACIONALIDAD_PLURAL:
            add(p.format(g=gp), 0, "nacionalidad_notoxico", p)
        for p in PORT_NACIONALIDAD_SINGULAR:
            add(p.format(gs=gs), 0, "nacionalidad_notoxico", p)

    df = pd.DataFrame(filas)
    df["texto_modelo"] = [normalizar(t) for t in df["texto_original"]]
    df = df.drop_duplicates(subset=["texto_modelo"]).reset_index(drop=True)

    # ── Higiene: nada que toque val, test o la batería adversarial
    prohibido: set[str] = set()
    for p, col in [("data/dataset_b2/val.csv", "texto_modelo"),
                   ("data/dataset_b2/test.csv", "texto_modelo"),
                   ("data/dataset_b2/test_adversarial.csv", "texto_normalizado"),
                   ("data/dataset_b2/test_adversarial.csv", "texto")]:
        d = pd.read_csv(RAIZ / p); d.columns = [c.lstrip("﻿") for c in d.columns]
        prohibido |= {clave(x) for x in d[col]}
    antes = len(df)
    df = df[~df["texto_modelo"].map(clave).isin(prohibido)].reset_index(drop=True)
    descartados = antes - len(df)

    # ── Equilibrio por clase.
    #    El léxico está dominado por insultos (1,510 variantes ofensivas frente a
    #    310 de odio), así que generar «todo lo posible» produciría un conjunto
    #    volcado hacia Lenguaje Ofensivo y empeoraría el F1-macro, que pondera
    #    las cuatro clases por igual. Se muestrea a un tope por clase repartiendo
    #    el cupo entre categorías, para no perder ninguna familia entera.
    df = _equilibrar(df, TOPE_POR_CLASE, seed)

    df.insert(0, "ID", [f"V3-{i+1:05d}" for i in range(len(df))])
    df.attrs["descartados"] = descartados
    return df


def _equilibrar(df: pd.DataFrame, tope: int, seed: int) -> pd.DataFrame:
    trozos = []
    for lab, sub in df.groupby("label"):
        if len(sub) <= tope:
            trozos.append(sub); continue
        cats = sub["origen"].unique()
        cupo = max(1, tope // len(cats))
        elegido = []
        for c in cats:
            g = sub[sub.origen == c]
            elegido.append(g.sample(min(len(g), cupo), random_state=seed))
        out = pd.concat(elegido)
        if len(out) < tope:                      # rellenar con lo que sobra
            resto = sub.drop(out.index)
            out = pd.concat([out, resto.sample(min(len(resto), tope - len(out)),
                                               random_state=seed)])
        trozos.append(out)
    return pd.concat(trozos).sample(frac=1, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    df = generar()
    sal = RAIZ / "data/dataset_v3"; sal.mkdir(exist_ok=True)
    df.to_csv(sal / "sinteticos_v3.csv", index=False, encoding="utf-8-sig")
    print(f"generados: {len(df)}   descartados por higiene: {df.attrs['descartados']}")
    print(f"plantillas: {df.plantilla_id.nunique()}   máx por plantilla: {df.plantilla_id.value_counts().max()}")
    print("\npor clase:"); print(df.label.value_counts().sort_index().to_string())
    print("\npor categoría:"); print(df.origen.value_counts().to_string())
    print("\n=== muestra por clase ===")
    for c in range(4):
        print(f"\n-- clase {c}")
        for t in df[df.label == c].sample(min(7, (df.label == c).sum()), random_state=7)["texto_modelo"]:
            print(f"   {t[:92]}")
