# -*- coding: utf-8 -*-
"""S139: que pierde la capa de texto de sp426.5.pdf, pagina por pagina.

Dos perdidas distintas y separables:
 (A) OPERADORES: los glifos <, >, <=, >=, sigma, mu, +- no llegan a la capa de
     texto; quedan como coma, "2", "4" u otro digito (regla A95). Se cuenta cuantas
     veces el patron de corrupcion aparece y se muestra el contexto.
 (B) TEXTO DENTRO DE IMAGENES: todo rotulo de panel, eje y barra de color de una
     figura es raster. Ninguna herramienta de texto lo ve. Se marca cada pagina con
     imagenes y cuantas.

Instrumento:
 (1) Si el detector de (A) estuviera roto daria 0 en la pagina 21 del PDF, donde la
     leyenda de la Fig. A6 dice "NTI < -0.93" y sabemos que el .txt trae ",20.93".
     Esa pagina es el control.
 (2) Si el detector de (B) estuviera muerto, las 25 paginas darian 0 imagenes, y
     sabemos que las de figuras las tienen.
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

RAIZ = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
PDF = os.path.join(RAIZ, "documentacion", "sp426.5.pdf")

# ",2" seguido de digito = "< -" comido;  ",0"/",-" variantes; "40"/".2" son ruido
RE_CORR = re.compile(r"[,]\s?[24]\s?[-\u2212]?\d")
RE_OP = re.compile(r"[<>\u2264\u2265\u03c3\u03bc\u00b1]")

doc = fitz.open(PDF)
tot_corr = tot_op = 0
print("pag  img  operadores_en_texto  corrupciones  contexto")
for i, page in enumerate(doc):
    t = page.get_text("text")
    ops = RE_OP.findall(t)
    corr = RE_CORR.findall(t)
    tot_op += len(ops)
    tot_corr += len(corr)
    ctx = []
    for m in RE_CORR.finditer(t):
        ctx.append(t[max(0, m.start() - 34) : m.end() + 6].replace("\n", " "))
    print(
        "%3d  %3d  %3d  %3d  %s"
        % (i + 1, len(page.get_images(full=True)), len(ops), len(corr), " | ".join(ctx[:2]))
    )
print("\nTOTAL en 25 paginas: operadores visibles en la capa de texto = %d ; corrupciones = %d" % (tot_op, tot_corr))
doc.close()
