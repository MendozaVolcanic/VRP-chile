# -*- coding: utf-8 -*-
"""Verificador CDE, D1: números de MOD-D contra la población congelada de S159 (poblacion_completa.json, blob cb48ddd4)
y contra los resultados del lote 39712862945. Denominador: MODIS, 2026-03-01 a 2026-10-21 sin el 17 al 20 de octubre,
pasadas que deciden. Uso: python -I verif_d1_numeros.py --pob <poblacion_completa.json> --art <run_39712862945>"""
import argparse, collections, glob, json, statistics as st, sys
sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser(); ap.add_argument("--pob", required=True); ap.add_argument("--art", required=True)
a = ap.parse_args()
pob = json.load(open(a.pob, encoding="utf-8"))
EX = ("2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
d = [o for o in pob["pasadas"] if o["b"] == "MODIS" and o["hora_utc"][:10] not in EX and o["decide"]]
pos = [o for o in d if o["lab"] == "pos"]
print("alertas MODIS:", len(pos), dict(collections.Counter(o["volcan"] for o in pos)), "(MOD-D: 80 de 92 Lascar)")
ch = [o for o in pos if o["volcan"] == "NevadosDeChillan"]
r = sorted(round(o["pc_vrp"] / o["mirova_vrp"], 3) for o in ch if o["pub_prod"] and o.get("pc_vrp"))
print("Chillan: alertas", len(ch), "protegidas", sum(bool(o["protegida"]) for o in ch), "K publica", sum(bool(o["pub_prod"]) for o in ch),
      "| K/MIROVA:", r, "mediana", round(st.median(r), 3), "n", len(r), "(MOD-D: 0,485 n 7)")
n = s = px = 0
for f in glob.glob(a.art + "/s159-portes-MODIS-*/resultados_MODIS_*.json"):
    for rr in json.load(open(f, encoding="utf-8")):
        if rr.get("estado") == "ok":
            n += 1; v = (rr.get("saturados") or {}).get("b22_nan_con_b21") or 0; s += v > 0; px += v
print("S159 ok:", n, "| pasadas con B22 NaN y B21 valida:", s, "| pixeles:", px, "(MOD-D: 0 de 149)")
