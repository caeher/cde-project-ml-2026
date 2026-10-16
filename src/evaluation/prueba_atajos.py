# -*- coding: utf-8 -*-
"""Pruebas de atajos por invariancia contrafactual (diagnóstico, NO se entrena con esto).

Idea: si el modelo usa un atajo (palabra, grupo, tema, emoji), cambiar solo ese elemento
debería cambiar la predicción. Si la clase debe mantenerse, la predicción debe mantenerse.

  1. Intercambio de grupo: el mismo ataque dirigido a distintos grupos protegidos → misma clase (Odio).
  2. Mención neutra de grupo: el mismo enunciado neutro con distintos grupos → No Tóxico (sin atajo "mencionar grupo = tóxico").
  3. Tema: la misma amenaza explícita en 8 temas → Amenazas; el mismo comentario neutro → No Tóxico.
  4. Emoji inocuo: añadir 😂 🙏 ❤️ a textos neutros no debe volverlos tóxicos.
  5. Palabra gatillo en contexto inocuo: «matar», «vergas», «cerote», «veneco/nica» sin ataque.

Uso: python src/evaluation/prueba_atajos.py [ruta_modelos]   (por defecto el modelo que usa la API)
"""
import sys
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import app.api.main as M  # noqa: E402

GRUPOS = ["las mujeres", "los gays", "los venezolanos", "los hondureños", "los indígenas", "los migrantes", "los nicaragüenses", "las lesbianas"]
ATAQUES = ["{G} son una plaga y no deberían estar en este país", "Qué asco {G}, no valen nada", "{G} son basura, que se vayan de aquí",
           "Todos {G} son iguales, gente inferior", "No quiero a {G} cerca, son lo peor"]
NEUTROS = ["Hoy hablamos con {G} que llegaron a la comunidad", "La organización de {G} presentó su informe anual", "Conozco a {G} que trabajan en mi oficina",
           "Hay una charla sobre los derechos de {G} el viernes", "Muchas de {G} participaron en la feria"]
TEMAS = ["el tráfico", "el partido", "la reforma", "el concierto", "la tormenta", "el estadio", "la Asamblea", "el aumento de precios"]
AMENAZA = ["Te voy a matar si seguís hablando de {T}", "Voy a ir a buscarte y te rompo la cara por lo de {T}", "Ojalá se mueran todos los que defienden {T}"]
NEUTRO_T = ["Qué opinan de {T}, yo todavía no me decido", "Hoy salió una noticia sobre {T}", "Mañana hablamos de {T} con calma"]
EMOJI_BASE = ["Qué buena noticia para la comunidad", "Gracias por la información", "Nos vemos mañana en la reunión", "Excelente trabajo del equipo", "Me parece una buena idea"]
EMOJIS = ["😂", "🙏", "❤️", "🔥", "👍", "🤡"]
GATILLO = ["Voy a matar el tiempo leyendo un rato", "Ese vergón de partido estuvo buenísimo", "Qué cerote tan buena onda es mi cuate",
           "Mi vecino veneco me regaló unas arepas", "La señora nica que vende en el mercado es muy amable", "Me muero de risa con este video",
           "Se la va a matar la selección el sábado", "Qué verga, maje, qué alegre verte"]


def clase(t):
    return M.predecir(t)["label"]


def tasa(textos, esperado):
    p = np.array([clase(t) for t in textos]); return float((p == esperado).mean()), p


def main():
    if len(sys.argv) > 1:
        M.MODELOS = Path(sys.argv[1]); M._modelos.clear()
    res = {}
    t = [a.format(G=g) for a in ATAQUES for g in GRUPOS]; r, p = tasa(t, 2)
    res["1. ataque a grupo → Odio"] = r
    por_g = {g: float(np.mean([clase(a.format(G=g)) == 2 for a in ATAQUES])) for g in GRUPOS}
    print("  Odio por grupo:", {k: round(v, 2) for k, v in por_g.items()}, "| dispersión (máx−mín):", round(max(por_g.values()) - min(por_g.values()), 2))
    t = [a.format(G=g) for a in NEUTROS for g in GRUPOS]; r, p = tasa(t, 0)
    res["2. mención neutra de grupo → No Tóxico"] = r
    por_g = {g: float(np.mean([clase(a.format(G=g)) == 0 for a in NEUTROS])) for g in GRUPOS}
    print("  No Tóxico por grupo:", {k: round(v, 2) for k, v in por_g.items()})
    res["3a. amenaza explícita en 8 temas → Amenazas"], _ = tasa([a.format(T=x) for a in AMENAZA for x in TEMAS], 3)
    res["3b. neutro en 8 temas → No Tóxico"], _ = tasa([a.format(T=x) for a in NEUTRO_T for x in TEMAS], 0)
    base_ok = np.array([clase(t) == 0 for t in EMOJI_BASE])
    res["4. emoji inocuo no vuelve tóxico un neutro (sobre los que eran NT)"] = float(np.mean(
        [clase(f"{t} {e}") == 0 for t, ok in zip(EMOJI_BASE, base_ok) if ok for e in EMOJIS if e != "🤡"] or [np.nan]))
    res["5. palabra gatillo en contexto inocuo → No Tóxico"], p = tasa(GATILLO, 0)
    print("\nRESULTADOS (1.0 = sin atajo detectado)")
    for k, v in res.items():
        print(f"  {v:5.2f}  {k}")
    fallos = [g for g, c in zip(GATILLO, p) if c != 0]
    if fallos:
        print("  gatillos que fallan:", fallos)


if __name__ == "__main__":
    main()
