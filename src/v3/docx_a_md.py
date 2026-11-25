# -*- coding: utf-8 -*-
"""
Convierte el .docx de la Etapa II al Markdown que alimenta el PDF.

La distinción entre viñeta y prosa no se hace por estilo —ambas usan Body Text,
igual que en el documento de la Etapa I— sino por la presencia de la referencia
de numeración en el párrafo, que es lo que de verdad dibuja la viñeta.
"""
import sys
from pathlib import Path

import emoji
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _imagen(hijo, doc, destino: Path):
    """Extrae la imagen de un párrafo y devuelve su ruta, o None si no tiene."""
    blip = hijo.find(f".//{A}blip")
    if blip is None:
        return None
    rid = blip.get(f"{R}embed")
    parte = doc.part.related_parts[rid]
    ruta = destino / Path(parte.partname).name
    ruta.write_bytes(parte.blob)
    return ruta


def convertir(ruta_docx: Path, dir_imagenes: Path | None = None) -> str:
    d = Document(str(ruta_docx))
    if dir_imagenes:
        dir_imagenes.mkdir(parents=True, exist_ok=True)
    salida = []
    empezo_el_cuerpo = False
    for hijo in d.element.body:
        if hijo.tag == f"{W}p":
            par = Paragraph(hijo, d)
            texto = par.text.strip()
            if not texto:
                # las figuras son párrafos sin texto que contienen la imagen;
                # la portada se omite porque el PDF la toma del documento anterior
                if dir_imagenes and empezo_el_cuerpo:
                    img = _imagen(hijo, d, dir_imagenes)
                    if img is not None:
                        salida.append(f"\n![]({img.as_posix()})\n")
                continue
            estilo = par.style.name
            es_vineta = bool(hijo.findall(f".//{W}numPr"))
            if estilo == "Heading 1":
                empezo_el_cuerpo = True
                salida.append(f"\n# {texto}\n")
            elif estilo == "Heading 2":
                salida.append(f"\n## {texto}\n")
            elif estilo == "Caption":
                salida.append(f"\n*{texto}*\n")
            elif es_vineta:
                salida.append(f"- {texto}")
            else:
                salida.append(f"\n{texto}\n")
        elif hijo.tag == f"{W}tbl":
            tb = Table(hijo, d)
            filas = [[c.text.strip().replace("|", "\\|").replace("\n", " ")
                      for c in r.cells] for r in tb.rows]
            if not filas:
                continue
            salida += ["", "| " + " | ".join(filas[0]) + " |",
                       "|" + "---|" * len(filas[0])]
            salida += ["| " + " | ".join(f) + " |" for f in filas[1:]] + [""]

    md = "\n".join(salida)
    # Las fuentes disponibles no tienen glifos de emoji; se sustituyen por su nombre
    return emoji.replace_emoji(
        md, replace=lambda ch, x: f"[{emoji.demojize(ch, language='es').strip(':').replace('_', ' ')}]")


if __name__ == "__main__":
    imgs = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    Path(sys.argv[2]).write_text(convertir(Path(sys.argv[1]), imgs), encoding="utf-8")
    print(f"markdown -> {sys.argv[2]}")
