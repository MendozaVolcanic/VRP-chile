# -*- coding: utf-8 -*-
"""S149. Cruce final: las sin_info V375 de noches con alerta, separadas por si MIROVA tiene veredicto
para ESA pasada (fila RUTINA CONS con VRP 0) y por posicion respecto del cumulo positivo de la noche.
Lee tabla.json (verificador S148), sin_info_v375.json (c3) y las_50.json (c1)."""
import json, collections, sys, io, statistics as st
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
T = json.loads((AQUI.parent / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
S = {(r["vol"], r["dt"]): r for r in json.loads((AQUI / "sin_info_v375.json").read_text(encoding="utf-8"))}
L = {(r["vol"], r["dt"]): r for r in json.loads((AQUI / "las_50.json").read_text(encoding="utf-8"))}
B = "_s146_ab_sin_test1"
npos = {(k.split("|")[0], k.split("|")[2][:10]) for k, v in T.items() if v[B]["lab"] == "pos"}
cl = [r for (v, d), r in S.items() if (v, d[:10]) in npos]
print("V375 sin_info en noche con alerta de MIROVA en el volcan (cualquier sensor)")
for nom, sel in (("todas", cl), ("publicadas por el control B", [r for r in cl if r["pB"]]),
                 ("apagadas por F", [r for r in cl if r["pB"] and not r["pF"]]), ("sobreviven a F", [r for r in cl if r["pF"]])):
    print("  %-28s n %3d | MIROVA miro esa pasada y dijo RUTINA VRP 0: %3d | sin fila: %3d" % (nom, len(sel), sum(r["rut"] for r in sel), sum(not r["rut"] for r in sel)))
rut = [r for r in cl if r["rut"]]
print("\nTasa de publicacion donde MIROVA dijo RUTINA en noche con alerta (n %d): B %.1f %% | F %.1f %%" % (
    len(rut), 100 * sum(r["pB"] for r in rut) / len(rut), 100 * sum(r["pF"] for r in rut) / len(rut)))
print("\nApagadas por F: veredicto de MIROVA cruzado con la posicion (separacion al cumulo positivo de la noche)")
for nom, f in (("MIROVA dijo RUTINA", True), ("sin fila", False)):
    s = [L[k] for k, r in S.items() if k in L and r["rut"] == f and L[k]["sep"] is not None]
    if s: print("  %-20s n %2d | <=0.4 km %2d | 0.4 a 2 km %2d | >2 km %2d | MW mediano %.3f" % (nom, len(s), sum(x["sep"] <= .4 for x in s),
          sum(.4 < x["sep"] <= 2 for x in s), sum(x["sep"] > 2 for x in s), st.median(x["dB"] for x in s)))
print("\nLas que no tienen fila, una por una:")
for k, r in sorted(S.items()):
    if k in L and not r["rut"]:
        x = L[k]; print("   %-22s %s | %.3f MW | z %.0f | sep %s km" % (k[0], k[1], x["dB"], x["z"], "%.2f" % x["sep"] if x["sep"] is not None else "-"))
