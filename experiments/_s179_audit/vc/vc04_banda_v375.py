# -*- coding: utf-8 -*-
"""Verificador VC, S179. vc04: C-montaje de VIIRS 375 con la banda post hoc, con los insumos de vc01 (via de D2 en DM)
contra el port C13 de V375-E (mismas carpetas que lista PROPUESTA_C_MONTAJE.md l. 24 a 25).

Mide: (a) rango de la diferencia relativa via contra el valor puntual del port en las pasadas que difieren a mas de
0,001 MW; (b) poder de la banda: cuantas pasadas con celdas alertadas quedarian fuera de la banda (con 0,001 MW de
holgura) si la via tuviera un sesgo de +2 %, +3 %, +5 % y -5 %.
PREGUNTAS. (1) Si la via fuera otra, lo veria? Solo en pasadas con celdas (se cuentan). (2) Muerto: 0 pareadas aborta.
Control positivo: sesgo 0 tiene que dar 0 fuera de la banda (la lectura dio C-montaje OK).
"""
import glob, json, sys
sys.stdout.reconfigure(encoding="utf-8")
INS = "D:/vrp-trabajo/temporales/s179-audit/vc/insumos/via"
CARP = ["D:/vrp-trabajo/temporales/s167_v375e_far", "D:/vrp-trabajo/temporales/s159_portes", "C:/vrp-trabajo/temporales/s162_v375"]
PLAT = {"VNP": "VIIRS_SNPP", "VJ1": "VIIRS_NOAA20", "VJ2": "VIIRS_NOAA21"}
via = {}
for f in glob.glob(INS + "/*.json"):
    d = json.load(open(f, encoding="utf-8"))
    for r in d["records"]:
        s = r["sensor"]
        if "2026-10-01" <= r["datetime_utc"][:10] <= "2026-10-16" and s.startswith("VIIRS") and not s.endswith("_750"):
            via[(d["volcano"], s, r["datetime_utc"][:16])] = r
ab = {}
for c in CARP:
    for f in glob.glob(c + "/**/resultados_VIIRS375_*.json", recursive=True):
        for e in json.load(open(f, encoding="utf-8")):
            if "2026-10-01" <= e["hora_utc"][:10] <= "2026-10-16" and "C13" in (e.get("port") or {}):
                ab.setdefault((e["volcan"], PLAT.get(e["granule"][:3]), e["hora_utc"][:16]), e)
par = [(k, via[k], ab[k]) for k in sorted(ab) if k in via]
print("pasadas del port en DM:", len(ab), "| pareadas con la via:", len(par))
if not par:
    sys.exit("ABORTA")
rel, con = [], 0
fuera = {g: 0 for g in (0.0, 0.02, 0.03, 0.05, -0.05)}
for k, r, e in par:
    p = e["port"]["C13"]
    vv = float((r.get("primary_cluster") or {}).get("vrp_mw") or 0.0)
    vp = float(p.get("vrp_mw") or 0.0)
    b = p.get("vrp_banda") or [vp, vp]
    if abs(vv - vp) > 1e-3 and vp:
        rel.append(round(100 * (vv - vp) / vp, 2))
    if r.get("anomaly_pixels") or p.get("pixeles"):
        con += 1
        for g in fuera:
            x = vv * (1 + g)
            fuera[g] += max(b[0] - x, x - b[1], 0.0) > 1e-3
print("diferencias a mas de 0,001 MW del valor puntual:", len(rel), "| relativas (%):", sorted(rel))
print("rango:", min(rel), "a", max(rel), "| |minima|:", min(abs(x) for x in rel))
print("pasadas con celdas alertadas:", con, "| fuera de la banda con sesgo g:", fuera)
