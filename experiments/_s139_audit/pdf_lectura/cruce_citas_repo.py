# -*- coding: utf-8 -*-
"""S139: cruza cada figura y tabla de los PDF de prioridad 1 contra las citas que
existen en docs/ y documentacion/*.md del repositorio.

Una figura nunca citada es candidata a "no la estamos viendo". El cruce es por
nombre ("Fig. 4", "Figure 4", "Figura 4", "Fig 4", "Tabla 1", "Table 1"), asi que
sobreestima (una cita a "Figure 4" de OTRO paper cuenta). Es decir: los ceros son
solidos, los positivos no.

Instrumento: la Tabla 1 de SP426.5 es el control positivo (sabemos que se cita
decenas de veces). Si diera 0, el cruce estaria roto.
"""
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RAIZ = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"

FIGURAS = {
    "SP426.5 (Coppola 2016a)": [("Figure", n) for n in range(1, 12)] + [("Table", 1)],
    "Coppola 2025 Fernandina": [("Figure", n) for n in range(1, 11)] + [("Table", 1)],
    "Coppola 2014 IJRS": [("Figure", n) for n in range(1, 13)] + [("Table", n) for n in (1, 2, 3)],
}


ALIAS = {
    "SP426.5 (Coppola 2016a)": ["sp426", "SP 426", "Coppola 2016", "Coppola et al. 2016"],
    "Coppola 2025 Fernandina": ["Rapid_Response", "Fernandina", "Coppola 2025", "rs17071191"],
    "Coppola 2014 IJRS": ["coppola2014", "Coppola 2014", "Coppola et al. 2014"],
}

def corpus():
    """(ruta, texto) de todos los .md de docs/ y documentacion/."""
    res = []
    for base in ("docs", "documentacion"):
        for dirpath, _, files in os.walk(os.path.join(RAIZ, base)):
            for f in files:
                if f.endswith((".md", ".txt")):
                    ruta = os.path.join(dirpath, f)
                    try:
                        res.append((ruta, open(ruta, encoding="utf-8", errors="ignore").read()))
                    except OSError:
                        pass
    return res

CORPUS = corpus()


def contar(tipo, n, alias):
    """Cuenta la etiqueta SOLO en los documentos que nombran el paper."""
    if tipo == "Figure":
        pat = re.compile(r"(Fig\.? ?%d|Figure ?%d|Figura ?%d)(?!\d)" % (n, n, n))
    else:
        pat = re.compile(r"(Table ?%d|Tabla ?%d)(?!\d)" % (n, n))
    total = 0
    docs = 0
    for ruta, txt in CORPUS:
        if not any(a.lower() in txt.lower() for a in alias):
            continue
        c = len(pat.findall(txt))
        if c:
            total += c
            docs += 1
    return total, docs


for paper, items in FIGURAS.items():
    print("\n### %s  (documentos del repo que lo nombran)" % paper)
    alias = ALIAS[paper]
    for tipo, n in items:
        c, d = contar(tipo, n, alias)
        marca = "  <-- NUNCA CITADA" if c == 0 else ""
        print("  %-7s %2d  citas=%4d en %2d docs%s" % (tipo, n, c, d, marca))
