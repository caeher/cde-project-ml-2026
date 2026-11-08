# -*- coding: utf-8 -*-
"""Panel Streamlit del prototipo local. Requiere la API en marcha (scripts/arrancar_demo.ps1 levanta las dos):
    uvicorn app.api.main:app --port 8000
    streamlit run app/ui/app.py
"""
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

def _cargar_catalogo():
    try:
        r = requests.get(f"{API}/modelos", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


catalogo = _cargar_catalogo()
opciones_modelo: list[tuple[str, str]] = []
modelo_default = "xlmr_hf"
if catalogo and catalogo.get("modelos"):
    modelo_default = catalogo.get("default") or modelo_default
    for m in catalogo["modelos"]:
        etiqueta = m.get("etiqueta") or m.get("id")
        if not m.get("disponible_local", True) and m.get("id", "").startswith("v3."):
            etiqueta = f"{etiqueta} (sin pesos locales)"
        opciones_modelo.append((m["id"], etiqueta))
if not opciones_modelo:
    opciones_modelo = [
        ("v3.6.0", "RoBERTuito v3.6.0"),
        ("v3.4.0", "RoBERTuito v3.4.0"),
        ("xlmr_hf", "XLM-R Large (Hugging Face)"),
        ("xlmr_local", "XLM-R Large (local)"),
    ]

if "modelo_id" not in st.session_state:
    ids = [o[0] for o in opciones_modelo]
    st.session_state.modelo_id = modelo_default if modelo_default in ids else ids[0]

idx_def = next((i for i, o in enumerate(opciones_modelo) if o[0] == st.session_state.modelo_id), 0)
st.session_state.modelo_id = st.sidebar.selectbox(
    "Modelo",
    options=[o[0] for o in opciones_modelo],
    format_func=lambda k: next(l for i, l in opciones_modelo if i == k),
    index=idx_def,
    key="modelo_select",
)
modelo_id = st.session_state.modelo_id

try:
    salud = requests.get(f"{API}/salud", params={"modelo_id": modelo_id}, timeout=5).json()
    if salud.get("ok"):
        st.sidebar.success(f"API activa · {salud.get('modelo', modelo_id)} · {salud.get('dispositivo', '?')}")
    else:
        st.sidebar.warning(f"Modelo «{modelo_id}»: {salud.get('error', 'no disponible')}")
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
            r = requests.post(
                f"{API}/predecir",
                json={"texto": texto, "modelo_id": modelo_id},
                timeout=120,
            )
            r.raise_for_status()
            d = r.json()
            st.subheader(f"{COLORES[d['clase']]} {d['clase']}")
            st.metric("Confianza", f"{d['confianza']:.0%}")
            if d["confianza"] < UMBRAL_BAJA_CONFIANZA:
                st.warning("Confianza baja: el modelo duda entre clases. Este caso debería ir a revisión humana.")
            if d["label"] > 0 and d["confianza"] >= UMBRAL_BAJA_CONFIANZA:
                st.info("Texto marcado como tóxico: confirmar con una persona antes de cualquier acción.")
            for clase in COLORES:
                st.caption(f"{clase}: {d['probabilidades'].get(clase, 0.0):.1%}")
                st.progress(float(d["probabilidades"].get(clase, 0.0)))
            st.caption(f"Modelo: {d['modelo']}.")
        except Exception as e:
            st.error(f"No se pudo consultar la API ({e})")
    else:
        st.info("Elegí un ejemplo o escribí un texto y presioná **Clasificar**.")

with st.expander("Límites del modelo (leer antes de usarlo)"):
    st.markdown("- Entrenado con texto de X (y Facebook en la parte original); etiquetas de consenso del equipo (Cristian, Willian y Julio).\n"
                "- Las groserías afectivas salvadoreñas son difíciles: el contexto importa y el modelo puede fallar.\n"
                "- No evalúa imágenes, sarcasmo complejo ni contexto del hilo.\n- Informe de sesgos: `reports/improvement/fairness.md`.")
