# -*- coding: utf-8 -*-
"""Para cada pasada que cambia (variante C): hay en su columna de Dist.png un marcador a +-0,6 km de la cifra OCR
(C_pres del verificador)? Sin marcador = la imagen contradice al OCR sin la ambiguedad de "dos marcadores, uno a la
cifra OCR" (VERIFICADOR.md §2). Tambien compara con la variante A (primera imagen)."""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
L = {}
for r in csv.DictReader(open(r"C:/Users/nmend/AppData/Local/Temp/claude/verifdist/v2/ocr_vs_serie.csv", encoding="utf-8")):
    L[({"ChillanNevadosde": "NevadosDeChillan"}.get(r["vol"], r["vol"]), r["t"][:16])] = r
PA = {(p["vol"], p["sensor"], p["t"]): p for p in csv.DictReader(open("pasadas_A.csv", encoding="utf-8"))}
from collections import Counter
c = Counter()
for p in csv.DictReader(open("pasadas_C.csv", encoding="utf-8")):
    if p["hoy_alerta"] == p["alt_alerta"]:
        continue
    r = L[(p["vol"], p["t"])]
    prot = p["hoy_prot"] != p["alt_prot"]
    a = PA.get((p["vol"], p["sensor"], p["t"]))
    a_txt = "A igual" if a and a["hoy_alerta"] != a["alt_alerta"] else f"A no cambia ({a['serie'] if a else '?'})"
    pres = r["C_pres"] == "True"
    c[(prot, p["nocturna"], pres)] += 1
    print(f"{'PROT' if prot else 'baja'} {p['vol']:16s} {p['t']} VRP {float(p['vrp']):6.2f} OCR {r['ocr']:>5s} columna {r['C_kmcol']:28s} "
          f"marcador a la cifra OCR: {'si' if pres else 'NO'} | {'noct' if p['nocturna']=='True' else 'DIURNA'} | {a_txt}")
print("\n(protegida, nocturna, marcador a la cifra OCR): n")
for k, v in sorted(c.items()):
    print("  ", k, v)
