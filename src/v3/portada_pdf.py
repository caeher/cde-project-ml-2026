# -*- coding: utf-8 -*-
"""
Construye el PDF de la Etapa II con la portada institucional real.

En esta máquina no hay LibreOffice, así que el .docx no puede convertirse
directamente. Se reutiliza la portada del PDF de la Etapa I —que es la plantilla
oficial del equipo— parcheando sobre ella el número de etapa y la fecha, y se le
antepone al cuerpo generado con pandoc. El resultado es visualmente el mismo
documento, no una aproximación.
"""
import sys
from pathlib import Path

import fitz

RAIZ = Path(__file__).resolve().parents[2]
ETAPA1 = RAIZ / "docs/etapa-1/Etapa I - Analisis de Discurso de Odio en Redes Sociales en El Salvador.pdf"

# (texto a sustituir, texto nuevo, tamaño, color, alineación)
CAMBIOS = [
    ("ETAPA I ", "ETAPA II", 26.0, 0xFFFFFF, "izq"),
    ("Ciudad universitaria, 16 de julio del 2026", "Ciudad universitaria, 12 de septiembre del 2026",
     18.0, 0x000000, "der"),
]


def _rgb(v):
    return ((v >> 16 & 255) / 255, (v >> 8 & 255) / 255, (v & 255) / 255)


def construir_portada(destino: Path) -> Path:
    src = fitz.open(ETAPA1)
    tapa = fitz.open()
    tapa.insert_pdf(src, from_page=0, to_page=0)
    pag = tapa[0]

    for viejo, nuevo, tam, color, alin in CAMBIOS:
        cajas = pag.search_for(viejo.strip())
        if not cajas:
            print(f"  aviso: no se encontró {viejo!r} en la portada")
            continue
        caja = cajas[0]
        # se tapa el texto original muestreando el color de fondo de su entorno
        fondo = pag.get_pixmap(clip=fitz.Rect(caja.x0, caja.y0 - 6, caja.x0 + 4, caja.y0 - 2))
        col = tuple(c / 255 for c in fondo.pixel(0, 0)[:3]) if fondo.width else (1, 1, 1)
        pag.draw_rect(fitz.Rect(caja.x0 - 2, caja.y0 - 4, pag.rect.x1, caja.y1 + 4),
                      color=col, fill=col)
        x = caja.x0 if alin == "izq" else caja.x1 - fitz.get_text_length(
            nuevo, fontname="tiro", fontsize=tam)
        pag.insert_text((x, caja.y1 - tam * 0.16), nuevo, fontname="tiro",
                        fontsize=tam, color=_rgb(color))
        print(f"  portada: {viejo.strip()!r} -> {nuevo!r}")

    tapa.save(destino)
    tapa.close(); src.close()
    return destino


def unir(portada: Path, cuerpo: Path, salida: Path):
    doc = fitz.open(portada)
    b = fitz.open(cuerpo)
    doc.insert_pdf(b)
    doc.save(salida, garbage=3, deflate=True)
    n = len(doc)
    doc.close(); b.close()
    return n


if __name__ == "__main__":
    tmp = Path("/tmp/_portada.pdf")
    construir_portada(tmp)
    if len(sys.argv) > 2:
        n = unir(tmp, Path(sys.argv[1]), Path(sys.argv[2]))
        print(f"unido: {n} páginas -> {sys.argv[2]}")
