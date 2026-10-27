# -*- coding: utf-8 -*-
"""Verificador: tres cosas que el censo propio dejo a la vista y que el evaluador del autor no mira.
1. El desplazamiento en el crater (interp - MxD03) llega a 103.470 km en algun record: fisicamente imposible
   (el corrimiento real es de 1 a 6 km). Que records son, que cenit, cuantos pixeles de relleno trae su MxD03, si
   tienen nulos R (que se trasladan ESE modulo) y como quedaron sus brazos.
2. MxD03 con relleno (n_fill_mxd03 > 0): donde MxD03 no tiene lat/lon, X pierde el pixel y K no. Cuantos records y
   si alguno decide (alerta, negativo publicado, cambio K->X).
3. M con mas decimales, y la protegida fragil (5 R la apagan).
Uso: python -I anomalias_desplazamiento.py <carpeta artefactos> <poblacion.json>
"""
import collections
import glob
import json
import math
import statistics
import sys
from pathlib import Path

ART, POB = Path(sys.argv[1]), Path(sys.argv[2])
NULOS = ["R%02d" % k for k in range(20)]
pob = json.load(open(POB, encoding="utf-8"))
pobf = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
ok = []
for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") == "record" and r.get("estado") == "ok":
            r.update({k: v for k, v in pobf[(r["vol"], r["dt"])].items() if k not in r})
            ok.append(r)

print("== 1. DESPLAZAMIENTO EN EL CRATER (km) por tramo")
for lo, hi in ((0, 1), (1, 3), (3, 6), (6, 10), (10, 100), (100, 1e9)):
    sel = [f for f in ok if lo <= f["desplazamiento"]["km"] < hi]
    print("   [%g, %g): %d records" % (lo, hi, len(sel)), "| z mediana %.1f" % statistics.median(f["z"] for f in sel) if sel else "")
raros = sorted([f for f in ok if f["desplazamiento"]["km"] > 10], key=lambda f: -f["desplazamiento"]["km"])
print("   records con desplazamiento > 10 km:", len(raros))
for f in raros:
    d = f["desplazamiento"]
    print("   ", f["vol"], f["dt"], f["sensor"], "z=%.1f" % f["z"], f["lado"], f["lab"], "| km=%.1f dn=%.1f de=%.1f linea=%d frame=%d" % (
        d["km"], d["dn_km"], d["de_km"], d["linea"], d["frame"]), "| n_fill_mxd03=%d" % f["n_fill_mxd03"], "| r_nulos", f["r_nulos"],
        "| pub K/X", f["pub"]["K"], f["pub"]["X"], "| K None", f["brazos"]["K"] is None, "X None", f["brazos"]["X"] is None,
        "| R None:", sum(1 for b in NULOS if f["r_nulos"] and f["brazos"].get(b) is None), "| R pub:", sum(f["pub"].get(b, 0) for b in NULOS),
        "| km_aplicado R00:", (f["nulos"] or [{}])[0].get("km_aplicado") if f["r_nulos"] else "-",
        "| hash X!=K", f["hash_grilla"]["X"] != f["hash_grilla"]["K"])
print("   de esos, con cambio de publicacion K->X:", sum(1 for f in raros if f["pub"]["K"] != f["pub"]["X"]),
      "| alertas:", sum(1 for f in raros if f["lab"] in ("protegida", "bajo1")), "| K publica:", sum(f["pub"]["K"] for f in raros))

print("\n== 2. MxD03 CON RELLENO (n_fill_mxd03 > 0)")
rell = [f for f in ok if (f.get("n_fill_mxd03") or 0) > 0]
print("   records:", len(rell), "| granulos:", len({f["clave"] for f in rell}), "| por etiqueta:", dict(collections.Counter(f["lab"] for f in rell)))
print("   n_fill (pixeles) por granulo:", sorted({(f["clave"], f["n_fill_mxd03"]) for f in rell}, key=lambda x: -x[1])[:12])
print("   de esos: K publica", sum(f["pub"]["K"] for f in rell), "| X publica", sum(f["pub"]["X"] for f in rell),
      "| cambio K->X", [(f["vol"], f["dt"], f["lab"], f["pub"]["K"], f["pub"]["X"]) for f in rell if f["pub"]["K"] != f["pub"]["X"]],
      "| con desplazamiento > 10 km:", sum(1 for f in rell if f["desplazamiento"]["km"] > 10))
print("   interseccion raros (>10 km) y relleno:", sum(1 for f in raros if (f.get("n_fill_mxd03") or 0) > 0), "de", len(raros))

print("\n== 3. BRAZOS R None (calculate_vrp devolvio None en una traslacion)")
rn = [f for f in ok if f["r_nulos"] and any(f["brazos"].get(b) is None for b in NULOS)]
for f in rn:
    print("   ", f["vol"], f["dt"], "z=%.1f" % f["z"], f["lab"], "| desplazamiento km=%.2f" % f["desplazamiento"]["km"],
          "| R None:", [b for b in NULOS if f["brazos"].get(b) is None], "| K None", f["brazos"]["K"] is None, "| pub K/X", f["pub"]["K"], f["pub"]["X"])

print("\n== 4. M con decimales")
pares = [(f["brazos"]["K"]["pc_vrp"], f["brazos"]["X"]["pc_vrp"], f["vrp_mirova"]) for f in ok
         if f["lab"] in ("protegida", "bajo1") and f["pub"]["K"] == 1 and f["pub"]["X"] == 1
         and (f["brazos"]["K"] or {}).get("pc_vrp") and (f["brazos"]["X"] or {}).get("pc_vrp") and f.get("vrp_mirova")]
d = sorted(abs(math.log10(x / m)) - abs(math.log10(k / m)) for k, x, m in pares)
rat = sorted(x / k for k, x, _ in pares)
print("   n=%d | mediana d=%.6f | d p10=%.4f p90=%.4f | X/K mediana=%.5f p10=%.4f p90=%.4f | X>K: %d, X<K: %d, X=K: %d" % (
    len(pares), statistics.median(d), d[int(0.1 * len(d))], d[int(0.9 * len(d))], statistics.median(rat), rat[int(0.1 * len(rat))],
    rat[int(0.9 * len(rat))], sum(1 for k, x, _ in pares if x > k), sum(1 for k, x, _ in pares if x < k), sum(1 for k, x, _ in pares if x == k)))
print("   |X/K - 1| > 10 %%: %d | > 30 %%: %d" % (sum(1 for r in rat if abs(r - 1) > 0.1), sum(1 for r in rat if abs(r - 1) > 0.3)))

print("\n== 5. PROTEGIDA FRAGIL")
for f in ok:
    if f["lab"] == "protegida" and f["r_nulos"]:
        apag = [b for b in NULOS if f["pub"].get(b) == 0]
        if apag:
            print("   ", f["vol"], f["dt"], "z=%.1f" % f["z"], f["lado"], "expuesta" if f.get("expuesta") else "", "| R que la apagan:", apag,
                  "| pc_dist K/X: %.2f/%.2f inner %s | pc_vrp K/X: %s/%s | desplaz %.2f km" % (
                      f["brazos"]["K"]["pc_dist"], f["brazos"]["X"]["pc_dist"], f["inner"], f["brazos"]["K"]["pc_vrp"], f["brazos"]["X"]["pc_vrp"], f["desplazamiento"]["km"]))

print("\n== 6. LAS 4 PROTEGIDAS EXPUESTAS (§5) en K y X")
for f in ok:
    if f["lab"] == "protegida" and f.get("expuesta"):
        print("   ", f["vol"], f["dt"], "z=%.1f" % f["z"], f["lado"], "| pub K/X", f["pub"]["K"], f["pub"]["X"],
              "| pc_dist K/X: %.2f/%.2f (inner %s) | pc_vrp K/X: %s/%s | MIROVA %s" % (
                  f["brazos"]["K"]["pc_dist"], f["brazos"]["X"]["pc_dist"], f["inner"], f["brazos"]["K"]["pc_vrp"], f["brazos"]["X"]["pc_vrp"], f["vrp_mirova"]))

print("\n== 7. LAS 2 PROTEGIDAS QUE K NO PUBLICA")
for f in ok:
    if f["lab"] == "protegida" and f["pub"]["K"] == 0:
        print("   ", f["vol"], f["dt"], "z=%.1f" % f["z"], f["lado"], "| pub X", f["pub"]["X"], "| K:", f["brazos"]["K"] and {k: f["brazos"]["K"][k] for k in ("pc_vrp", "pc_dist", "dc", "n_anom")},
              "| X:", f["brazos"]["X"] and {k: f["brazos"]["X"][k] for k in ("pc_vrp", "pc_dist", "dc", "n_anom")}, "| MIROVA", f["vrp_mirova"])
