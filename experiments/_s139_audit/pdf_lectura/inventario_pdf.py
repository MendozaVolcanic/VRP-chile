# -*- coding: utf-8 -*-
"""S139 auditoria (tanda 2): inventario de tablas, figuras y ecuaciones por pagina
en los PDF de prioridad 1 del corpus MIROVA.

NO modifica nada del repositorio. Escribe un JSON en out/ y, opcionalmente,
renderiza a PNG las paginas marcadas.

Las dos preguntas del instrumento:
 (1) si la deteccion estuviera rota, lo veria? -> el script imprime, por PDF,
     cuantas paginas dan 0 en cada categoria; un PDF con 0 figuras en 25 paginas
     seria sospechoso y se revisa a mano.
 (2) si el instrumento estuviera muerto? -> get_images/get_drawings/find_tables
     devolverian listas vacias en TODOS los PDF; el resultado se veria como
     "ningun PDF tiene nada", que es distinguible de la salida real.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

RAIZ = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
DOC = os.path.join(RAIZ, "documentacion")
OUT = os.path.join(RAIZ, "experiments", "_s139_audit", "pdf_lectura", "out")
os.makedirs(OUT, exist_ok=True)

PRIORIDAD1 = [
    "sp426.5.pdf",
    "coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf",
    "coppola2012_jvgr_stromboli_10.1016-j.jvolgeores.2011.12.001.pdf",
    "THESIS_MASSIMETTI.pdf",
    "Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf",
    "Coppola_2019_supp_DataSheet.pdf",
]

# Patron de la capa de texto corrupta (regla A95): coma o digito donde el papel
# lleva un operador de comparacion. Ej: ",20.93" por "< -0.93"; "40" por "> 0".
RE_CORRUPTO = re.compile(r"(?<![0-9])[,](?=\s?[-\u2212]?\s?\d)")
RE_OPERADOR = re.compile(r"[<>\u2264\u2265\u03c3\u03bc\u00b1\u2211\u221a]")
RE_CAPTION_TAB = re.compile(r"\b(Table|Tabla|TABLE)\s*([0-9IVX]+)", re.I)
RE_CAPTION_FIG = re.compile(r"\b(Fig(?:ure|\.)?|Figura)\s*([0-9IVX]+)", re.I)
RE_EQ = re.compile(r"\(\s*\d{1,2}\s*\)\s*$", re.M)


def analizar(ruta):
    doc = fitz.open(ruta)
    paginas = []
    for i, page in enumerate(doc):
        txt = page.get_text("text")
        imgs = page.get_images(full=True)
        try:
            draws = page.get_drawings()
        except Exception:
            draws = []
        try:
            tablas = page.find_tables()
            n_tab_detect = len(tablas.tables)
        except Exception:
            n_tab_detect = -1  # no disponible en esta version
        caps_tab = sorted(set(m.group(0).strip() for m in RE_CAPTION_TAB.finditer(txt)))
        caps_fig = sorted(set(m.group(0).strip() for m in RE_CAPTION_FIG.finditer(txt)))
        n_eq = len(RE_EQ.findall(txt))
        n_corrupto = len(RE_CORRUPTO.findall(txt))
        n_operador = len(RE_OPERADOR.findall(txt))
        paginas.append(
            dict(
                pagina=i + 1,
                n_chars=len(txt),
                n_imagenes=len(imgs),
                n_dibujos=len(draws),
                n_tablas_detectadas=n_tab_detect,
                captions_tabla=caps_tab,
                captions_figura=caps_fig,
                n_ecuaciones_numeradas=n_eq,
                n_coma_sospechosa=n_corrupto,
                n_operadores_presentes=n_operador,
            )
        )
    r = dict(archivo=os.path.basename(ruta), n_paginas=len(doc), paginas=paginas)
    doc.close()
    return r


def main():
    resultados = []
    for nombre in PRIORIDAD1:
        ruta = os.path.join(DOC, nombre)
        if not os.path.exists(ruta):
            print("FALTA: %s" % nombre)
            continue
        r = analizar(ruta)
        resultados.append(r)
        con_img = sum(1 for p in r["paginas"] if p["n_imagenes"] > 0)
        con_tab = sum(1 for p in r["paginas"] if p["captions_tabla"])
        con_fig = sum(1 for p in r["paginas"] if p["captions_figura"])
        con_eq = sum(1 for p in r["paginas"] if p["n_ecuaciones_numeradas"] > 0)
        con_corr = sum(1 for p in r["paginas"] if p["n_coma_sospechosa"] > 0)
        sin_texto = sum(1 for p in r["paginas"] if p["n_chars"] < 100)
        print(
            "%-62s pag=%3d  img=%3d  capTab=%3d  capFig=%3d  eq=%3d  comaSosp=%3d  sinTexto=%d"
            % (r["archivo"][:62], r["n_paginas"], con_img, con_tab, con_fig, con_eq, con_corr, sin_texto)
        )
    destino = os.path.join(OUT, "inventario.json")
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(resultados, fh, ensure_ascii=False, indent=1)
    print("\nJSON -> %s" % destino)


if __name__ == "__main__":
    main()
