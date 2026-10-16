# -*- coding: utf-8 -*-
"""Palomar: pasadas OCR que la serie manda a la MISMA marca lejana de la misma columna. Una marca de Dist.png es una
pasada; si dos filas OCR de la misma noche reclaman la misma marca unica, a lo sumo una puede estar ahi (salvo marcas
superpuestas, que el lector funde). Cuenta cuantas pasadas que cambian comparten marca, y el minimo de cambios
compatible con la imagen (uno por marca)."""
import csv, sys
from collections import defaultdict
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")
P = [p for p in csv.DictReader(open("pasadas_C.csv", encoding="utf-8")) if p["hoy_alerta"] != p["alt_alerta"]]
g = defaultdict(list)
for p in P:
    g[(p["vol"], p["intervalo"], p["t"][:10])].append(p)
compartidas = 0; min_prot = 0; prot = 0; min_todas = 0
for k, ps in sorted(g.items()):
    np_ = sum(p["hoy_prot"] != p["alt_prot"] for p in ps)
    prot += np_
    min_todas += 1
    min_prot += 1 if np_ else 0   # cota inferior: a lo sumo una pasada por marca; si alguna es protegida, puede ser ella
    if len(ps) > 1:
        compartidas += len(ps)
        print(f"{k[0]:12s} noche {k[2]} marca {k[1]}: {len(ps)} pasadas -> " + ", ".join(
            f"{p['t'][11:]} ({float(p['vrp']):.2f} MW{', PROT' if p['hoy_prot'] != p['alt_prot'] else ''})" for p in ps))
print(f"\npasadas que cambian: {len(P)}; en marcas compartidas: {compartidas}; marcas distintas: {len(g)}")
print(f"protegidas que cambian: {prot}; cota inferior compatible con una pasada por marca: {min_prot}")
