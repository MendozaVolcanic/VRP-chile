# -*- coding: utf-8 -*-
"""Records cuyo pixel MxD03 mas cercano al vent esta en el borde del granulo (linea 0/2029: borde de la traza; frame
0/1353: borde del barrido). P1: si el crater estuviera dentro, el pixel mas cercano no estaria en el borde salvo
coincidencia (nulo: fraccion esperada de records con el crater en una linea/frame del borde ~ 2/2030 + 2/1354 = 0,25 %).
P2: el conteo usa el indice persistido por el arnes, no la distancia (no persistida): SIN DATO de cuan lejos queda.
Para los de borde de traza, ¿existe otro record del mismo volcan en el granulo vecino (+-5 min)? Uso: python -I verif_borde.py"""
import glob, io, json, sys, collections
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ART = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\tandas")
ok = []
for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") == "record" and r.get("estado") == "ok": ok.append(r)
idx = collections.defaultdict(list)
for r in ok:
    idx[r["vol"]].append(datetime.strptime(r["dt"], "%Y-%m-%d %H:%M"))
traza = [r for r in ok if r["desplazamiento"]["linea"] in (0, 2029)]
barr = [r for r in ok if r["desplazamiento"]["frame"] in (0, 1353) and r["desplazamiento"]["linea"] not in (0, 2029)]
print("n records %d | esperado por azar (crater dentro, uniforme) en linea 0/2029: %.1f, en frame 0/1353: %.1f" % (len(ok), len(ok) * 2 / 2030, len(ok) * 2 / 1354))
print("borde de traza (linea 0/2029): %d | lab %s" % (len(traza), dict(collections.Counter(r["lab"] for r in traza))))
vec = 0
for r in traza:
    t = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
    vec += any(timedelta(0) < abs(u - t) <= timedelta(minutes=5) for u in idx[r["vol"]])
print("   con un record del mismo volcan en el granulo vecino (+-5 min) en la poblacion: %d de %d" % (vec, len(traza)))
print("borde de barrido (frame 0/1353): %d | lab %s | cenit min %.1f mediana %.1f" % (len(barr), dict(collections.Counter(r["lab"] for r in barr)),
      min(r["z"] for r in barr), sorted(r["z"] for r in barr)[len(barr) // 2]))
print("anillo K en borde de barrido: mediana %d min %d | en el resto con z>60: mediana %d" % (
    sorted(r["brazos"]["K"]["diag_n_bg_anillo"] for r in barr if r["brazos"]["K"])[len(barr) // 2],
    min(r["brazos"]["K"]["diag_n_bg_anillo"] for r in barr if r["brazos"]["K"]),
    sorted(r["brazos"]["K"]["diag_n_bg_anillo"] for r in ok if r["brazos"]["K"] and r["z"] > 60 and r not in barr)[sum(1 for r in ok if r["brazos"]["K"] and r["z"] > 60 and r not in barr) // 2]))
print("publican en K o X: traza %d, barrido %d" % (sum(1 for r in traza if r["pub"]["K"] or r["pub"]["X"]), sum(1 for r in barr if r["pub"]["K"] or r["pub"]["X"])))
