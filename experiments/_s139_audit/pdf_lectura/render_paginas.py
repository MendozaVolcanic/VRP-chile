# -*- coding: utf-8 -*-
"""S139: renderiza a PNG paginas concretas de un PDF del corpus, para mirarlas
con la herramienta Read (la capa de texto corrompe los operadores, regla A95).

Uso:  python render_paginas.py <archivo.pdf> <pag1> <pag2> ...   (1-based)
Los PNG van a out/ y NO se commitean (derechos de autor, repo publico).
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

RAIZ = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
DOC = os.path.join(RAIZ, "documentacion")
OUT = os.path.join(RAIZ, "experiments", "_s139_audit", "pdf_lectura", "out")
os.makedirs(OUT, exist_ok=True)


def main():
    nombre = sys.argv[1]
    paginas = [int(x) for x in sys.argv[2:]]
    dpi = int(os.environ.get("DPI", "150"))
    doc = fitz.open(os.path.join(DOC, nombre))
    base = os.path.splitext(nombre)[0].replace(".", "_")[:30]
    for n in paginas:
        page = doc[n - 1]
        pix = page.get_pixmap(dpi=dpi)
        destino = os.path.join(OUT, "%s_p%03d.png" % (base, n))
        pix.save(destino)
        print("%s  (%dx%d)" % (destino, pix.width, pix.height))
    doc.close()


if __name__ == "__main__":
    main()
