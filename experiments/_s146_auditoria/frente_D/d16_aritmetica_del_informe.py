# -*- coding: utf-8 -*-
"""d16: los numeros derivados que el informe usa y que no salian directo de otro script: fechas exactas del hueco del corpus,
fraccion de pares del libro que son del regimen previo, y 921-44. Instrumento: (1) roto => fechas None. (2) lee los JSON de d02/d05."""
import io, sys, json
from datetime import date, timedelta
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); out = {}
for v in VOLS:
    fs = sorted({r["datetime_utc"][:10] for r in D[v]}); huecos = []
    for a, b in zip(fs, fs[1:]):
        da = date(*map(int, a.split("-"))); db = date(*map(int, b.split("-")))
        if (db - da).days > 3: huecos.append((str(da + timedelta(days=1)), str(db - timedelta(days=1)), (db - da).days - 1))
    out[v] = huecos
for v, h in out.items(): print(v, h)
d5 = json.load(open("d05_libro_por_regimen.json")); a = d5["previo(01-01..08-28)"]["ratio_global_pc(n,mediana)"][0]; b = d5["libro(2026 entero)"]["ratio_global_pc(n,mediana)"][0]
print("pares previos / pares libro:", a, b, round(100*a/b, 1))
t = json.load(open("d02_noches_A94_A98.json"))["total"]; print("NOCT_total - NOCT_sin_nada =", t["NOCT_total"] - t["NOCT_sin_nada"], "| publica", t["NOCT_publica"])
json.dump(out, open("d16_huecos.json", "w"), indent=1)
