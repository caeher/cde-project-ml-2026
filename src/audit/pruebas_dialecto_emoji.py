# -*- coding: utf-8 -*-
"""
Dos baterías de prueba nuevas.

BATERÍA F — Falsos amigos dialectales
    Palabras que en otras variantes del español son insultos fuertes pero en
    El Salvador son de uso cotidiano y neutro. Ejemplo canónico: «pajero» aquí
    significa «mentiroso», no lo que significa en España.
    Se incluyen pares de contraste: la MISMA palabra en contexto agresivo, donde
    sí es ofensiva. Si el modelo usa contexto y no diccionario, debe distinguirlos.

BATERÍA G — Pares mínimos de emoji
    El mismo texto base con distinto emoji. Solo cambia el emoji, y con él la
    clase correcta. Aísla exactamente cuánto aporta el emoji al significado.
"""

# =====================================================================
# BATERÍA F — FALSOS AMIGOS DIALECTALES
# =====================================================================
# (texto, clase esperada, palabra clave, por qué)
FALSOS_AMIGOS = [
    # --- pajero / paja : mentiroso / mentira ---
    ("No sea pajero, contame la verdad", 0, "pajero",
     "En SV «pajero» = mentiroso. Reproche coloquial entre amigos"),
    ("Ese maje es bien pajero, nunca cumple", 0, "pajero",
     "Describe a alguien poco confiable, registro cotidiano"),
    ("Qué paja tan buena la que contó anoche", 0, "paja",
     "«Paja» = cuento, anécdota. Elogio, no insulto"),
    ("Dejate de pajas y andá a trabajar", 0, "paja",
     "«Dejate de pajas» = deja de perder el tiempo"),
    ("Puras pajas las que dice ese noticiero", 0, "paja",
     "Crítica a un medio, sin insulto a persona"),

    # --- cerote : amigo (o insulto, según contexto) ---
    ("Ese cerote me ayudó cuando más lo necesitaba", 0, "cerote",
     "Uso afectivo entre amigos, muy común en SV"),
    ("Qué onda cerote, cómo has estado", 0, "cerote",
     "Saludo entre conocidos"),

    # --- bicho / cipote : niño ---
    ("Los bichos ya salieron de vacaciones", 0, "bicho",
     "«Bicho» = niño en SV. En Puerto Rico es vulgar"),
    ("Mi cipote entra a la universidad este año", 0, "cipote",
     "«Cipote» = niño en SV. En España es vulgar"),
    ("No sea bicho, présteme el cuaderno un ratito", 0, "bicho",
     "Aquí «bicho» = tonto, en tono de broma"),

    # --- verga / vergón : expresión o elogio ---
    ("Está bien vergón el carro que te compraste", 0, "vergón",
     "«Vergón» = excelente. Elogio pese a la raíz vulgar"),
    ("Qué verga, ni me acordaba de la reunión", 0, "verga",
     "Interjección de sorpresa, sin destinatario"),
    ("A la gran puta, qué frío está haciendo", 0, "puta",
     "Interjección meteorológica, no dirigida a nadie"),
    ("Puchica, se me olvidó el cumpleaños", 0, "puchica",
     "Eufemismo suavizado, equivale a «caramba»"),

    # --- otros ---
    ("Anoche andaba bien pedo en la fiesta del barrio", 0, "pedo",
     "«Pedo» = ebrio. Descripción, no insulto"),
    ("Mi chero me acompañó al hospital toda la noche", 0, "chero",
     "«Chero» = amigo"),
    ("Prestame pisto para el pasaje porfa", 0, "pisto",
     "«Pisto» = dinero"),
    ("Qué chivo quedó el mural de la escuela", 0, "chivo",
     "«Chivo» = bonito, chévere"),
    ("Ese bayunco no sabe bailar pero se anima", 0, "bayunco",
     "«Bayunco» = torpe, en tono cariñoso"),
    ("El chucho de la vecina ladra toda la noche", 0, "chucho",
     "«Chucho» = perro, literal"),
    ("No sea chucho y convide del almuerzo", 0, "chucho",
     "«Chucho» = tacaño, reproche leve"),
    ("Vamos por unos guaros el viernes", 0, "guaro",
     "«Guaro» = licor"),
    ("Quedó bien chuco el patio con el lodo", 0, "chuco",
     "«Chuco» = sucio, describe un patio"),
    ("Cabal a las seis nos vemos entonces", 0, "cabal",
     "«Cabal» = exacto, confirmación"),
    ("Había un cachimbo de gente en el mercado", 0, "cachimbo",
     "«Cachimbo» = mucho"),
    ("Mi chele ya cumplió el añito", 0, "chele",
     "«Chele» = de piel clara. Aquí afectivo hacia un bebé"),
    ("Se nos reventó la chibola en pleno partido", 0, "chibola",
     "«Chibola» = pelota"),
    ("Se armó el desmadre en la fiesta pero todo bien", 0, "desmadre",
     "«Desmadre» = alboroto, sin agresión"),
    ("Ese maje es bien codo, nunca invita", 0, "codo",
     "«Codo» = tacaño, comentario ligero"),
    ("Nos tomamos unas minutas en el parque ayer", 0, "minutas",
     "«Minuta» = raspado de hielo"),

    # --- CONTRASTE: misma palabra, contexto agresivo -> SÍ es ofensivo ---
    ("Sos un pajero de mierda, no volvás a hablarme", 1, "pajero",
     "CONTRASTE: la misma palabra dirigida como agresión"),
    ("Callate cerote hijo de puta", 1, "cerote",
     "CONTRASTE: «cerote» como insulto real"),
    ("Ese bicho no sirve para nada, es un inútil", 1, "bicho",
     "CONTRASTE: descalificación directa a una persona"),
    ("Andá a la gran verga vos y tu familia", 1, "verga",
     "CONTRASTE: mandar a la verga a alguien es ofensivo"),
]

# =====================================================================
# BATERÍA G — PARES MÍNIMOS DE EMOJI
# =====================================================================
# (texto base, [(emoji, clase esperada, por qué)])
PARES_EMOJI = [
    ("Ya sabés lo que te espera", [
        ("", 0, "Sin emoji es ambiguo pero inocuo: puede ser una sorpresa"),
        ("🎂", 0, "El pastel lo vuelve claramente una sorpresa de cumpleaños"),
        ("🎉", 0, "Celebración"),
        ("🔫", 3, "El arma lo convierte en amenaza explícita"),
        ("⚰️", 3, "El ataúd lo convierte en amenaza de muerte"),
    ]),
    ("Te voy a buscar mañana", [
        ("", 0, "Frase cotidiana: pasar a recoger a alguien"),
        ("❤️", 0, "Afectivo: una cita"),
        ("🚗", 0, "Literal: ir en carro"),
        ("🔪", 3, "El cuchillo lo convierte en amenaza"),
        ("💀", 3, "La calavera señala amenaza de muerte"),
    ]),
    ("Mirá a este", [
        ("", 0, "Señalar a alguien, neutro"),
        ("😍", 0, "Admiración"),
        ("👏", 0, "Reconocimiento"),
        ("🤡", 1, "El payaso lo convierte en burla"),
        ("💩", 1, "Desprecio explícito"),
    ]),
    ("Los que vienen del sur", [
        ("", 0, "Descripción geográfica neutra"),
        ("⚽", 0, "Contexto deportivo"),
        ("🇸🇻", 0, "Referencia nacional neutra"),
        ("🐒", 2, "El mono deshumaniza: bestialización racial"),
        ("🪳", 2, "La cucaracha deshumaniza al grupo"),
    ]),
    ("Ahí viene el grupo de siempre", [
        ("", 0, "Comentario cotidiano"),
        ("🙌", 0, "Entusiasmo por ver a los amigos"),
        ("🐀", 2, "Las ratas deshumanizan al colectivo"),
        ("🧹", 3, "La escoba evoca «limpieza» eliminacionista"),
    ]),
    ("No lo quiero ver más por aquí", [
        ("", 1, "Rechazo fuerte pero sin ataque a grupo"),
        ("🙏", 0, "Con el rezo suena a hartazgo resignado"),
        ("🔫", 3, "El arma lo vuelve amenaza"),
    ]),
    ("Qué bonita familia", [
        ("", 0, "Elogio"),
        ("❤️", 0, "Elogio afectuoso"),
        ("🤮", 1, "El vómito lo convierte en burla despectiva"),
        ("🐷", 2, "El cerdo señala gordofobia hacia la familia"),
    ]),
    ("Ese es el vecino nuevo", [
        ("", 0, "Presentación neutra"),
        ("👋", 0, "Saludo cordial"),
        ("🌑", 2, "La luna negra alude despectivamente a la tez"),
        ("🦶", 2, "Referencia despectiva racializada"),
    ]),
]


def construir():
    """Devuelve las dos baterías como lista de diccionarios."""
    casos = []
    for texto, esp, palabra, motivo in FALSOS_AMIGOS:
        casos.append(dict(bateria="F. Falsos amigos dialectales", base=palabra,
                          variante="agresivo" if esp == 1 else "cotidiano",
                          texto=texto, esperado=esp, motivo=motivo))
    for base, variantes in PARES_EMOJI:
        for emo, esp, motivo in variantes:
            casos.append(dict(bateria="G. Pares mínimos de emoji", base=base,
                              variante=emo if emo else "(sin emoji)",
                              texto=f"{base} {emo}".strip(), esperado=esp,
                              motivo=motivo))
    return casos


if __name__ == "__main__":
    import sys
    import numpy as np
    import pandas as pd
    sys.path.insert(0, "/sessions/bold-practical-shannon/mnt/outputs")
    sys.path.insert(0, "/sessions/bold-practical-shannon/mnt/proyecto")
    from xlmr_numpy import XLMRNumpy, CLASES
    from src.features.normalization import normalizar

    df = pd.DataFrame(construir())
    m = XLMRNumpy()
    textos = [normalizar(t) for t in df.texto]
    L = []
    for i in range(0, len(textos), 24):
        X, M = m.codificar(textos[i:i + 24], max_length=128)
        L.append(m.forward(X, M))
    L = np.concatenate(L)
    e = np.exp(L - L.max(-1, keepdims=True))
    P = e / e.sum(-1, keepdims=True)
    df["pred"] = L.argmax(-1)
    df["conf"] = P.max(-1)
    df["ok"] = df.pred == df.esperado
    df["clase_esperada"] = df.esperado.map(dict(enumerate(CLASES)))
    df["clase_predicha"] = df.pred.map(dict(enumerate(CLASES)))
    df.to_csv("/sessions/bold-practical-shannon/mnt/proyecto/reports/pruebas_dialecto_emoji.csv",
              index=False, encoding="utf-8-sig")
    print(f"guardado {len(df)} casos")
    print(df.groupby("bateria").ok.agg(["sum", "size"]).to_string())
