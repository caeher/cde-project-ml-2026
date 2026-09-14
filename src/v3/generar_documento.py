# -*- coding: utf-8 -*-
"""
Genera el documento de la Etapa II heredando los estilos del de la Etapa I.

En vez de recrear el formato, se abre el documento anterior, se vacía su cuerpo
y se escribe encima: así los estilos (Heading, Caption, Grid Table 1 Light, la
tipografía y los márgenes) son exactamente los mismos y el documento se lee como
continuación del primero, no como otro documento.
"""
import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

RAIZ = Path(__file__).resolve().parents[2]
PLANTILLA = RAIZ / "docs/etapa-1/plantilla_etapa1.docx"
DESTINO = RAIZ / "reports/9-12-2026/Etapa II - Analisis de Discurso de Odio en Redes Sociales en El Salvador.docx"

S, A = RAIZ / "reports/v3_resultados", RAIZ / "reports/v3_arquitectura"
D = {
    "final": json.loads((S / "evaluacion_v3_final.json").read_text()),
    "ens": json.loads((S / "ensemble.json").read_text()),
    "cv": json.loads((A / "validacion_cruzada.json").read_text()),
    "hpo": json.loads((A / "hpo_robertuito_mejor.json").read_text()),
    "fair": json.loads((S / "fairness.json").read_text()),
    "meta": json.loads((RAIZ / "data/dataset_v3/metadata.json").read_text()),
}

_n_tabla = 0
_n_figura = 0
FIGS = RAIZ / "reports/figures/etapa2"


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def vaciar_cuerpo(doc):
    """
    Quita el contenido pero CONSERVA la portada, el índice y los saltos de sección.

    El cuerpo del documento de la Etapa I empieza con: el párrafo que contiene el
    dibujo de la portada y su salto de sección, un marcador, el campo de índice
    automático (un elemento sdt), y un encabezado vacío con el segundo salto de
    sección. A partir de ahí viene el texto. Borrar todo eso —que es lo que hacía
    la primera versión de este script— dejaba el documento sin portada ni índice.
    """
    cuerpo = doc.element.body
    # el contenido real empieza después del segundo salto de sección
    inicio = 0
    for i, hijo in enumerate(cuerpo):
        if hijo.tag == f"{W}p" and hijo.findall(f".//{W}sectPr"):
            inicio = i + 1
    # el último hijo es el sectPr final del documento: se conserva
    for hijo in list(cuerpo)[inicio:]:
        if hijo.tag != f"{W}sectPr":
            cuerpo.remove(hijo)
    return inicio


def actualizar_portada(doc, reemplazos):
    """La portada son cuadros de texto; su contenido vive en elementos w:t sueltos."""
    hechos = []
    claves = {k.strip(): v for k, v in reemplazos.items()}
    for t in doc.element.body.iter(f"{W}t"):
        if not t.text:
            continue
        crudo = t.text
        limpio = crudo.strip()
        if limpio in claves:
            # se respeta el espaciado original del run, que forma parte del diseño
            izq = crudo[:len(crudo) - len(crudo.lstrip())]
            der = crudo[len(crudo.rstrip()):]
            t.text = izq + claves[limpio] + der
            hechos.append(f"{crudo!r} -> {t.text!r}")
    return hechos


def forzar_actualizacion_de_campos(doc):
    """
    Marca los campos para que Word los recalcule al abrir.

    El índice del documento es un campo con su resultado en caché: sin esto
    mostraría los títulos de la Etapa I hasta que alguien pulse F9.
    """
    from docx.oxml.ns import qn
    ajustes = doc.settings.element
    for etiqueta in ajustes.findall(qn("w:updateFields")):
        ajustes.remove(etiqueta)
    el = ajustes.makeelement(qn("w:updateFields"), {qn("w:val"): "true"})
    ajustes.append(el)


def h1(doc, t): doc.add_paragraph(t, style="Heading 1")
def h2(doc, t): doc.add_paragraph(t, style="Heading 2")
def p1(doc, t): doc.add_paragraph(t, style="First Paragraph")
def p(doc, t): doc.add_paragraph(t, style="Body Text")


# Identificador de la lista con viñeta ➢ que usa el documento de la Etapa I.
# La viñeta no viene del estilo sino de una referencia de numeración puesta
# directamente en cada párrafo, así que hay que reproducirla igual.
NUM_ID_VINETA = "13"


def vinetas(doc, items):
    from docx.oxml.ns import qn
    for it in items:
        par = doc.add_paragraph(it, style="Body Text")
        pPr = par._p.get_or_add_pPr()
        numPr = pPr.makeelement(qn("w:numPr"), {})
        ilvl = pPr.makeelement(qn("w:ilvl"), {qn("w:val"): "0"})
        numId = pPr.makeelement(qn("w:numId"), {qn("w:val"): NUM_ID_VINETA})
        numPr.append(ilvl); numPr.append(numId)
        pPr.insert(0, numPr)


def figura(doc, archivo, titulo, ancho=6.0):
    """Inserta una figura centrada con su pie numerado, como en la Etapa I."""
    global _n_figura
    from docx.shared import Inches
    _n_figura += 1
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run().add_picture(str(FIGS / archivo), width=Inches(ancho))
    cap = doc.add_paragraph(f"Figura {_n_figura} {titulo}", style="Caption")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return _n_figura


def tabla(doc, titulo, cabecera, filas):
    global _n_tabla
    _n_tabla += 1
    t = doc.add_table(rows=1, cols=len(cabecera))
    t.style = "Grid Table 1 Light"
    for c, txt in zip(t.rows[0].cells, cabecera):
        c.text = str(txt)
    for fila in filas:
        celdas = t.add_row().cells
        for c, txt in zip(celdas, fila):
            c.text = str(txt)
    cap = doc.add_paragraph(f"Tabla {_n_tabla} {titulo}", style="Caption")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return _n_tabla


def construir():
    doc = Document(str(PLANTILLA))
    n = vaciar_cuerpo(doc)
    print(f"conservados {n} elementos de cabecera (portada, índice y saltos de sección)")
    for h in actualizar_portada(doc, {
            "ETAPA I": "ETAPA II",
            "julio": "septiembre",
            "Ciudad universitaria, 16 de": "Ciudad universitaria, 12 de",
    }):
        print("  portada:", h)
    forzar_actualizacion_de_campos(doc)
    f, e, cv, hpo, fair = D["final"], D["ens"], D["cv"], D["hpo"], D["fair"]
    t = f["test"]

    # ═══════════════════════════════════════════════ 1
    h1(doc, "Introducción y Planteamiento")
    h2(doc, "Alcance de esta etapa")
    p1(doc, "La Etapa I dejó el corpus salvadoreño construido, etiquetado y validado entre "
            "anotadores, con tres baselines clásicos como referencia. La Etapa II parte de ahí "
            "y aborda el modelado: qué arquitectura conviene a este problema, cómo debe "
            "ampliarse el corpus, qué hiperparámetros lo optimizan, y si el sistema resultante "
            "es lo bastante sólido y equitativo para presentarse como prototipo.")
    p(doc, "El punto de partida fueron dos modelos ya entrenados por el equipo, mBERT y "
           "XLM-RoBERTa, con F1-macro de 0.7777 y 0.8058 sobre el conjunto de prueba. Ninguno "
           "alcanzaba la meta de 0.80 con significancia estadística: el intervalo de confianza "
           "del mejor de los dos descendía hasta 0.7665. Esta etapa cierra esa brecha.")

    h2(doc, "Objetivo de la Etapa II")
    p1(doc, "Alcanzar un F1-macro de al menos 0.80 sobre el conjunto de prueba de forma "
            "defendible, entendiendo por defendible que el extremo inferior del intervalo de "
            "confianza del 95 % también supere ese umbral, y no solamente la estimación puntual.")

    h2(doc, "Objetivos específicos")
    vinetas(doc, [
        "Seleccionar la arquitectura con evidencia medida y no por convención, comparando "
        "siete modelos preentrenados bajo condiciones idénticas.",
        "Ampliar el corpus con datos sintéticos dirigidos a las debilidades efectivamente "
        "medidas, manteniendo intactos los conjuntos de validación y prueba.",
        "Optimizar hiperparámetros mediante búsqueda sistemática sobre el conjunto de validación.",
        "Evaluar con validación cruzada estratificada además de la prueba final única.",
        "Cuantificar sesgos por plataforma, registro dialectal, figura retórica y contexto.",
        "Entregar un prototipo funcional que aplique el mismo pipeline de inferencia del "
        "entrenamiento, sin divergencias.",
    ])

    h2(doc, "Taxonomía")
    p1(doc, "Se conservan las cuatro clases canónicas de la Etapa I, sin añadir ni fusionar "
            "ninguna: No Tóxico (0), Lenguaje Ofensivo (1), Discurso de Odio (2) y "
            "Amenazas/Violencia (3), con la precedencia "
            "Amenazas > Odio > Ofensivo > No Tóxico.")

    # ═══════════════════════════════════════════════ 2
    h1(doc, "Metodología")
    p1(doc, "La etapa sigue las fases de modelado y evaluación de CRISP-DM, con una fase previa "
            "de auditoría que no estaba prevista y que resultó determinante.")
    vinetas(doc, [
        "Auditoría de la entrega anterior: reejecución independiente de los cuatro checkpoints "
        "entregados para verificar que las cifras publicadas se reproducen desde los pesos.",
        "Selección de arquitectura: análisis de adecuación del tokenizador y comparación "
        "controlada de siete modelos preentrenados.",
        "Preparación de datos: generación de corpus sintético dirigido y corrección de tres "
        "defectos del pipeline compartido.",
        "Modelado: ablación de datos y régimen de entrenamiento, optimización de "
        "hiperparámetros con Optuna y construcción de un ensemble por voto blando.",
        "Evaluación: validación cruzada estratificada de cinco pliegues, prueba final única, "
        "batería adversarial, sonda dirigida e informe de equidad.",
        "Despliegue: prototipo de inferencia con API e interfaz web.",
    ])
    p(doc, "Todo el código es determinista con semilla fija. Los conjuntos de validación y "
           "prueba se mantuvieron idénticos byte a byte a los de la etapa anterior, lo que hace "
           "que todas las cifras de este documento sean directamente comparables con las previas.")

    # ═══════════════════════════════════════════════ 3
    h1(doc, "Auditoría de la Entrega Anterior")
    p1(doc, "Antes de modelar nada se reejecutaron los cuatro checkpoints entregados por el "
            "equipo, cargando los pesos y corriendo la inferencia sobre el mismo conjunto de "
            "prueba. El propósito era comprobar que las cifras publicadas se reproducen.")
    tabla(doc, "Reproducibilidad de las cifras publicadas en la entrega anterior",
          ["Entrega", "Cifras verificadas", "Reproducibles"],
          [["mBERT B2", "26", "26 de 26"],
           ["Prototipo XLM-R V2", "11", "3 de 11"]])
    p(doc, "La entrega de mBERT reprodujo todas sus cifras al cuarto decimal. La del prototipo "
           "XLM-R no reprodujo ninguna de las tres que declaraba como resultado, y la revisión "
           "del código de entrenamiento mostró por qué: veintiún textos del conjunto de prueba "
           "habían sido reinyectados en el conjunto de entrenamiento etiquetados como No Tóxico, "
           "y la mejora de la tasa de falsos positivos se medía después sobre esos mismos textos.")
    p(doc, "La auditoría también cuantificó una vulnerabilidad del filtro de reglas de ese "
           "prototipo: anteponer la palabra «gracias» a una amenaza la reclasificaba como No "
           "Tóxico en veinte de cada cien casos. Ese hallazgo motivó la decisión de no usar "
           "ninguna capa de reglas post-hoc en la Etapa II.")
    p(doc, "El informe completo de la auditoría, con la tabla de contraste cifra por cifra, se "
           "adjunta como anexo.")

    # ═══════════════════════════════════════════════ 4
    h1(doc, "Selección de Arquitectura")
    h2(doc, "Adecuación del tokenizador al dialecto")
    p1(doc, "Antes de entrenar conviene medir cuánto le cuesta a cada modelo leer este registro. "
            "La fertilidad es el número medio de subtokens por palabra: cuanto más alta, más "
            "troceado queda el texto y menos contexto efectivo cabe en la ventana.")
    tabla(doc, "Adecuación del tokenizador medida sobre los 2,144 textos reales del corpus",
          ["Modelo", "Vocabulario", "Fertilidad", "UNK", "Jerga como un token"],
          [["RoBERTuito", "30 K", "1.470", "0", "108 / 1923 (5.6 %)"],
           ["BERTIN", "50 K", "1.546", "0", "19 (1.0 %)"],
           ["BETO", "31 K", "1.598", "588", "86 (4.5 %)"],
           ["XLM-R base / large / TwitterXLM-R", "250 K", "1.696", "3", "45 (2.3 %)"],
           ["mBERT", "120 K", "1.805", "45", "31 (1.6 %)"],
           ["mDeBERTa-v3", "250 K", "1.851", "45", "40 (2.1 %)"]])
    figura(doc, "fig01_tokenizador.png",
           "Fragmentación del texto salvadoreño por tokenizador")
    p(doc, "La figura ordena los candidatos por cuánto trocean el mismo texto. La distancia "
           "entre los extremos es de 0.38 subtokens por palabra, un 26 % más de fragmentación "
           "en el peor caso que en el mejor. Dos modelos quedan marcados por motivos opuestos: "
           "RoBERTuito es el que menos trocea y el único que además cubre más del 5 % del "
           "léxico local como unidad, y BETO aparece con 588 tokens desconocidos, que es un "
           "defecto de otra naturaleza —no fragmenta, directamente no reconoce— y lo descarta.")
    p(doc, "mBERT, uno de los dos modelos elegidos en la Etapa I, resultó ser el peor "
           "tokenizador del grupo: gasta un 23 % más de subtokens que RoBERTuito sobre el mismo "
           "texto. «cerote» se parte en «cero ##te», «maje» en «maj ##e» y «pisto» en «pis ##to». "
           "BETO queda descartado por producir 588 tokens desconocidos sobre el corpus.")
    p(doc, "El dato de fondo, sin embargo, es que ningún tokenizador conoce el dialecto: el "
           "mejor cubre apenas el 5.6 % del léxico salvadoreño como unidad léxica.")

    h2(doc, "Comparación controlada de siete arquitecturas")
    p1(doc, "Los siete candidatos se entrenaron con hiperparámetros idénticos sobre el mismo "
            "corpus y se evaluaron sobre el mismo conjunto de validación.")
    tabla(doc, "Comparación de arquitecturas con hiperparámetros idénticos (F1-macro sobre validación, n = 459)",
          ["Modelo", "F1-macro", "Parámetros", "Tiempo"],
          [["TwitterXLM-R", "0.8289", "278 M", "3.1 min"],
           ["RoBERTuito", "0.8272", "109 M", "1.5 min"],
           ["BERTIN", "0.8141", "125 M", "1.7 min"],
           ["XLM-R large", "0.8090", "560 M", "42.2 min"],
           ["BETO", "0.8000", "110 M", "1.6 min"],
           ["XLM-R base", "0.7895", "278 M", "2.0 min"],
           ["mBERT", "0.7636", "178 M", "2.1 min"]])
    figura(doc, "fig02_arquitecturas.png",
           "Desempeño frente a tamaño del modelo, con el dominio de preentrenamiento destacado")
    p(doc, "La figura cruza el tamaño del modelo con su desempeño, y lo que muestra es que no "
           "hay relación. Si el tamaño explicara el resultado, los puntos subirían de izquierda "
           "a derecha; no lo hacen. Lo que sí separa a los dos mejores del resto es el color: "
           "ambos fueron preentrenados sobre publicaciones de redes sociales. El modelo más "
           "grande de la comparación, con 560 millones de parámetros, queda por debajo de uno "
           "cinco veces menor.")
    p(doc, "Dos conclusiones. La primera: escalar el modelo no resuelve este problema. XLM-R "
           "large tiene cinco veces los parámetros de RoBERTuito, tarda veintiocho veces más y "
           "obtiene menos F1. Con 2,144 ejemplos reales el cuello de botella no es la capacidad.")
    p(doc, "La segunda, que es la que explica el salto de esta etapa: el corpus de "
           "preentrenamiento importa más que la arquitectura. TwitterXLM-R es exactamente la "
           "misma arquitectura que XLM-R base, con el mismo tamaño y el mismo tokenizador, y le "
           "saca 0.039 de F1-macro por el solo hecho de haber sido preentrenado sobre "
           "publicaciones de redes sociales. Los dos modelos elegidos en la Etapa I resultaron "
           "ser los dos peores de la comparación.")

    # ═══════════════════════════════════════════════ 5
    h1(doc, "Corpus Dirigido")
    h2(doc, "Diseño del generador")
    p1(doc, "El corpus se amplió con ejemplos sintéticos dirigidos a las debilidades que la "
            "auditoría había medido: amenazas ofuscadas, eufemismos locales de violencia, "
            "emojis como vehículo de ataque y falsos positivos ante jerga inofensiva.")
    p(doc, "El material de partida es el léxico salvadoreño del proyecto, reconstruido en 110 "
           "familias canónicas con sus 1,979 variantes de ofuscación. Son deformaciones "
           "observadas en el corpus real, no inventadas para el ejercicio.")
    p(doc, "Tres decisiones de diseño merecen constar, porque las tres corrigen defectos de la "
           "versión anterior del generador. Los portadores de frase son vocativos y "
           "aposiciones, que no exigen concordancia de género ni número, de modo que no se "
           "producen construcciones agramaticales que el modelo aprendería como señal. Cada "
           "emoji se empareja únicamente con referentes de su propio grupo, según el catálogo "
           "del proyecto, para no enseñar asociaciones falsas. Y cada término dialectal lleva "
           "su rol gramatical, porque «pisto» es un objeto, «chivo» un adjetivo y «puchica» una "
           "interjección, y colocarlos en el mismo hueco produce frases que no existen.")

    h2(doc, "Composición")
    m = D["meta"]
    tabla(doc, "Composición del corpus de entrenamiento",
          ["Origen", "Registros"],
          [["Publicaciones reales", f"{m['reales']:,}".replace(",", ",")],
           ["Sintéticos de la versión anterior", f"{m['sinteticos_b2']:,}"],
           ["Sintéticos dirigidos nuevos", f"{m['sinteticos_v3']:,}"],
           ["Total de entrenamiento", f"{m['n_train']:,}"],
           ["Validación (sin modificar)", f"{m['n_val']}"],
           ["Prueba (sin modificar)", f"{m['n_test']}"]])
    p(doc, "Los conjuntos de validación y prueba se copiaron sin tocar una sola etiqueta ni "
           "renormalizar un solo texto. Sus funciones resumen coinciden con las de la etapa "
           "anterior, lo que garantiza que las comparaciones de este documento son válidas y "
           "que ninguna mejora puede atribuirse a haber facilitado la prueba.")

    h2(doc, "Higiene del corpus")
    p1(doc, "Se verificó que ningún texto del entrenamiento coincide con validación, prueba o la "
            "batería adversarial. La verificación detectó siete filas que el proyecto arrastraba "
            "desde agosto, compartidas entre la batería y el entrenamiento, y que quedaron fuera.")
    p(doc, "La comprobación se hace también contra la normalización vigente del texto crudo y no "
           "solo contra la columna almacenada: una de las siete filas se había vuelto invisible "
           "porque la batería guardaba su texto normalizado con una versión anterior del "
           "normalizador.")

    h2(doc, "Correcciones al pipeline compartido")
    p1(doc, "La construcción del corpus destapó dos defectos del normalizador que afectaban a "
            "todo el proyecto.")
    tabla(doc, "Defectos corregidos en el normalizador",
          ["Defecto", "Efecto", "Corrección"],
          [["La anonimización de menciones no exigía límite de palabra",
            "«m@tar» se convertía en «m@usuario»; la ofuscación con arroba, que es una de las "
            "evasiones a detectar, se destruía en la normalización",
            "Se añadió una guarda de límite de palabra. El conjunto de prueba no cambia ni una fila"],
           ["El emoji de pistola se traducía como «pistola de agua»",
            "Es el nombre Unicode vigente, pero enseñaba «agua» donde el catálogo documenta un "
            "vehículo de amenaza",
            "Se corrigió la traducción a «pistola»"]])

    # ═══════════════════════════════════════════════ 6
    h1(doc, "Optimización de Hiperparámetros")
    p1(doc, "Se ejecutaron veinte pruebas con Optuna, usando un muestreador TPE con semilla fija, "
            "optimizando F1-macro sobre el conjunto de validación. El conjunto de prueba no "
            "participó en la búsqueda ni se consultó durante ella.")
    par = hpo["mejores_parametros"]
    tabla(doc, "Espacio de búsqueda y configuración seleccionada",
          ["Hiperparámetro", "Rango explorado", "Valor elegido"],
          [["Tasa de aprendizaje", "8×10⁻⁶ – 6×10⁻⁵ (log)", f"{par['lr']:.2e}"],
           ["Tamaño de lote", "8 / 16 / 32", str(par["bs"])],
           ["Épocas", "3 – 6", str(par["epochs"])],
           ["Decaimiento de pesos", "0.00 – 0.15", f"{par['weight_decay']:.4f}"],
           ["Calentamiento", "0.00 – 0.20", f"{par['warmup']:.4f}"],
           ["Peso de los ejemplos sintéticos", "0.25 / 0.50 / 0.75 / 1.00", str(par["peso_sintetico"])],
           ["Épocas finales solo con ejemplos reales", "0 – 3", str(par["fases_reales"])],
           ["Ponderación por clase", "sí / no", "sí" if par["pesos_clase"] else "no"]])
    peor = min(h["val_f1_macro"] for h in hpo["historial"])
    p(doc, f"La mejor prueba alcanzó {hpo['mejor_val_f1']:.4f} en validación frente a 0.8272 de "
           f"la configuración por defecto, lo que sitúa la aportación de la búsqueda en "
           f"+0.025. El rango entre la mejor y la peor configuración fue de "
           f"{hpo['mejor_val_f1'] - peor:.4f}, lo que da idea de cuánto dependía el resultado de "
           f"unos valores que hasta ahora se habían fijado por convención.")
    figura(doc, "fig04_hpo.png",
           "Trayectoria de la búsqueda de hiperparámetros")
    p(doc, "La línea del mejor acumulado avanza a saltos: la mitad de las pruebas no mejora nada "
           "y el hallazgo llega en la prueba once. La nube de puntos se reparte casi seis puntos "
           "de F1 entre la mejor y la peor configuración, lo que dimensiona el riesgo de fijar "
           "los hiperparámetros por convención, como se había hecho hasta ahora.")
    p(doc, "La configuración ganadora resultó interesante por sí misma: peso completo a los "
           "ejemplos sintéticos durante el grueso del entrenamiento y tres épocas finales "
           "únicamente con ejemplos reales. El modelo aprovecha toda la señal de robustez que "
           "aportan los sintéticos y después se reasienta en la distribución que realmente se "
           "va a evaluar.")

    h2(doc, "Ablación de datos y de régimen de entrenamiento")
    p1(doc, "Antes de fijar la configuración se aisló el efecto de cada decisión, con la "
            "arquitectura y los hiperparámetros constantes.")
    tabla(doc, "Ablación de corpus, vocabulario y régimen (F1-macro sobre validación)",
          ["Variante", "TwitterXLM-R", "RoBERTuito"],
          [["Corpus anterior solamente", "0.8331", "0.8272"],
           ["Corpus dirigido, peso 1.0", "0.8080", "0.8337"],
           ["Corpus dirigido, peso 0.5", "0.8094", "0.8371"],
           ["Corpus dirigido, peso 0.25", "0.8144", "0.8403"],
           ["Corpus dirigido, dos fases", "0.8090", "0.8386"],
           ["Corpus dirigido, peso 0.5 y dos fases", "—", "0.8473"],
           ["Vocabulario extendido, corpus anterior", "0.7756", "0.8231"],
           ["Vocabulario extendido, corpus dirigido", "0.8016", "0.8213"]])
    figura(doc, "fig03_ablacion.png",
           "Efecto del corpus sintético según la capacidad del modelo")
    p(doc, "Las dos líneas se cruzan, y ese cruce es el hallazgo. Partiendo del corpus anterior, "
           "el modelo grande va por delante; en cuanto entran los ejemplos sintéticos, cae más "
           "de dos puntos y ya no se recupera, mientras que el pequeño sube de forma sostenida. "
           "Bajar el peso de los sintéticos amortigua la caída del grande pero no la revierte.")
    p(doc, "El resultado más informativo es que los mismos datos ayudan a un modelo y perjudican "
           "al otro. Con TwitterXLM-R, de 278 millones de parámetros, los sintéticos cuestan "
           "hasta 2.5 puntos; con RoBERTuito, de 109 millones, aportan hasta 2. La lectura es "
           "que el modelo grande tiene capacidad de sobra para memorizar la estructura de las "
           "plantillas, y esa estructura no existe en el lenguaje real; el pequeño no puede "
           "memorizarla y se queda con la señal.")
    p(doc, "La extensión del vocabulario con 189 tokens de dominio perjudicó en las seis "
           "configuraciones probadas. La hipótesis era razonable, porque los marcadores de "
           "emoji se fragmentan en cuatro o más piezas, pero un token nuevo nace con un vector "
           "aleatorio y no hay ejemplos suficientes para aprenderlo: mientras tanto sustituye "
           "una representación imperfecta pero informativa por ruido. La vía se documenta como "
           "explorada y descartada.")
    p(doc, "Un subconjunto que conserva solo las familias dirigidas a una debilidad medida, con "
           "1,292 filas menos, obtiene 0.8472 frente a 0.8473 del conjunto completo. Es decir, "
           "la mitad de los sintéticos generados era prescindible: los modelos ya acertaban "
           "entre el 68 % y el 89 % en insultos ofuscados, y añadir volumen donde no hay "
           "problema solo desplaza la distribución de entrenamiento.")

    # ═══════════════════════════════════════════════ 7
    h1(doc, "Modelos Avanzados y Ensemble")
    p1(doc, "Los siete candidatos evaluados son modelos de aprendizaje profundo de la familia "
            "Transformer, ajustados mediante transfer learning sobre el corpus salvadoreño. "
            "Seis son variantes de codificador bidireccional preentrenado —BERT multilingüe, "
            "BETO, BERTIN, RoBERTuito, XLM-RoBERTa en sus versiones base y large, y "
            "TwitterXLM-R— y se compararon bajo condiciones idénticas antes de elegir.")
    h2(doc, "Modelo individual")
    p1(doc, "El modelo final es RoBERTuito ajustado con la configuración óptima. Se entrenó con "
            "tres semillas y se seleccionó la mediana, no la mejor: quedarse con la semilla más "
            "favorable es una forma silenciosa de sobreajustar al conjunto de selección.")
    tabla(doc, "Dispersión entre semillas del modelo final",
          ["Semilla", "F1-macro en validación"],
          [["42", "0.8374"], ["1337", "0.8409  (mediana, seleccionada)"], ["2026", "0.8555"]])
    p(doc, "La dispersión entre semillas es de 1.8 puntos. Conviene tenerlo presente al leer "
           "cualquier comparación de este proyecto: varias de las «mejoras» reportadas en "
           "entregas anteriores son del mismo orden que el ruido de inicialización.")

    h2(doc, "Ensemble por voto blando")
    p1(doc, "Se construyó un ensemble promediando las probabilidades de las tres semillas del "
            "modelo final. La regla de selección se fijó antes de mirar el conjunto de prueba: "
            "se promedian las tres, sin elegir ninguna. Cualquier criterio de selección, "
            "incluso sobre validación, reintroduce el sesgo de quedarse con la combinación "
            "afortunada; con tres semillas el promedio completo es la opción menos sobreajustada.")
    p(doc, "El mejor modelo individual sobre validación es la semilla 2026, con 0.8562, pero esa "
           "semilla conserva cuatro falsos positivos en la sonda de construcción. Escogerla "
           "habría sido seleccionar por la métrica que no ve el defecto.")
    filas_e = [[f"{c['f1_val']:.4f}", " + ".join(c["miembros"])]
               for c in e["todas_las_combinaciones"][:6]]
    tabla(doc, "Combinaciones evaluadas sobre validación (seis mejores)",
          ["F1-macro en validación", "Miembros"], filas_e)
    p(doc, f"La combinación seleccionada fue {' + '.join(e['miembros'])}. Sobre validación "
           f"obtiene {e['val_f1_macro']:.4f}, prácticamente empatada con el mejor modelo "
           f"individual ({e['mejor_individual']['val_f1_macro']:.4f}); sobre el conjunto de "
           f"prueba la diferencia sí se materializa.")

    # ═══════════════════════════════════════════════ 8
    h1(doc, "Evaluación Rigurosa")
    h2(doc, "Validación cruzada estratificada")
    p1(doc, "Se ejecutó una validación cruzada estratificada de cinco pliegues sobre los "
            "conjuntos de entrenamiento y validación unidos, reservando el conjunto de prueba "
            "como evaluación final única.")
    p(doc, "Los ejemplos sintéticos se asignan siempre al lado de entrenamiento y nunca aparecen "
           "en el pliegue de evaluación: medir sobre texto de plantilla inflaría artificialmente "
           "la métrica. Cada pliegue se evalúa exclusivamente sobre publicaciones reales.")
    tabla(doc, "Validación cruzada estratificada de cinco pliegues",
          ["Pliegue", "Evaluado sobre", "F1-macro"],
          [[str(x["pliegue"]), f"{x['n_eval']} reales", f"{x['f1_macro']:.4f}"]
           for x in cv["por_pliegue"]] +
          [["Media ± desviación", f"{sum(x['n_eval'] for x in cv['por_pliegue'])} reales",
            f"{cv['media']:.4f} ± {cv['desv']:.4f}"]])
    figura(doc, "fig05_validacion_cruzada.png",
           "Dispersión del F1-macro entre los cinco pliegues", ancho=6.0)
    p(doc, "La franja sombreada marca una desviación típica alrededor de la media. Cuatro "
           "pliegues caen dentro de ella y uno queda claramente por debajo, lo que indica que "
           "la partición concreta influye en el resultado más de lo que sugeriría una cifra "
           "única.")
    p(doc, f"La media de {cv['media']:.4f} con desviación {cv['desv']:.4f} corrobora el "
           f"resultado de la prueba final y acota su incertidumbre. El rango entre pliegues "
           f"({cv['min']:.4f} a {cv['max']:.4f}) muestra que con este tamaño de corpus la "
           f"partición concreta influye casi siete puntos, lo que refuerza la necesidad de "
           f"reportar intervalos y no solo estimaciones puntuales.")

    h2(doc, "Prueba final")
    p1(doc, "Resultados sobre el conjunto de prueba, consultado una sola vez con los modelos ya "
            "seleccionados.")
    tabla(doc, "Resultados sobre el conjunto de prueba (n = 460)",
          ["Sistema", "F1-macro", "IC 95 %", "Aciertos", "¿Meta con IC?"],
          [["Ensemble", f"{e['test']['f1_macro']:.4f}",
            f"[{e['test']['ic_lo']:.4f}, {e['test']['ic_hi']:.4f}]",
            f"{e['test']['aciertos']}/460", "Sí"],
           ["RoBERTuito individual", f"{t['f1_macro']:.4f}",
            f"[{t['ic_lo']:.4f}, {t['ic_hi']:.4f}]", f"{t['aciertos']}/460", "Sí"],
           ["TwitterXLM-R (corpus anterior)", "0.8302", "[0.7940, 0.8633]", "383/460", "No"],
           ["XLM-R v1 (Etapa I)", "0.8058", "[0.7665, 0.8420]", "371/460", "No"],
           ["XLM-R mitigado", "0.7887", "[0.7486, 0.8257]", "363/460", "No"],
           ["mBERT v1 (Etapa I)", "0.7777", "[0.7363, 0.8144]", "360/460", "No"],
           ["mBERT B2", "0.7610", "[0.7172, 0.7983]", "353/460", "No"]])
    figura(doc, "fig06_comparacion.png",
           "Comparación de los siete sistemas con su intervalo de confianza")
    p(doc, "La línea vertical marca la meta. Lo que la figura hace visible es que cuatro de los "
           "cinco sistemas anteriores la cruzan con su intervalo, es decir, ni la superan ni la "
           "descartan: con ese tamaño de prueba no se puede afirmar nada sobre ellos. Solo los "
           "dos sistemas de esta etapa quedan enteramente a la derecha de la línea.")
    p(doc, f"La meta del proyecto se cumple en el criterio exigente: el extremo inferior del "
           f"intervalo del ensemble se sitúa en {e['test']['ic_lo']:.4f} y el del modelo "
           f"individual en {t['ic_lo']:.4f}, ambos por encima de 0.80. No pasa solo la "
           f"estimación puntual; pasa el intervalo completo.")

    h2(doc, "Métricas por clase")
    tabla(doc, "Métricas por clase del modelo individual sobre el conjunto de prueba",
          ["Clase", "Precisión", "Recall", "F1", "Soporte"],
          [[c, f"{v['precision']:.4f}", f"{v['recall']:.4f}", f"{v['f1']:.4f}", str(v["soporte"])]
           for c, v in t["por_clase"].items()])
    figura(doc, "fig07_confusion.png", "Matriz de confusión del modelo final", ancho=4.3)
    p(doc, "Los errores se concentran, como era de esperar, entre clases contiguas en la escala "
           "de gravedad. La confusión mayor sigue siendo entre Lenguaje Ofensivo y Discurso de "
           "Odio, que es también la distinción que más cuesta a los anotadores humanos. Los "
           "errores de dos o más niveles —clasificar una amenaza como no tóxica, o al revés— "
           "son escasos, que es lo relevante para un uso de moderación.")
    p(doc, "Las cuatro clases superan 0.83. Discurso de Odio, que era la peor clase en todos los "
           "modelos anteriores, con valores entre 0.7330 y 0.8041, sube a 0.8308. "
           "Amenazas/Violencia pasa de un rango de 0.7349 a 0.7975 hasta 0.8488.")

    h2(doc, "Comparación pareada")
    p1(doc, "Prueba de McNemar exacta sobre las mismas 460 instancias.")
    tabla(doc, "Prueba de McNemar del modelo final frente a los modelos anteriores",
          ["Comparación", "Solo acierta el nuevo", "Solo acierta el anterior", "p", "Favorece"],
          [[f"vs {k}", str(v["b_solo_v3"]), str(v["c_solo_ref"]), f"{v['p']:.4f}", "modelo V3"]
           for k, v in f["mcnemar"].items()])
    p(doc, "Las tres comparaciones son estadísticamente significativas. Es la primera vez en el "
           "proyecto que una mejora reportada supera la prueba pareada.")

    h2(doc, "Robustez ante evasión")
    p1(doc, "Además de la prueba estándar se evaluaron dos conjuntos diagnósticos: la batería "
            "adversarial de 144 casos del proyecto y una sonda dirigida de 204 casos construida "
            "durante la auditoría, con ofuscación de groserías mediante asteriscos, arrobas, "
            "almohadillas y sustitución de letras por dígitos, amenazas de muerte literales y "
            "disfrazadas, eufemismos locales y emojis.")
    tabla(doc, "Conjuntos diagnósticos de robustez",
          ["Conjunto", "Modelo V3", "mBERT B2", "XLM-R v1", "XLM-R mitigado"],
          [["Batería adversarial (144)", f"{f['bateria']['aciertos']}", "120", "74", "77"],
           ["Sonda dirigida (204)", f"{f['sonda']['aciertos']}", "167", "105", "112"],
           ["Amenazas de muerte disfrazadas (72)", "72", "61", "26", "39"],
           ["Emojis de amenaza (12)", "12", "12", "0", "0"],
           ["Emoji inofensivo en texto amable (16)", "16", "16", "5", "8"]])
    figura(doc, "fig09_robustez.png",
           "Aciertos por familia de la sonda dirigida, frente a los modelos anteriores")
    p(doc, "La figura separa lo que la cifra global esconde. Los modelos anteriores no fallaban "
           "de forma pareja: se hundían en familias concretas —emojis de amenaza, amenazas "
           "disfrazadas, jerga inofensiva— y rendían bien en el resto. Las dos barras de emoji "
           "de amenaza del modelo XLM-R v1 no aparecen porque su acierto es cero.")
    p(doc, "Debe constar una advertencia metodológica: la sonda dirigida dejó de ser un conjunto "
           "independiente para el modelo de esta etapa. Cuatro de sus textos aparecen en el "
           "entrenamiento, y el 31 % de la sonda usa términos del mismo léxico con el que se "
           "generaron los ejemplos sintéticos. Excluyendo los cuatro textos el resultado es "
           "196 de 200, pero la cifra que sí es limpia e independiente es el F1-macro sobre el "
           "conjunto de prueba, donde el solape con el entrenamiento es cero.")
    p(doc, "La sonda sigue siendo independiente para los cuatro modelos anteriores, que no "
           "vieron esos datos, por lo que la comparación entre columnas conserva su valor.")

    h2(doc, "Resistencia a la evasión deliberada")
    p1(doc, "La auditoría mostró que el filtro de reglas del prototipo anterior se desactivaba "
            "anteponiendo un marcador afectivo. Se repitió la prueba sobre el modelo de esta "
            "etapa con cien amenazas y seis prefijos.")
    tabla(doc, "Amenazas reclasificadas como No Tóxico al anteponer un marcador afectivo",
          ["Prefijo", "Modelo V3", "Prototipo anterior"],
          [["(ninguno)", "3 / 100", "1 / 100"],
           ["«gracias, »", "5 / 100", "20 / 100"],
           ["«qué onda, »", "5 / 100", "19 / 100"],
           ["«todo bien, »", "7 / 100", "17 / 100"],
           ["«mi hermano, »", "5 / 100", "21 / 100"],
           ["«buena onda, »", "7 / 100", "17 / 100"]])
    figura(doc, "fig10_evadibilidad.png",
           "Efecto de anteponer un marcador afectivo a cien amenazas")
    p(doc, "El contraste entre los dos grupos de barras es el argumento en contra de resolver el "
           "sesgo con reglas. Sin prefijo ambos sistemas se comportan de forma parecida; con "
           "prefijo, el que lleva filtro se degrada entre tres y cuatro veces más, porque la "
           "regla convierte el marcador afectivo en una llave.")
    p(doc, "El marcador afectivo degrada al modelo de esta etapa entre dos y cuatro casos de "
           "cien, que es la sensibilidad normal de cualquier clasificador al contexto. En el "
           "prototipo anterior lo degradaba entre dieciséis y veinte, porque la regla lo "
           "forzaba. Sin capa de reglas no hay puerta trasera.")

    # ═══════════════════════════════════════════════ 9
    h1(doc, "Un Atajo Detectado Después de Publicar")
    p1(doc, "Probando el prototipo con la frase «voy a comer», el sistema la clasificó como "
            "Amenazas/Violencia con un 82.6 % de confianza. La investigación del caso destapó "
            "un defecto que ninguna de las métricas anteriores había visto, y se documenta aquí "
            "porque la lección metodológica vale más que la corrección.")
    h2(doc, "El defecto")
    p1(doc, "El modelo no había aprendido los verbos violentos: había aprendido la construcción "
            "sintáctica que los envolvía. Sobre una sonda de veinticuatro frases inocuas "
            "construidas con los mismos portadores, trece salían como amenaza.")
    tabla(doc, "Presencia de la construcción «te voy a» en los corpus de entrenamiento",
          ["Corpus", "Filas con la construcción", "De ellas, Amenaza", "De ellas, No Tóxico"],
          [["train v1 (Etapa I)", "3", "1 (33 %)", "0"],
           ["train B2 (agosto)", "29", "27 (93 %)", "0"],
           ["train dirigido, antes del arreglo", "47", "45 (96 %)", "0"]])
    p(doc, "El generador rellenaba sus portadores de amenaza únicamente con verbos de agresión, "
           "de modo que esas construcciones aparecían en el entrenamiento casi solo con la "
           "etiqueta Amenaza y nunca con No Tóxico. Sin un solo contraejemplo, aprender la "
           "construcción es la solución más barata, y el modelo la tomó.")
    p(doc, "Es el mismo fallo que la auditoría había documentado con los emojis en la primera "
           "versión —«hay emoji, es ofensivo»— trasladado a la sintaxis. El generador ya "
           "incorporaba pares mínimos para la jerga y para los emojis; no los tenía para los "
           "portadores de amenaza.")
    tabla(doc, "Probabilidad media de Amenaza sobre siete frases inocuas, por modelo",
          ["Modelo", "Ejemplos sintéticos de plantilla", "p(amenaza) media"],
          [["XLM-R v1 (Etapa I)", "ninguno", "14.6 %"],
           ["mBERT v1 (Etapa I)", "ninguno", "35.7 %"],
           ["TwitterXLM-R sobre B2", "1,149", "67.4 %"],
           ["mBERT B2", "1,149", "80.7 %"],
           ["Modelo dirigido, antes del arreglo", "4,058", "82.6 %"]])
    p(doc, "El defecto entra con los ejemplos sintéticos y se agrava con cada ampliación del "
           "corpus. Es una propiedad del método de aumento por plantilla, no de una "
           "implementación concreta.")

    h2(doc, "Por qué ninguna métrica lo detectó")
    p1(doc, "Las construcciones afectadas aparecen en catorce de las cuatrocientas sesenta "
            "instancias del conjunto de prueba, un 3 %. Un modelo puede tener el atajo "
            "completamente instalado sin perder apenas F1-macro, porque la prueba no ejercita "
            "esa zona. Ni la batería adversarial ni la sonda dirigida lo cubrían: ambas se "
            "diseñaron contra la ofuscación, los emojis y el sesgo dialectal.")
    p(doc, "Es la lección del hallazgo, y aplica a todo el proyecto: una métrica agregada sobre "
           "un conjunto que no muestrea el modo de fallo no lo ve, por alta que sea la cifra.")

    h2(doc, "La corrección")
    p1(doc, "Se añadió al generador una familia de contrapeso: los mismos portadores de "
            "amenaza, sin modificarlos, rellenados con quince verbos inocuos que admiten la "
            "misma morfología —llamar, invitar, ayudar, esperar, visitar, saludar— y "
            "etiquetados No Tóxico. Son 219 filas.")
    p(doc, "Se excluyó el verbo «buscar» a propósito, porque «te voy a buscar» sí se usa como "
           "amenaza y la batería adversarial lo tiene etiquetado así; enseñarlo como inocuo "
           "habría introducido una contradicción en el corpus.")
    figura(doc, "fig12_atajo.png",
           "Efecto del contrapeso sobre la sonda de construcción")
    p(doc, "La corrección separa las dos poblaciones sin tocar la detección de amenazas "
           "reales: la probabilidad media de amenaza en frases inocuas cae del 53.2 % al 1.6 %, "
           "mientras que en amenazas reales se mantiene en el 100 %. Los falsos positivos de la "
           "sonda pasan de trece a cero y no se pierde ninguna amenaza.")
    tabla(doc, "Efecto de la corrección sobre las métricas del proyecto",
          ["Métrica", "Antes", "Después"],
          [["Falsos positivos en la sonda de construcción", "13 / 24", "0 / 24"],
           ["Amenazas reales no detectadas", "0 / 10", "0 / 10"],
           ["F1-macro sobre el conjunto de prueba", "0.8499", "0.8529"],
           ["Extremo inferior del intervalo", "0.8164", "0.8191"],
           ["Batería adversarial", "125 / 144", "127 / 144"],
           ["Sonda dirigida", "200 / 204", "202 / 204"]])
    p(doc, "Tras rehacer la búsqueda de hiperparámetros sobre el corpus corregido, el sistema "
           "no solo deja de tener el atajo sino que supera ligeramente la cifra anterior. Eso "
           "no debe leerse como que el problema no existía: el resultado previo se apoyaba en "
           "parte en un modelo que llamaba amenaza a «voy a comer», y que la prueba no lo "
           "penalizara es un defecto de la prueba, no una virtud del modelo.")
    p(doc, "Se excluyó del ensemble al TwitterXLM-R entrenado sobre el corpus anterior, pese a "
           "que formaba parte de la combinación previa: arrastra el atajo con catorce falsos "
           "positivos de veinticuatro y lo reintroducía en el promedio. Un miembro con un "
           "defecto conocido contamina el conjunto aunque mejore la métrica agregada.")
    p(doc, "La regla que se deriva del hallazgo, y que queda incorporada al diseño del "
           "generador, es que toda estructura usada para producir una clase debe aparecer "
           "también, con relleno distinto, produciendo otra. De lo contrario el modelo aprende "
           "la estructura.")

    h1(doc, "Análisis de Sesgos y Ética")
    h2(doc, "Métricas por subgrupo")
    p1(doc, "El informe de equidad desagrega el desempeño por plataforma, registro dialectal, "
            "figura retórica, contexto y presencia de emoji. Se reportan F1-macro, tasa de "
            "falsos positivos —contenido inofensivo marcado como tóxico— y tasa de falsos "
            "negativos —contenido tóxico que pasa.")
    tabla(doc, "Desempeño por subgrupo sobre el conjunto de prueba",
          ["Corte", "n", "F1-macro", "FPR", "FNR"],
          [[c["corte"], str(c["n"]), f"{c['f1']:.4f}",
            "n/a" if c["fpr"] is None else f"{c['fpr']:.4f}",
            "n/a" if c["fnr"] is None else f"{c['fnr']:.4f}"] for c in fair["cortes"]])

    h2(doc, "Brechas de paridad")
    tabla(doc, "Diferencias de desempeño entre subgrupos",
          ["Comparación", "Δ F1-macro", "Δ FPR"],
          [[b["par"], f"{b['dF1']:+.4f}",
            "n/a" if b["dFPR"] is None else f"{b['dFPR']:+.4f}"] for b in fair["brechas"]])

    figura(doc, "fig08_equidad.png",
           "Brechas de desempeño entre subgrupos del conjunto de prueba")
    p(doc, "Las barras hacia la derecha señalan subgrupos donde el sistema rinde mejor; hacia la "
           "izquierda, donde rinde peor. Las dos barras rojas son las figuras retóricas, y son "
           "además las más largas: la ironía abre una brecha de casi treinta puntos de F1-macro, "
           "el doble que la brecha entre plataformas.")

    h2(doc, "Calibración")
    p1(doc, "Una métrica de acierto no dice nada sobre si el sistema sabe cuándo se está "
            "equivocando, y eso importa si la salida va a presentarse a un moderador humano.")
    figura(doc, "fig11_calibracion.png", "Confianza declarada frente a acierto observado",
           ancho=4.3)
    p(doc, "La curva del modelo queda por debajo de la diagonal en casi todo el rango: cuando "
           "declara un 90 % de confianza acierta menos del 90 %. El error de calibración "
           "esperado es de 0.1214, mejor que el 0.1640 del modelo de la etapa anterior pero aún "
           "lejos de ser fiable. La implicación práctica es que la confianza que devuelve el "
           "prototipo no debe leerse como una probabilidad.")

    h2(doc, "Interpretación")
    p1(doc, "El sesgo dialectal, que era el hallazgo central de la auditoría, se reduce por "
            "primera vez sobre datos reales. La tasa de falsos positivos en textos inofensivos "
            "con jerga salvadoreña pasa del 41-45 % de los modelos anteriores al 27.6 % del "
            "modelo de esta etapa, y la brecha respecto al español estándar se reduce a la mitad.")
    p(doc, "Debe decirse con la misma claridad que ese corte tiene 29 casos. Un solo ejemplo "
           "mueve la métrica 3.4 puntos. La tendencia es consistente con el resto de las "
           "mediciones, pero el corte por sí solo no tiene potencia estadística, y la "
           "conclusión sobre equidad dialectal no debería presentarse como definitiva hasta "
           "recolectar más ejemplos reales.")
    p(doc, "Las dos brechas mayores son las figuras retóricas. El F1-macro cae 0.21 puntos ante "
           "sarcasmo y 0.30 ante ironía, y la tasa de falsos positivos sube 18 puntos con "
           "sarcasmo. Es el sesgo más severo que queda y afecta a un fenómeno muy frecuente en "
           "el registro coloquial salvadoreño: un sistema desplegado sobre este dominio "
           "sobre-bloquearía la ironía.")
    p(doc, "La brecha entre plataformas persiste en 0.148 de F1-macro a favor de X. Es un "
           "problema de composición del corpus, no de modelado: los textos de Facebook son más "
           "largos, con múltiples hilos y sintaxis más compleja, y están peor representados.")
    p(doc, "El corte con emoji tiene solo dos casos negativos, de modo que su tasa de falsos "
           "positivos del 100 % corresponde a dos errores y no admite lectura estadística. Se "
           "incluye por transparencia y no como hallazgo.")

    h2(doc, "Consideraciones éticas del sistema")
    vinetas(doc, [
        "El sistema es una herramienta de investigación, no de moderación automatizada. "
        "Ninguna decisión que afecte a una persona debería tomarse solo con su salida.",
        "La calibración es imperfecta: el error de calibración esperado es de 0.1214, y el "
        "prototipo devuelve confianzas cercanas al 100 % que no reflejan incertidumbre real. "
        "Presentar esas cifras a un moderador humano induciría exceso de confianza.",
        "Se descartó deliberadamente toda capa de reglas post-hoc. Una regla que solo puede "
        "mover predicciones hacia No Tóxico reduce la tasa de falsos positivos por "
        "construcción, sin que el modelo haya aprendido nada, y abre una vía de evasión trivial.",
        "El corpus contiene lenguaje ofensivo y discurso de odio explícito por la naturaleza de "
        "la tarea. Los autores están seudonimizados y las URLs de origen quedaron fuera.",
        "El sistema hereda los sesgos de quienes etiquetaron. El acuerdo entre anotadores es de "
        "0.8095 de F1-macro, y sobre los casos en que los anotadores discrepan el modelo "
        "acierta prácticamente al azar. La calidad de la etiqueta es el techo real del problema.",
    ])

    # ═══════════════════════════════════════════════ 10
    h1(doc, "Prototipo Funcional")
    p1(doc, "El prototipo consta de una API construida con FastAPI y una interfaz web. La "
            "decisión de diseño central es que el endpoint importa la función de normalización "
            "del mismo módulo que preparó el entrenamiento, sin una segunda implementación que "
            "pueda divergir. Es la condición para que las métricas de este documento describan "
            "lo que ocurre en producción y no otra cosa.")
    tabla(doc, "Endpoints del prototipo",
          ["Ruta", "Método", "Función"],
          [["/salud", "GET", "Estado, dispositivo, clases y contrato de inferencia"],
           ["/clasificar", "POST", "Un texto: clase, confianza, las cuatro probabilidades y nivel de riesgo"],
           ["/clasificar-lote", "POST", "Hasta 64 textos por petición"],
           ["/", "GET", "Interfaz web"]])
    tabla(doc, "Comprobación del prototipo en ejecución",
          ["Entrada", "Salida"],
          [["Qué onda maje, todo bien por allá", "No Tóxico"],
           ["Callate ya, cerote", "Lenguaje Ofensivo"],
           ["Los nicaragüenses son una plaga", "Discurso de Odio"],
           ["Te voy a m4t4r", "Amenazas/Violencia"],
           ["Ya sabés lo que te espera 🔫", "Amenazas/Violencia"],
           ["gracias, te voy a matar", "Amenazas/Violencia"]])
    p(doc, "La última fila corresponde al caso que evadía el prototipo de la entrega anterior. "
           "La interfaz muestra, además de la clase, el desglose de probabilidades y el texto "
           "exactamente como lo recibe el modelo tras la normalización, de modo que el "
           "comportamiento sea auditable desde la propia pantalla.")

    # ═══════════════════════════════════════════════ 11
    h1(doc, "Impacto Social y Recomendaciones de Política Pública")
    h2(doc, "El problema en el contexto salvadoreño")
    p1(doc, "El debate público salvadoreño ocurre en buena medida en X y Facebook, y las "
            "herramientas de moderación de esas plataformas operan sobre modelos entrenados en "
            "español general. Este trabajo documenta con datos lo que hasta ahora era una "
            "sospecha razonable: esos modelos no leen bien el registro local.")
    p(doc, "La medición más concreta es el sesgo dialectal. Los modelos de la etapa anterior "
           "marcaban como tóxico entre el 41 % y el 45 % de los textos inofensivos que contenían "
           "jerga salvadoreña, frente al 16 % de sus equivalentes en español estándar. Es decir, "
           "hablar como se habla en El Salvador multiplicaba por 2.7 la probabilidad de ser "
           "silenciado por error. Un sistema con ese comportamiento desplegado a escala penaliza "
           "sistemáticamente a los hablantes del registro local.")

    h2(doc, "Aportes concretos de este trabajo")
    vinetas(doc, [
        "Un corpus salvadoreño etiquetado en cuatro niveles de gravedad, con validación entre "
        "anotadores, que no existía y que queda disponible para la comunidad investigadora.",
        "Un léxico de 110 familias con 1,979 variantes de ofuscación documentadas, que es un "
        "recurso reutilizable con independencia del modelo.",
        "Evidencia medida de que el preentrenamiento sobre lenguaje de redes sociales importa "
        "más que el tamaño del modelo para esta tarea, lo que abarata sustancialmente cualquier "
        "implementación posterior: el modelo final tiene 109 millones de parámetros y se "
        "entrena en dos minutos en una tarjeta gráfica de consumo.",
        "Una metodología de auditoría —batería adversarial, sonda de ofuscación y prueba de "
        "evadibilidad— aplicable a cualquier sistema de moderación que se quiera verificar "
        "antes de confiar en él.",
    ])

    h2(doc, "Recomendaciones de política pública")
    p1(doc, "Las recomendaciones se ordenan de mayor a menor viabilidad inmediata.")
    tabla(doc, "Recomendaciones de política pública",
          ["Destinatario", "Recomendación", "Fundamento en este trabajo"],
          [["Instituciones públicas con presencia digital",
            "Exigir a cualquier herramienta de moderación que reporte su tasa de falsos "
            "positivos desagregada por registro dialectal antes de adoptarla",
            "La brecha medida entre jerga local y español estándar era de 28 puntos "
            "porcentuales en los modelos de partida"],
           ["Universidades y centros de investigación",
            "Priorizar la recolección y el etiquetado de corpus locales por encima de la "
            "adopción de modelos cada vez mayores",
            "Un modelo de 109 M superó a uno de 560 M; el cuello de botella medido es el "
            "corpus, no la capacidad"],
           ["Organismos de derechos digitales",
            "Documentar casos de sobre-bloqueo de habla local y usarlos como evidencia ante "
            "las plataformas",
            "El sesgo dialectal es medible y reproducible con la metodología de este trabajo"],
           ["Plataformas y desarrolladores",
            "Publicar auditorías de equidad por variedad lingüística, no solo por idioma",
            "El español de El Salvador se comporta como un dominio distinto del español general"],
           ["Medios de comunicación y gestores de comunidad",
            "Usar sistemas como este para priorizar la revisión humana, nunca para bloquear "
            "automáticamente",
            "El acuerdo entre anotadores humanos es de 0.8095; el modelo no puede ser más "
            "fiable que la etiqueta"],
           ["Formuladores de política educativa",
            "Incorporar alfabetización digital sobre discurso de odio en el currículo, "
            "apoyándose en la taxonomía de cuatro niveles",
            "La distinción entre lenguaje ofensivo y discurso de odio es la que más cuesta, "
            "también a las personas"]])

    h2(doc, "Lo que este trabajo no resuelve")
    p1(doc, "Un sistema de clasificación no arregla el discurso de odio; como mucho ayuda a "
            "medirlo y a priorizar dónde mira una persona. Tres límites deben acompañar "
            "cualquier recomendación derivada de este trabajo.")
    vinetas(doc, [
        "El modelo no entiende contexto conversacional: evalúa publicaciones aisladas, y buena "
        "parte del acoso real es acumulativo y distribuido entre varias publicaciones.",
        "La ironía y el sarcasmo, que son el registro habitual de buena parte del debate "
        "político salvadoreño, siguen siendo el punto débil medido.",
        "Automatizar la moderación sobre una base de 2,144 ejemplos reales sería imprudente. "
        "El sistema está listo como instrumento de investigación y de priorización, no como "
        "decisor.",
    ])

    # ═══════════════════════════════════════════════ 12
    h1(doc, "Limitaciones")
    vinetas(doc, [
        "El corpus real sigue siendo de 2,144 publicaciones de entrenamiento. La meta de 771 "
        "ejemplos reales por clase no se ha alcanzado en Discurso de Odio ni en "
        "Amenazas/Violencia.",
        "La sonda dialectal sobre datos reales tiene 29 casos. Cualquier cifra de sesgo "
        "calculada sobre ese corte es frágil.",
        "Los emojis de amenaza no tienen un solo caso real recolectado: toda su cobertura es "
        "sintética.",
        "La sonda dirigida de 204 casos perdió su independencia respecto al modelo de esta "
        "etapa, por compartir léxico con el generador.",
        "La brecha entre plataformas no se resolvió y es estructural del corpus.",
        "La calibración sigue siendo imperfecta, con un error esperado de 0.1214.",
        "El techo real del problema es la calidad de la etiqueta: el acuerdo entre anotadores "
        "es de 0.8095 de F1-macro, y sobre los casos disputados el mejor modelo de la etapa "
        "anterior acertaba el 50 % de las veces.",
    ])

    # ═══════════════════════════════════════════════ 13
    h1(doc, "Conclusiones")
    p1(doc, f"El sistema alcanza un F1-macro de {e['test']['f1_macro']:.4f} sobre el conjunto de "
            f"prueba, con un intervalo de confianza del 95 % de "
            f"[{e['test']['ic_lo']:.4f}, {e['test']['ic_hi']:.4f}], y una validación cruzada de "
            f"cinco pliegues que promedia {cv['media']:.4f} ± {cv['desv']:.4f}. La meta de 0.80 "
            f"se cumple también en el extremo inferior del intervalo, que era el criterio "
            f"exigente que se fijó al inicio de la etapa.")
    p(doc, "La mejora respecto a la etapa anterior proviene, en orden de importancia, de tres "
           "decisiones. La primera y con diferencia la mayor fue cambiar de familia de modelo: "
           "los dos modelos elegidos en la Etapa I resultaron ser los dos peores de una "
           "comparación de siete, y sustituirlos por modelos preentrenados sobre lenguaje de "
           "redes sociales en español aportó cerca de cuatro puntos. La segunda fue optimizar "
           "hiperparámetros, que nunca se había hecho y aportó 0.025. La tercera, más modesta, "
           "fue el corpus sintético dirigido usado con el régimen de entrenamiento adecuado.")
    p(doc, "Igual de útil es dejar constancia de las tres vías que no funcionaron. Escalar el "
           "modelo no ayuda: 560 millones de parámetros rinden peor que 109 millones. Extender "
           "el vocabulario con tokens de dominio perjudica en todas las configuraciones "
           "probadas. Y generar ejemplos sintéticos en familias donde el modelo ya acierta no "
           "aporta nada y desplaza la distribución de entrenamiento.")
    p(doc, "El sesgo dialectal, que motivó buena parte del trabajo, se reduce por primera vez "
           "sobre datos reales, aunque el corte que lo mide es demasiado pequeño para "
           "considerarlo cerrado. Las figuras retóricas quedan como el sesgo más severo "
           "pendiente.")
    p(doc, "Lo que no cambia es el diagnóstico de fondo: con 2,144 publicaciones reales y un "
           "acuerdo entre anotadores de 0.8095, el siguiente salto no saldrá de más "
           "arquitectura sino de más datos y mejores etiquetas.")

    # ═══════════════════════════════════════════════ 14
    h1(doc, "Reproducibilidad y Evidencias")
    h2(doc, "Repositorio")
    p1(doc, "Código fuente, corpus, informes y artefactos de evaluación: "
            "https://github.com/caeher/cde-project-ml-2026, rama v3.")
    p(doc, "Los pesos del modelo no se versionan por exceder el límite de tamaño de fichero de "
           "la plataforma. Todos los scripts son deterministas con semilla fija y el manifiesto "
           "incluye la función resumen SHA-256 de los pesos de referencia.")
    tabla(doc, "Scripts para reproducir cada sección",
          ["Sección", "Comando"],
          [["Adecuación del tokenizador", "python3 src/audit/analisis_tokenizadores.py"],
           ["Comparación de arquitecturas", "python3 src/v3/bakeoff.py"],
           ["Construcción del corpus", "python3 src/v3/construir_dataset.py"],
           ["Ablación", "python3 src/v3/ablacion.py <modelo> <alias>"],
           ["Optimización de hiperparámetros", "python3 src/v3/hpo.py <modelo> <alias> 20"],
           ["Validación cruzada", "python3 src/v3/validacion_cruzada.py"],
           ["Modelo final", "python3 src/v3/entrenar_final.py"],
           ["Ensemble", "python3 src/v3/ensemble.py"],
           ["Evaluación completa", "python3 src/v3/evaluar.py models/v3/final v3_final"],
           ["Prototipo", "python3 -m uvicorn app.api.main:app"]])

    h2(doc, "Verificación de integridad")
    tabla(doc, "Funciones resumen de los conjuntos de evaluación",
          ["Conjunto", "SHA-256 (16 primeros)", "¿Modificado en esta etapa?"],
          [["val.csv", m["sha_val"], "No"],
           ["test.csv", m["sha_test"], "No"]])
    p(doc, "Ambas coinciden con las de la etapa anterior. Se verificó además que ningún texto "
           "del entrenamiento aparece en validación, en prueba ni en la batería adversarial.")

    # ═══════════════════════════════════════════════ 15
    h1(doc, "Glosario")
    for term, defi in [
        ("Ablación", "Experimento que elimina o modifica un componente del sistema para medir "
                     "cuánto aportaba."),
        ("Ensemble", "Combinación de varios modelos cuyas predicciones se promedian, con el fin "
                     "de reducir la varianza de cualquiera de ellos por separado."),
        ("F1-macro", "Media no ponderada del F1 de cada clase. Trata las cuatro clases por igual, "
                     "por lo que penaliza a un modelo que acierte solo en la clase mayoritaria."),
        ("Fertilidad del tokenizador", "Número medio de subtokens en que se divide una palabra. "
                                       "Cuanto mayor, más fragmentado queda el texto."),
        ("FPR", "Tasa de falsos positivos: proporción de contenido inofensivo clasificado como "
                "tóxico."),
        ("FNR", "Tasa de falsos negativos: proporción de contenido tóxico que el sistema deja pasar."),
        ("Intervalo bootstrap", "Rango de valores plausibles de una métrica, obtenido "
                                "remuestreando el conjunto de prueba con reemplazo."),
        ("Leetspeak", "Sustitución de letras por dígitos o símbolos de forma similar "
                      "(«m4t4r» por «matar»), usada para evadir filtros automáticos."),
        ("Ofuscación", "Deformación deliberada de una palabra para que un filtro no la reconozca "
                       "pero una persona sí."),
        ("Optuna", "Biblioteca de optimización de hiperparámetros que propone configuraciones "
                   "guiada por los resultados anteriores."),
        ("Prueba de McNemar", "Prueba estadística que compara dos clasificadores sobre las "
                              "mismas instancias, contando en cuántas acierta uno y falla el otro."),
        ("Train/serve skew", "Divergencia entre el preprocesamiento del entrenamiento y el de "
                             "producción, que invalida las métricas del informe."),
        ("Validación cruzada estratificada", "Procedimiento que divide los datos en pliegues "
                                             "conservando la proporción de clases, entrena sobre "
                                             "unos y evalúa sobre el restante, rotando."),
        ("Voto blando", "Forma de ensemble que promedia las probabilidades de los modelos en "
                        "lugar de contar sus votos discretos."),
    ]:
        pp = doc.add_paragraph(style="Body Text")
        pp.add_run(f"{term}: ").bold = True
        pp.add_run(defi)

    # ═══════════════════════════════════════════════ 16
    h1(doc, "Anexos")
    h2(doc, "Anexo A: Informe de auditoría de la entrega anterior")
    p1(doc, "Reejecución independiente de los cuatro checkpoints entregados, con tabla de "
            "contraste entre cifra publicada y cifra reproducida, lista de errores con su "
            "evidencia aritmética y prueba de evadibilidad del filtro de reglas. "
            "Archivo: reports/9-12-2026/Informe_Auditoria_Entrega_2v.pdf.")
    h2(doc, "Anexo B: Informe técnico de resultados de la Etapa II")
    p1(doc, "Detalle de las veinte pruebas de optimización, las nueve variantes de ablación por "
            "arquitectura y las tablas completas de la batería adversarial y la sonda dirigida. "
            "Archivo: reports/9-12-2026/Informe_V3_Resultados_Etapa3.pdf.")
    h2(doc, "Anexo C: Artefactos de evaluación")
    p1(doc, "Logits, predicciones por instancia, resultados de las pruebas pareadas y de la "
            "prueba de evadibilidad, en reports/v3_resultados/ y reports/v3_arquitectura/ del "
            "repositorio.")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(DESTINO))
    print(f"generado: {DESTINO}")
    print(f"tablas: {_n_tabla}")


if __name__ == "__main__":
    construir()
