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


def convertir(ruta_docx: Path) -> str:
    d = Document(str(ruta_docx))
    salida = []
    for hijo in d.element.body:
        if hijo.tag == f"{W}p":
            par = Paragraph(hijo, d)
            texto = par.text.strip()
            if not texto:
                continue
            estilo = par.style.name
            es_vineta = bool(hijo.findall(f".//{W}numPr"))
            if estilo == "Heading 1":
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
    Path(sys.argv[2]).write_text(convertir(Path(sys.argv[1])), encoding="utf-8")
    print(f"markdown -> {sys.argv[2]}")
