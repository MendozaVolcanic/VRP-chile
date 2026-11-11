# -*- coding: utf-8 -*-
"""Cuantas noches de sombra tenia la via de MODIS cuando se encendio en produccion (2026-11-02 20:11:43 UTC).
Lee data/sombra_codigo_mirova/*.json de main 438a60a1e. Control de instrumento vivo: total de records de la via
por sensor (centenas). Denominador: records con via_codigo_mirova True de los 11 Tier A."""
import io, sys, os, json, glob, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
tot, primero, noches = collections.Counter(), {}, collections.Counter()
for f in sorted(glob.glob(os.path.join(BASE, "data", "sombra_codigo_mirova", "*.json"))):
    for r in json.load(open(f, encoding="utf-8"))["records"]:
        if r.get("via_codigo_mirova") is not True: continue
        s = r.get("sensor", ""); b = "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
        tot[b] += 1
        v = (r.get("first_processed_utc") or r.get("processed_utc") or "", r["datetime_utc"], os.path.basename(f))
        if b not in primero or v < primero[b]: primero[b] = v
        if b == "MODIS": noches[r["datetime_utc"][:10]] += 1
print("records de la via en la sombra, por sensor:", dict(tot))
for b, v in sorted(primero.items()): print(f"  primer record de {b}: escrito {v[0]}, pasada {v[1]} ({v[2]})")
print("fechas de observacion con records MODIS de la via en la sombra:", dict(sorted(noches.items())))
print("encendido de produccion: 2026-11-02T20:11:43Z -> noches de sombra de MODIS anteriores al encendido:",
      sum(1 for n in noches if n < "2026-11-02"))
