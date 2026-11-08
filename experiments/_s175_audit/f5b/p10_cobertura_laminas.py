# -*- coding: utf-8 -*-
"""P10 (F5b): días sin lámina Latest10NTI por volcán y sensor en el índice del archivo (copia de la ola 0), del 2026-09-22
al 2026-11-06, y las láminas MODIS de Láscar alrededor del 25-sep y del 8-oct. Sólo lee el índice; no baja nada.
Pregunta 2: el conteo de días con lámina (35 a 44 de 46) muestra que el instrumento ve días presentes y ausentes."""
import csv, collections, datetime as dt, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = [r for r in csv.DictReader(open(r"C:\Users\nmend\vrp-temporales\s175_audit\insumos\png_index.csv", encoding="utf-8")) if r["kind"] == "Latest10NTI"]
dias = [(dt.date(2026, 9, 22) + dt.timedelta(d)).isoformat() for d in range(46)]
have = collections.defaultdict(set)
for r in rows:
    if r["last_modified_utc"][:10] >= "2026-09-22":
        have[(r["volcano"], r["sensor"])].add(r["last_modified_utc"][:10])
for k in sorted(have):
    falt = [d for d in dias if d not in have[k]]
    print(k, "días con lámina", len(have[k]), "de", len(dias), "faltan", len(falt), falt)
print("Láscar MODIS, láminas con last_modified entre el 24-sep y el 27-sep y entre el 7-oct y el 10-oct:")
for r in rows:
    if r["volcano"] == "Lascar" and r["sensor"] == "MODIS" and (("2026-09-24" <= r["last_modified_utc"][:10] <= "2026-09-27") or ("2026-10-07" <= r["last_modified_utc"][:10] <= "2026-10-10")):
        print("  ", r["last_modified_utc"], r["png_path"])
print("última captura del índice:", max(r["captured_at_utc"] for r in rows))
