# -*- coding: utf-8 -*-
"""
Batería adversarial para el modelo XLM-R del equipo.

Mide robustez ante:
  A. Ofuscación de groserías (asteriscos, arroba, numeral, leetspeak)
  B. Emojis como vehículo del ataque (crudos vs demojizados)
  C. Amenazas ofuscadas
  D. Falsos positivos sobre jerga salvadoreña inofensiva
"""
import sys
sys.path.insert(0, "/sessions/bold-practical-shannon/mnt/outputs")
sys.path.insert(0, "/sessions/bold-practical-shannon/mnt/proyecto")

CASOS = []


def add(grupo, base, variante, texto, esperado):
    CASOS.append(dict(grupo=grupo, base=base, variante=variante,
                      texto=texto, esperado=esperado))


# ------------------------------------------------------- A. Ofuscación
OFUSC = [
    ("Sos una puta barata", 1, [
        ("original", "Sos una puta barata"),
        ("asterisco", "Sos una p*ta barata"),
        ("arroba", "Sos una put@ barata"),
        ("numeral", "Sos una p#ta barata"),
        ("leetspeak", "Sos una pu74 barata"),
        ("vocal_v", "Sos una pvta barata"),
        ("espaciado", "Sos una p u t a barata"),
        ("repeticion", "Sos una puuuta barata"),
    ]),
    ("Qué mierda de gente", 1, [
        ("original", "Qué mierda de gente"),
        ("leetspeak", "Qué m13rda de gente"),
        ("asterisco", "Qué m*erda de gente"),
        ("arroba", "Qué mierd@ de gente"),
    ]),
    ("Andate a la verga pendejo", 1, [
        ("original", "Andate a la verga pendejo"),
        ("leetspeak", "Andate a la v3rg4 p3nd3j0"),
        ("asterisco", "Andate a la v*rga p*ndejo"),
        ("numeral", "Andate a la v#rga p#ndejo"),
    ]),
    ("Son unos hijos de puta", 1, [
        ("original", "Son unos hijos de puta"),
        ("sigla", "Son unos HDP"),
        ("leetspeak", "Son unos hij0s d3 pu74"),
        ("asterisco", "Son unos hijos de p***"),
    ]),
]
for base, esp, vs in OFUSC:
    for nombre, txt in vs:
        add("A. Ofuscación de groserías", base, nombre, txt, esp)

# ------------------------------------------------------- B. Emojis
EMOJI = [
    ("Insulto por emoji", 1, [
        ("solo_texto", "Mira a este tipo"),
        ("con_payaso", "Mira a este tipo 🤡"),
        ("con_caca", "Mira a este tipo 💩"),
        ("con_dedo", "Mira a este tipo 🖕"),
        ("con_dedo_tono", "Mira a este tipo 🖕🏽"),
        ("multiple", "Mira a este tipo 🤡💩🖕"),
    ]),
    ("Odio racial por emoji", 2, [
        ("neutro", "Los jugadores de ese equipo"),
        ("mono", "Los jugadores de ese equipo 🐒"),
        ("mono_bandera", "Los jugadores de ese equipo 🐒🇸🇻"),
        ("bestializacion", "Esos 🐒🐒 no merecen jugar"),
    ]),
    ("Amenaza por emoji", 3, [
        ("neutro", "Te espero afuera"),
        ("pistola", "Te espero afuera 🔫"),
        ("cuchillo", "Te espero afuera 🔪"),
        ("ataud", "Te espero afuera ⚰️"),
        ("combo", "Te espero afuera 🔫⚰️"),
    ]),
    ("Positivo con emoji", 0, [
        ("neutro", "Qué alegre verte de nuevo"),
        ("corazon", "Qué alegre verte de nuevo ❤️"),
        ("risa", "Qué alegre verte de nuevo 😂"),
    ]),
]
for base, esp, vs in EMOJI:
    for nombre, txt in vs:
        add("B. Emojis", base, nombre, txt, esp)

# ------------------------------------------------------- C. Amenazas
AMEN = [
    ("Te voy a matar", 3, [
        ("original", "Te voy a matar"),
        ("leetspeak", "Te voy a m4t4r"),
        ("asterisco", "Te voy a m*tar"),
        ("eufemismo", "Te voy a dar piso"),
        ("indirecta", "Ya sabés lo que te va a pasar"),
    ]),
    ("Hay que matarlos a todos", 3, [
        ("original", "Hay que matarlos a todos"),
        ("leetspeak", "Hay que m4t4rl0s a todos"),
        ("eufemismo_sv", "Hay que darles cuello a todos"),
        ("celebracion", "Bien hecho que lo mataron, uno menos"),
    ]),
    ("Ojalá se muera", 3, [
        ("original", "Ojalá se muera ese maldito"),
        ("asterisco", "Ojalá se m*era ese maldito"),
    ]),
]
for base, esp, vs in AMEN:
    for nombre, txt in vs:
        add("C. Amenazas ofuscadas", base, nombre, txt, esp)

# ------------------------------------------------------- D. Jerga inofensiva
JERGA = [
    "Qué verga, maje, qué alegre verte",
    "Puta, qué rico estuvo el almuerzo",
    "A huevo que sí, vamos a la playa",
    "Ese cerote es mi mejor amigo desde la escuela",
    "Qué chivo tu carro, maje",
    "No sea bicho, ayudame con esto",
    "Vaya pues, nos vemos mañana cabal",
    "Está bien vergón el concierto",
    "Qué onda maje, todo tranquilo",
    "Mi cipote ya cumplió los quince",
    "Andaba bien pedo pero llegó bien",
    "Puchica, se me olvidó la cita",
    "Vamos a comer pupusas al mercado",
    "Ese bayunco no sabe ni manejar",
]
for t in JERGA:
    add("D. Jerga salvadoreña inofensiva", "neutro con jerga", "-", t, 0)

# Control: mismo registro sin jerga
CONTROL = [
    "Qué bueno verte de nuevo",
    "Estuvo muy rico el almuerzo",
    "Claro que sí, vamos a la playa",
    "Ese muchacho es mi mejor amigo desde la escuela",
    "Qué bonito tu carro",
    "Por favor ayudame con esto",
    "Está bien, nos vemos mañana",
    "Estuvo excelente el concierto",
    "Hola, todo tranquilo",
    "Mi hijo ya cumplió los quince",
    "Se me olvidó la cita",
    "Vamos a comer al mercado",
]
for t in CONTROL:
    add("E. Control sin jerga", "neutro estándar", "-", t, 0)


if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    from xlmr_numpy import XLMRNumpy, CLASES
    from src.features.normalization import normalizar

    m = XLMRNumpy()
    df = pd.DataFrame(CASOS)

    # Dos condiciones: texto crudo, y texto pasado por la normalización del proyecto
    for col, fn in [("crudo", lambda t: t), ("normalizado", normalizar)]:
        textos = [fn(t) for t in df.texto]
        L = []
        for i in range(0, len(textos), 24):
            X, M = m.codificar(textos[i:i + 24], max_length=128)
            L.append(m.forward(X, M))
        L = np.concatenate(L)
        e = np.exp(L - L.max(-1, keepdims=True)); P = e / e.sum(-1, keepdims=True)
        df[f"pred_{col}"] = L.argmax(-1)
        df[f"conf_{col}"] = P.max(-1)

    df["texto_norm"] = [normalizar(t) for t in df.texto]
    df.to_csv("/sessions/bold-practical-shannon/mnt/outputs/adversarial_result.csv",
              index=False, encoding="utf-8-sig")
    print("guardado adversarial_result.csv |", len(df), "casos")
