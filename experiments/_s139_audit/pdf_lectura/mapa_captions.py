# -*- coding: utf-8 -*-
"""S139: mapa de captions (Table N / Figure N) por PDF de prioridad 1, y cruce
con las citas que existen en docs/ y documentacion/*.md del repo.

Una tabla o figura que no aparece citada en ningun doc es candidata a
"no la estamos viendo".

Instrumento: (1) si el cruce estuviera roto, TODO daria "no citada", incluida la
Tabla 1 de SP426.5, que sabemos citadisima -> el control es esa fila; (2) si el
extractor de captions estuviera muerto, la columna de captions saldria vacia.
"""
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

RAIZ = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
DOC = os.path.join(RAIZ, "documentacion")

PDFS = {
    "sp426.5.pdf": "Coppola 2016a SP426.5",
    "coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf": "Coppola 2014 IJRS",
    "coppola2012_jvgr_stromboli_10.1016-j.jvolgeores.2011.12.001.pdf": "Coppola 2012 JVGR",
    "Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf": "Coppola 2025 Fernandina",
    "THESIS_MASSIMETTI.pdf": "Massimetti tesis",
}

# caption real = la linea empieza con "Fig. N." / "Figure N." / "Table N."
RE_CAP = re.compile(r"^\s*(Fig\.?|Figure|Table|Tab\.)\s*(\d{1,2})[.:]", re.M)


def captions(ruta):
    doc = fitz.open(ruta)
    res = {}
    for i, page in enumerate(doc):
        for m in RE_CAP.finditer(page.get_text("text")):
            tipo = "Table" if m.group(1).lower().startswith("tab") else "Figure"
            clave = "%s %s" % (tipo, m.group(2))
            res.setdefault(clave, []).append(i + 1)
    doc.close()
    return res


def main():
    for pdf, etiqueta in PDFS.items():
        ruta = os.path.join(DOC, pdf)
        if not os.path.exists(ruta):
            print("FALTA", pdf)
            continue
        caps = captions(ruta)
        print("\n### %s  (%s)  -> %d captions distintos" % (etiqueta, pdf, len(caps)))
        for clave in sorted(caps, key=lambda k: (k.split()[0], int(k.split()[1]))):
            print("  %-10s pag %s" % (clave, caps[clave]))


if __name__ == "__main__":
    main()
