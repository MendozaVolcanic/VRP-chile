# -*- coding: utf-8 -*-
"""Control del caso ambiguo. Patron: en la columna de Dist.png hay un marcador a la cifra OCR (+-0,6 km) y otro
lejano (> limite + 0,6). En las filas OCR con la MISMA pasada en la tabla y la tabla dentro del limite (verdad =
crater), cuantas veces la serie dice "lejos" con ese patron? Si lo dice a menudo, el patron no distingue y los
cambios con ese patron en las filas solo OCR no se pueden atribuir al OCR. Ventana 2026-06-13 a 2026-10-08, VIIRS 375,
variante C. Tambien el patron sin marcador a la cifra OCR."""
import csv, ast, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
LIM = {"Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0, "Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0}
lim = lambda v: LIM.get(v, 5.0)
c = Counter()
for r in csv.DictReader(open(r"C:/Users/nmend/AppData/Local/Temp/claude/verifdist/v2/ocr_vs_serie.csv", encoding="utf-8")):
    if not ("2026-06-13" <= r["t"][:10] <= "2026-10-08") or r["sensor"] != "VIIRS375" or not r["C_clase"]:
        continue
    if r["C_dec"] not in ("cerca", "lejos"):
        continue
    U = lim(r["vol"]); col = ast.literal_eval(r["C_kmcol"]); o = min(float(r["ocr"]), 25)
    near = any(abs(m - o) <= 0.6 for m in col); far = any(m > U + 0.6 for m in col)
    patron = ("cifra OCR + lejano" if near and far else "solo cifra OCR/cercanos" if near else
              "sin cifra OCR, con lejano" if far else "sin cifra OCR, sin lejano")
    if r["d_tab"]:
        if float(r["d_tab"]) > U:      # control: solo verdad = crater (el OCR ALERTA de la ventana)
            continue
        pob = "CONTROL (tabla = crater)"
    else:
        if r["tipo"] != "ALERTA_TERMICA_OCR":
            continue
        pob = "solo OCR ALERTA"
    c[(pob, patron, r["C_dec"])] += 1
for pob in ("CONTROL (tabla = crater)", "solo OCR ALERTA"):
    print(f"== {pob}")
    for patron in ("cifra OCR + lejano", "solo cifra OCR/cercanos", "sin cifra OCR, con lejano", "sin cifra OCR, sin lejano"):
        n_l, n_c = c[(pob, patron, "lejos")], c[(pob, patron, "cerca")]
        if n_l + n_c:
            print(f"   {patron:28s} serie dice lejos {n_l:3d} de {n_l + n_c:3d} ({100 * n_l / (n_l + n_c):.0f} %)")
