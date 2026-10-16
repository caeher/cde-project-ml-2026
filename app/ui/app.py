# -*- coding: utf-8 -*-
"""Panel Streamlit del prototipo local. Requiere la API en marcha (scripts/arrancar_demo.ps1 levanta las dos):
    uvicorn app.api.main:app --port 8000
    streamlit run app/ui/app.py
"""
import pandas as pd
import requests
import streamlit as st

API = "http://127.0.0.1:8000"
UMBRAL_BAJA_CONFIANZA = 0.55
COLORES = {"No Tóxico": "🟢", "Lenguaje Ofensivo": "🟠", "Discurso de Odio": "🔴", "Amenazas/Violencia": "⛔"}
EJEMPLOS = {
    "Escribir mi propio texto": "",
    "Saludo afectivo con grosería (jerga salvadoreña)": "Qué onda cerote, hace rato no te veía, vení a echarnos unas pupusas",
    "Crítica política sin insulto": "Este gobierno gasta mal el presupuesto y no rinde cuentas, así no se arregla nada",
    "Insulto directo": "Sos un imbécil, no sabés ni de lo que hablás",
    "Discurso de odio (generalización contra un grupo)": "Esos venezolanos son una plaga, deberían sacarlos a todos del país",
    "Amenaza": "Te voy a buscar y te vas a arrepentir, sabemos dónde vivís",
}

st.set_page_config(page_title="Toxicidad — El Salvador", layout="wide")
st.title("Detección de toxicidad y discurso de odio")
st.caption("Clasificador de 4 clases para texto de redes sociales de El Salvador. **Apoyo a la moderación: no es un veredicto.** "
           "Toda decisión que afecte a una persona requiere revisión humana.")

try:
    salud = requests.get(f"{API}/salud", timeout=5).json()
    st.sidebar.success(f"API activa · {salud['modelos_cargados']} modelo(s) cargado(s) · {salud['dispositivo']}")
except Exception:
    st.sidebar.error("La API no responde en http://127.0.0.1:8000")
st.sidebar.markdown("### Clases\n- 🟢 **No Tóxico**: sin agresión; incluye groserías afectivas y crítica dura.\n- 🟠 **Lenguaje Ofensivo**: insulto a una persona.\n"
                    "- 🔴 **Discurso de Odio**: ataque a un grupo por su identidad.\n- ⛔ **Amenazas/Violencia**: intención de causar daño.\n\n"
                    "Precedencia si hay varias: Amenazas > Odio > Ofensivo > No Tóxico (guía de anotación v2.0).")

col_in, col_out = st.columns([3, 2])
with col_in:
    ej = st.selectbox("Ejemplo precargado", list(EJEMPLOS))
    texto = st.text_area("Publicación", value=EJEMPLOS[ej], height=160, placeholder="Escribí o pegá el texto...", key=f"t_{ej}")
    ir = st.button("Clasificar", type="primary", disabled=not texto.strip())

with col_out:
    if ir:
        try:
            r = requests.post(f"{API}/predecir", json={"texto": texto}, timeout=60); r.raise_for_status(); d = r.json()
            st.subheader(f"{COLORES[d['clase']]} {d['clase']}")
            st.metric("Confianza", f"{d['confianza']:.0%}")
            if d["confianza"] < UMBRAL_BAJA_CONFIANZA:
                st.warning("Confianza baja: el modelo duda entre clases. Este caso debería ir a revisión humana.")
            if d["label"] > 0 and d["confianza"] >= UMBRAL_BAJA_CONFIANZA:
                st.info("Texto marcado como tóxico: confirmar con una persona antes de cualquier acción.")
            pr = pd.Series(d["probabilidades"]).reindex(list(COLORES)); st.bar_chart(pr)
            st.caption(f"Modelos en el ensamble: {d['n_modelos']}. Las probabilidades están calibradas (temperature scaling).")
        except Exception as e:
            st.error(f"No se pudo consultar la API ({e})")
    else:
        st.info("Elegí un ejemplo o escribí un texto y presioná **Clasificar**.")

with st.expander("Límites del modelo (leer antes de usarlo)"):
    st.markdown("- Entrenado con texto de X (y Facebook en la parte original); etiquetas de consenso de anotadores LLM sin validación humana.\n"
                "- Las groserías afectivas salvadoreñas son difíciles: el contexto importa y el modelo puede fallar.\n"
                "- No evalúa imágenes, sarcasmo complejo ni contexto del hilo.\n- Informe de sesgos: `reports/improvement/fairness.md`.")
