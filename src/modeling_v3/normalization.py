"""
Normalización de texto para el corpus salvadoreño de toxicidad.

FILOSOFÍA — "preservación máxima"
---------------------------------
Este pipeline es DELIBERADAMENTE conservador. NO corrige ortografía, NO elimina
tildes, NO pasa a minúsculas, NO elimina signos de puntuación, NO lematiza y NO
elimina stopwords.

Razones técnicas:

1. mBERT (bert-base-multilingual-CASED) y XLM-R fueron preentrenados sobre texto
   real en español, con tildes, mayúsculas y puntuación. Su vocabulario subword
   ya modela esas formas. Normalizar las destruye y aleja la entrada de la
   distribución de preentrenamiento.

2. Las faltas de ortografía y el leetspeak ("4güevo", "pvto") no son ruido: en
   contenido tóxico son con frecuencia EVASIÓN DELIBERADA de moderación. Son
   señal, no error. El léxico del proyecto (lexicon_salvadoreno.csv) documenta
   2,035 de estas variantes precisamente porque importan.

3. TRAIN/SERVE SKEW: en producción la API recibirá texto crudo de usuarios. Toda
   transformación aplicada al entrenamiento debe aplicarse idénticamente en
   inferencia. Cuanto más corto y determinista el pipeline, menor el riesgo.
   Por eso este módulo es la ÚNICA fuente de verdad: lo importa el notebook,
   el script de entrenamiento y el endpoint de FastAPI.

Lo que SÍ se hace, y por qué:
  - Unicode NFC        : dos representaciones de "á" deben ser el mismo token.
  - ftfy (mojibake)    : reparar "Ã±" -> "ñ" cuando exista.
  - Caracteres invisibles: zero-width y variation selectors rompen tokenizadores.
  - Colapso de espacios: whitespace no es señal lingüística.
  - Placeholders PII   : @menciones y URLs se reemplazan por un token constante.
                         NO se eliminan: la PRESENCIA de una mención distingue un
                         ataque dirigido de una afirmación general, y eso sí es
                         señal. Se elimina la identidad, se conserva la estructura.
  - Emojis (opcional)  : ver docstring de `demojizar`.
"""

from __future__ import annotations

import re
import unicodedata

import emoji as _emoji

try:
    import ftfy as _ftfy

    _HAS_FTFY = True
except ImportError:  # pragma: no cover
    _HAS_FTFY = False


# --------------------------------------------------------------------------
# Tokens placeholder. Se eligen en minúscula y sin caracteres especiales para
# que los tokenizadores subword los segmenten de forma estable y consistente.
# --------------------------------------------------------------------------
TOKEN_USUARIO = "@usuario"
TOKEN_URL = "http://url"
TOKEN_EMAIL = "correo@ejemplo.com"
TOKEN_TELEFONO = "0000-0000"

# --------------------------------------------------------------------------
# Expresiones regulares
# --------------------------------------------------------------------------
RE_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
# La arroba solo abre mención si NO viene pegada a una letra o dígito. Sin esta
# guarda, "m@tar" se convertía en "m@usuario": la ofuscación con arroba es
# justamente una de las evasiones que el sistema debe detectar, así que
# destruirla en la normalización sería borrar la señal.
RE_MENCION = re.compile(r"(?<![\w@])@[A-Za-z0-9_]{1,30}\b")
RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
# Teléfonos de El Salvador: 8 dígitos, opcionalmente con +503 y separadores.
RE_TELEFONO = re.compile(r"(?:\+?503[\s-]?)?\b[267]\d{3}[\s-]?\d{4}\b")
RE_ESPACIOS = re.compile(r"\s+")
# Zero-width, BOM, soft hyphen, marcas bidireccionales.
RE_INVISIBLES = re.compile(r"[​-‏‪-‮⁠﻿­]")
# Variation Selector-16: fuerza presentación emoji, invisible, rompe vocabularios.
RE_VS16 = re.compile(r"️")
# Modificadores de tono de piel (Fitzpatrick U+1F3FB..U+1F3FF).
RE_TONO_PIEL = re.compile(r"[\U0001F3FB-\U0001F3FF]")
RE_HASHTAG = re.compile(r"#(\w+)")


# --------------------------------------------------------------------------
# Pasos individuales
# --------------------------------------------------------------------------
def reparar_codificacion(texto: str) -> str:
    """Repara mojibake ('Ã±' -> 'ñ') y normaliza a Unicode NFC."""
    if _HAS_FTFY:
        texto = _ftfy.fix_text(texto)
    return unicodedata.normalize("NFC", texto)


def quitar_invisibles(texto: str) -> str:
    """Elimina caracteres de ancho cero y marcas bidireccionales."""
    return RE_INVISIBLES.sub("", texto)


def anonimizar(texto: str) -> str:
    """
    Sustituye PII por tokens constantes. El ORDEN importa: email antes que
    mención, porque 'juan@correo.com' contiene un patrón tipo @correo.
    """
    texto = RE_URL.sub(TOKEN_URL, texto)
    texto = RE_EMAIL.sub(TOKEN_EMAIL, texto)
    texto = RE_MENCION.sub(TOKEN_USUARIO, texto)
    texto = RE_TELEFONO.sub(TOKEN_TELEFONO, texto)
    return texto


# La librería `emoji` traduce U+1F52A como ":pistola_de_agua:" porque ese es el
# nombre Unicode vigente: en 2016 los fabricantes rediseñaron el glifo como
# pistola de juguete. Para este proyecto esa traducción es falsa — el catálogo
# documenta 🔫 como vehículo de amenaza — y le enseñaba al modelo "agua" donde
# hay un arma. Se corrige aquí, que es el único punto por el que pasa el texto.
CORRECCIONES_EMOJI = {
    ":pistola_de_agua:": ":pistola:",
}


def _corregir_nombres(texto: str) -> str:
    for malo, bueno in CORRECCIONES_EMOJI.items():
        texto = texto.replace(malo, bueno)
    return texto


def demojizar(texto: str, quitar_tono_piel: bool = True, idioma: str = "es") -> str:
    """
    Convierte emojis a su descripción textual en español.

        "sos un 🤡"  ->  "sos un :payaso:"

    ¿Por qué convertir en vez de dejar el emoji crudo?

    - mBERT usa un vocabulario WordPiece construido sobre volcados de Wikipedia
      (2018), donde prácticamente no hay emojis. La mayoría cae en [UNK] y la
      señal se pierde por completo.
    - XLM-R usa SentencePiece sobre CommonCrawl (CC-100), que sí contiene
      emojis: la cobertura es mejor pero irregular. Los emojis frecuentes están;
      las secuencias ZWJ, banderas (pares de indicadores regionales) y
      modificadores de tono de piel se fragmentan o se pierden.
    - La descripción textual siempre se segmenta en subwords que el modelo
      conoce, así que la señal sobrevive en ambos modelos por igual.
    - RoBERTuito (pysentimiento), uno de los baselines del proyecto, aplica
      exactamente esta conversión en su preprocesamiento. Usar el mismo criterio
      hace la comparación justa.

    ¿Por qué quitar el tono de piel? "🖕🏼" y "🖕🏾" expresan lo mismo. El
    modificador solo fragmenta el token y multiplica la dispersión. Se elimina
    salvo que el análisis sea específicamente sobre racialización.

    NOTA: no destruye información. El texto original queda intacto en la columna
    `texto_original`; esto genera una columna PARALELA (`texto_modelo`).
    """
    if quitar_tono_piel:
        texto = RE_TONO_PIEL.sub("", texto)
    texto = RE_VS16.sub("", texto)
    return _corregir_nombres(_emoji.demojize(texto, language=idioma, delimiters=(" :", ": ")))

def separar_hashtags(texto: str, conservar_almohadilla: bool = True) -> str:
    """
    Deja el hashtag legible. En español los hashtags suelen ser una sola palabra
    ('#pupusas'), así que NO se aplica segmentación CamelCase agresiva; solo se
    garantiza que quede separado del texto contiguo.
    """
    if conservar_almohadilla:
        return texto
    return RE_HASHTAG.sub(r"\1", texto)


def colapsar_espacios(texto: str) -> str:
    """Colapsa cualquier secuencia de whitespace a un espacio simple y recorta."""
    return RE_ESPACIOS.sub(" ", texto).strip()


# --------------------------------------------------------------------------
# Pipeline público
# --------------------------------------------------------------------------
def normalizar(
    texto: str,
    *,
    con_emojis: bool = True,
    anonimizacion: bool = True,
    quitar_tono_piel: bool = True,
) -> str:
    """
    Pipeline canónico. Esta función debe llamarse IDÉNTICAMENTE en:
      1. la preparación del dataset de entrenamiento,
      2. la evaluación,
      3. el endpoint de inferencia en `app/api/`.

    Parameters
    ----------
    con_emojis : convertir emojis a texto en español. Recomendado True.
    anonimizacion : reemplazar @menciones, URLs, emails y teléfonos.
    quitar_tono_piel : eliminar modificadores Fitzpatrick.

    Returns
    -------
    str : texto listo para el tokenizador.
    """
    if not isinstance(texto, str):
        return ""

    texto = reparar_codificacion(texto)
    texto = quitar_invisibles(texto)
    if anonimizacion:
        texto = anonimizar(texto)
    if con_emojis:
        texto = demojizar(texto, quitar_tono_piel=quitar_tono_piel)
    texto = colapsar_espacios(texto)
    return texto


def normalizar_agresivo(texto: str) -> str:
    """
    Variante DESTRUCTIVA, incluida solo como grupo de control para el estudio de
    ablación. Aplica el preprocesamiento "clásico" de NLP pre-Transformers:
    minúsculas, sin tildes, sin puntuación, sin emojis.

    NO usar en producción. Existe para poder demostrar empíricamente, con F1
    medido, que degrada el rendimiento respecto a `normalizar()`.
    """
    texto = normalizar(texto, con_emojis=False)
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\d+", " ", texto)
    return colapsar_espacios(texto)


# --------------------------------------------------------------------------
# Utilidades de diagnóstico (usadas por el EDA)
# --------------------------------------------------------------------------
def perfil_texto(texto: str) -> dict:
    """Extrae indicadores estructurales de un texto, sin modificarlo."""
    if not isinstance(texto, str):
        texto = ""
    return {
        "n_chars": len(texto),
        "n_palabras": len(texto.split()),
        "n_emojis": _emoji.emoji_count(texto),
        "n_menciones": len(RE_MENCION.findall(texto)),
        "n_urls": len(RE_URL.findall(texto)),
        "n_hashtags": len(RE_HASHTAG.findall(texto)),
        "tiene_tildes": bool(re.search(r"[áéíóúñüÁÉÍÓÚÑÜ]", texto)),
        "ratio_mayusculas": (
            sum(c.isupper() for c in texto) / max(sum(c.isalpha() for c in texto), 1)
        ),
        "n_exclamaciones": texto.count("!") + texto.count("¡"),
        "elongacion": bool(re.search(r"(.)\1{2,}", texto)),  # "holaaaa", "jajajaja"
    }
