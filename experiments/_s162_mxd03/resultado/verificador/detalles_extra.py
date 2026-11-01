# -*- coding: utf-8 -*-
"""Verificador: detalles que faltaban tras anomalias_desplazamiento.py: la protegida con MxD03 de relleno, los pares de M
que cambian mas de 30 %, y el tamano del corrimiento del pixel del crater por tramo (para leer el 10-16 km del borde).
Uso: python -I detalles_extra.py <art> <poblacion.json>"""
import glob, json, math, statistics, sys, collections
from pathlib import Path
ART, POB = Path(sys.argv[1]), Path(sys.argv[2])
pob = json.load(open(POB, encoding="utf-8"))
pobf = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
ok = []
for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") == "record" and r.get("estado") == "ok":
            r.update({k: v for k, v in pobf[(r["vol"], r["dt"])].items() if k not in r}); ok.append(r)
print("== protegida/alertas con MxD03 de relleno")
for f in ok:
    if (f.get("n_fill_mxd03") or 0) > 0 and f["lab"] in ("protegida", "bajo1"):
        print("  ", f["vol"], f["dt"], f["lab"], "z=%.1f" % f["z"], "n_fill", f["n_fill_mxd03"], "pub K/X", f["pub"]["K"], f["pub"]["X"],
              "pc_vrp K/X", f["brazos"]["K"]["pc_vrp"], f["brazos"]["X"]["pc_vrp"], "pc_dist K/X", f["brazos"]["K"]["pc_dist"], f["brazos"]["X"]["pc_dist"], "desplaz km", f["desplazamiento"]["km"])
print("\n== M: pares con |X/K - 1| > 30 % (K, X, MIROVA, z)")
pares = [f for f in ok if f["lab"] in ("protegida", "bajo1") and f["pub"]["K"] == 1 and f["pub"]["X"] == 1
         and (f["brazos"]["K"] or {}).get("pc_vrp") and (f["brazos"]["X"] or {}).get("pc_vrp") and f.get("vrp_mirova")]
for f in sorted(pares, key=lambda f: -abs(f["brazos"]["X"]["pc_vrp"] / f["brazos"]["K"]["pc_vrp"] - 1)):
    k, x, m = f["brazos"]["K"]["pc_vrp"], f["brazos"]["X"]["pc_vrp"], f["vrp_mirova"]
    if abs(x / k - 1) > 0.3:
        print("   %s %s %s z=%.1f K=%.3f X=%.3f MIROVA=%.2f X/K=%.2f | |log X/M|-|log K/M| = %+.3f (negativo = X mas cerca de MIROVA) | n_anom K/X %s/%s" % (
            f["vol"], f["dt"], f["lab"], f["z"], k, x, m, x / k, abs(math.log10(x / m)) - abs(math.log10(k / m)), f["brazos"]["K"]["n_anom"], f["brazos"]["X"]["n_anom"]))
d = [abs(math.log10(f["brazos"]["X"]["pc_vrp"] / f["vrp_mirova"])) - abs(math.log10(f["brazos"]["K"]["pc_vrp"] / f["vrp_mirova"])) for f in pares]
print("   d < 0 (X mas cerca de MIROVA): %d | d > 0: %d | d = 0: %d | suma d: %+.3f" % (sum(1 for x in d if x < 0), sum(1 for x in d if x > 0), sum(1 for x in d if x == 0), sum(d)))
print("\n== corrimiento del pixel del crater (km) por tramo de cenit y lado, mediana (n), sin los 2 absurdos")
tab = collections.defaultdict(list)
for f in ok:
    if f["desplazamiento"]["km"] < 1000:
        tab[(f["tramo"], f["lado"])].append(f["desplazamiento"]["km"])
for k in sorted(tab):
    v = sorted(tab[k]); print("   %-6s %-5s mediana %.2f p90 %.2f max %.2f (n %d)" % (k[0], k[1], statistics.median(v), v[int(0.9 * len(v))], v[-1], len(v)))
