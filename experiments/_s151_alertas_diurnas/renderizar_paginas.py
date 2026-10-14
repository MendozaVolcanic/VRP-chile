# -*- coding: utf-8 -*-
"""Renderiza a imagen (PyMuPDF, 200 dpi) las paginas que hablan del dia en los papers de MIROVA (A95).

La capa de texto de PyMuPDF corrompe operadores y simbolos; estas paginas se LEEN como imagen. Solo se usa
`get_text` para ubicar en que pagina buscar. Las imagenes van a un directorio temporal pasado como argumento
(no se commitean: son paginas de papers con derechos de autor).
Uso: python renderizar_paginas.py <dir_salida>
"""
import sys
from pathlib import Path

import fitz

DOC = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/documentacion")
PAGINAS = {
    "sp426.5.pdf": [2, 5, 6, 15],
    "campus2022_sensors_22_1713.pdf": [15, 16],
    "Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf": [6, 7],
    "THESIS_MASSIMETTI.pdf": [38, 39, 138],
}

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for fn, idxs in PAGINAS.items():
    d = fitz.open(DOC / fn)
    for i in idxs:
        pix = d[i].get_pixmap(dpi=200)
        dest = out / ("%s_idx%02d.png" % (Path(fn).stem[:20], i))
        pix.save(dest)
        print(dest, pix.width, pix.height)
