# -*- coding: utf-8 -*-
"""d03: cobertura del corpus por volcan y mes (dias con al menos un record). Base para juzgar toda ventana 'toda la serie'.
Instrumento: (1) roto => todo 0, visible. (2) control: total de records = 60037 aprox (dlib)."""
import io, sys, json
from collections import defaultdict
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); meses = sorted({r["datetime_utc"][:7] for v in VOLS for r in D[v]})
tab = {v: defaultdict(set) for v in VOLS}
for v in VOLS:
    for r in D[v]: tab[v][r["datetime_utc"][:7]].add(r["datetime_utc"][:10])
print("%-8s" % "mes" + "".join("%6s" % v[:5] for v in VOLS))
out = {}
for m in meses:
    print("%-8s" % m + "".join("%6d" % len(tab[v][m]) for v in VOLS)); out[m] = {v: len(tab[v][m]) for v in VOLS}
json.dump(out, open("d03_cobertura_corpus.json", "w"), indent=1)
print("total records", sum(len(D[v]) for v in VOLS))
