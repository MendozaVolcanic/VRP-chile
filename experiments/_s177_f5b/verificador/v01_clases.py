# -*- coding: utf-8 -*-
"""V177 v01. Pregunta: las cifras de clases antes/despues de INFORME sec. 4 salen con un selector escrito aparte?
Si mi codigo discrepa de s02/s03, algo de los dos esta mal. Control: mi regla A debe dar las lat/lon de p8_clases.json (303/303).
Salida: stdout y v01_manchas.pkl para los siguientes scripts."""
import json, sys, collections, pickle, os
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import *

rows = []
for x in P8:
    if not x.get("png") or "geometria" not in x:
        continue
    g = grilla(x["vol"], x["b"])
    P = panel(x, g)
    A = mancha(P, g, "A", False)
    C1 = mancha(P, g, "B", False)
    C2 = mancha(P, g, "B", True)
    dist = x.get("dist_tabla_km")
    dist = float(dist) if dist not in (None, "") else None
    o = dict(vol=x["vol"], b=x["b"], sensor=x["sensor"], dt=x["dt"], prot=x["protegida"], vrp=float(x["vrp_mirova"]), dist=dist, fuente=x["fuente_dist"],
             pt=(float(x["our_lat"]), float(x["our_lon"])), claseF5b=x["clase"].rstrip("?"), png=x["png"], panel=x["panel"], F5b=(x.get("png_lat"), x.get("png_lon")),
             geom=x["geometria"], celda=g["celda"], A=resumen(A, g), C1=resumen(C1, g), C2=resumen(C2, g), x=x)
    rows.append(o)
pickle.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "v01_manchas.pkl"), "wb"))
print("con lamina:", len(rows))
rep = sum(abs(o["A"]["la"] - o["F5b"][0]) < 2e-5 and abs(o["A"]["lo"] - o["F5b"][1]) < 2e-5 for o in rows)
print("mi regla A = lat/lon de p8_clases.json:", rep, "de", len(rows))
S2 = {(o["vol"], o["sensor"], o["dt"]): o for o in json.load(open(F + r"\salidas\s02_manchas.json", encoding="utf-8"))}
for k in ("C1", "C2"):
    same = 0
    dif = []
    for o in rows:
        q = S2[(o["vol"], o["sensor"], o["dt"])][k]
        if abs(o[k]["la"] - q["lat"]) < 2e-5 and abs(o[k]["lo"] - q["lon"]) < 2e-5 and o[k]["px"] == q["px_principal"] and o[k]["ncomp"] == q["n_comps"]:
            same += 1
        else:
            dif.append((o["vol"], o["sensor"], o["dt"]))
    print(f"mi {k} = s02 (lat, lon, px, n comps): {same} de {len(rows)}", dif[:5])


def cl(o, v):
    g = grilla(o["vol"], o["b"])
    if v == "C1":
        return clase(o["C1"], o["pt"], o["dist"], o["b"], o["celda"], g, "cent")
    if v == "C2p":
        return clase(o["C2"], o["pt"], o["dist"], o["b"], o["celda"], g, "any")
    if v == "C2_cc":
        return clase(o["C2"], o["pt"], o["dist"], o["b"], o["celda"], g, "cent")
    if v == "C2_nc":
        return clase(o["C2"], o["pt"], o["dist"], o["b"], o["celda"], g, "any", True)


gr = [("Todos", lambda o: True, 2), ("Chillan V375", lambda o: o["vol"] == CH and o["b"] == "VIIRS375", 0), ("Chillan V750", lambda o: o["vol"] == CH and o["b"] == "VIIRS750", 0),
      ("Chillan MODIS", lambda o: o["vol"] == CH and o["b"] == "MODIS", 1), ("Chillan prot V375", lambda o: o["vol"] == CH and o["b"] == "VIIRS375" and o["prot"] == "True", 0),
      ("Chillan prot V750", lambda o: o["vol"] == CH and o["b"] == "VIIRS750" and o["prot"] == "True", 0), ("Chillan prot MODIS", lambda o: o["vol"] == CH and o["b"] == "MODIS" and o["prot"] == "True", 1),
      ("Resto V375", lambda o: o["vol"] != CH and o["b"] == "VIIRS375", 0)]
VS = ("F5b_guardada", "C1", "C2p", "C2_cc", "C2_nc")
print(f"{'universo':20s} n    " + " ".join(f"{v:>14s}" for v in VS))
for nom, f, ex in gr:
    s = [o for o in rows if f(o)]
    cc = []
    for v in VS:
        c = collections.Counter(o["claseF5b"] if v == "F5b_guardada" else cl(o, v) for o in s)
        c["iv"] += ex
        cc.append(f"{c['i']}/{c['iii']}/{c['iv']}")
    print(f"{nom:20s} {len(s) + ex:4d} " + " ".join(f"{v:>14s}" for v in cc))
print("\nCentroide ajustado a celda contra continuo, Chillan, sin control:")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    s = [o for o in rows if o["vol"] == CH and o["b"] == b]
    dc = np.array([hav(o["C2"]["la"], o["C2"]["lo"], *o["pt"]) for o in s])
    dcc = np.array([hav(o["C2"]["la_c"], o["C2"]["lo_c"], *o["pt"]) for o in s])
    print(f"  {b} n={len(s)} d celda p50 {np.median(dc):.3f} max {dc.max():.2f} i={int((dc <= TOL[b]).sum())}; d continuo p50 {np.median(dcc):.3f} max {dcc.max():.2f} i={int((dcc <= TOL[b]).sum())}")
