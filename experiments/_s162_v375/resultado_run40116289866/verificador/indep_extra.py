# -*- coding: utf-8 -*-
"""Verificador S162 V375: comprobaciones extra (geometria de C13/M14, seleccion por volcan en T, composite en O por volcan,
magnitud de lo recuperado por C13, dayflag, tramo)."""
import collections, io, json, sys, math
from pathlib import Path
import numpy as np, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.argv = [sys.argv[0]]
exec(open(Path(__file__).with_name("indep_decision.py"), encoding="utf-8").read().split("rows162 = ")[0].replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\"utf-8\")", "pass"))
from pyproj import Transformer

ver = {v["name"]: v for v in vy}
# 1. geometria
print("== 1. geometria C13/M14 sobre las pasadas S162 ok")
bad = []
cnt = collections.Counter()
for i, o in sorted(obj.items()):
    if o["lote"] != "S162":
        continue
    r = r162.get(i)
    if not r or r["estado"] != "ok":
        continue
    g = o["grilla"]; v = ver[o["volcan"]]
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    xc, yc = t.transform(v.get("vent_lon", v["lon"]), v.get("vent_lat", v["lat"]))
    if abs(xc - r["crater_xy"][0]) > 1 or abs(yc - r["crater_xy"][1]) > 1:
        bad.append(("crater_xy distinto", i, xc, yc, r["crater_xy"]))
    n = g["n"]
    xs = g["ul_x"] + g["celda"] * (np.arange(n) + 0.5)
    ys = g["ul_y"] - g["celda"] * (np.arange(n) + 0.5)
    j0 = int(np.argmin(abs(xs - xc))); i0 = int(np.argmin(abs(ys - yc)))
    for b, h in (("C13", 6), ("C21", 10), ("M13", 6), ("M21", 10)):
        cx, cy = (xc, yc) if b[0] == "C" else (g["X0"], g["Y0"])
        jj = int(np.argmin(abs(xs - cx))); ii = int(np.argmin(abs(ys - cy)))
        p = r["port"][b]
        cnt[(b, "n_roi2", p["n_roi2"])] += 1
        for q in p["pixeles"]:
            if q[2] == 2 and not (abs(q[0] - ii) <= h and abs(q[1] - jj) <= h):
                bad.append((b, "pixel box=2 fuera de la caja", i, q[:4]))
            if q[2] != 2 and abs(q[0] - ii) <= h and abs(q[1] - jj) <= h and b in ("C13", "C21"):
                bad.append((b, "pixel dentro de la caja con box!=2", i, q[:4]))
print("   n_roi2 por brazo:", {k: v for k, v in sorted(cnt.items())})
print("   anomalias:", bad[:10], len(bad))
print("   dayflag en ok S162:", collections.Counter(r162[i]["dayflag"] for i in r162 if r162[i]["estado"] == "ok"))
print("   sunglint min/max:", min(r162[i]["sunglint"] for i in r162 if r162[i]["estado"] == "ok"), max(r162[i]["sunglint"] for i in r162 if r162[i]["estado"] == "ok"))

# 2. seleccion por volcan en T, recalculada
print("\n== 2. eleccion por volcan en T (union, mis pesos)")
W = pesos(rows)
ORDEN = ("PIX7", "M13", "C13", "M14", "C14", "M21", "C21", "SENS_PT", "CIRC", "SENS")
elec = {}
for vol in sorted({x["vol"] for x in rows}):
    tv = [x for x in rows if x["vol"] == vol and x["tramo"] == "T"]
    cand = []
    for b in BRAZOS:
        if any(x["c"] == "pos_prot" and not x["pub"][b] for x in tv):
            continue
        e = sum(W[id(x)] for x in tv if err(x, b))
        cand.append((round(e, 6), 0 if b == "M14" else 1, ORDEN.index(b), b))
    c = sorted(cand)
    elec[vol] = c[0][3] if tv and c else "M14"
    print(f"   {vol:22s} -> {elec[vol]:8s} (T: {len(tv)} pasadas) top3 {c[:3]}")
for x in rows:
    x["pub"]["POR_VOLCAN"] = x["pub"][elec[x["vol"]]]
    x["vrp"]["POR_VOLCAN"] = x["vrp"][elec[x["vol"]]]
O = [x for x in rows if x["tramo"] != "T"]
print("   composite en O vs M14:", p2(O, W, "POR_VOLCAN", "M14")[:3], "vs K:", p2(O, W, "POR_VOLCAN", "K")[:3])
for vv in ("PuyehueCordonCaulle", "Tupungatito"):
    sub = [x for x in O if x["vol"] == vv]
    print(f"   composite en O solo {vv}:", p2(sub, W, "POR_VOLCAN", "M14")[:3], "(pasadas O:", len(sub), ")")
sub = [x for x in O if x["vol"] not in ("PuyehueCordonCaulle", "Tupungatito")]
print("   composite en O fuera de PCC y Tup (deberia ser identico a M14):", p2(sub, W, "POR_VOLCAN", "M14")[:3])
# tramos T/O1/O2 de C13 vs M14
for tr in ("T", "O1", "O2"):
    sub = [x for x in rows if x["tramo"] == tr]
    print(f"   C13 vs M14 en {tr}:", p2(sub, W, "C13", "M14")[:3])
print("   C13 vs M14 fuera de PCC y Tup (todas las ventanas):", p2([x for x in rows if x["vol"] not in ("PuyehueCordonCaulle", "Tupungatito")], W, "C13", "M14")[:3])

# 3. magnitud de lo que C13 recupera
print("\n== 3. alertas bajo 1 MW que C13 publica y M14 no: razon VRP port/MIROVA")
rr = [(x["vrp"]["C13"] / x["mir"], x["vol"], x["hora"]) for x in rows if x["c"] == "pos_bajo" and x["pub"]["C13"] and not x["pub"]["M14"] and x["mir"] > 0]
print("   n", len(rr), "mediana", np.median([a for a, _, _ in rr]), "min/max", min(rr)[0], max(rr)[0])
print("   por volcan:", collections.Counter(v for _, v, _ in rr))
rr2 = [x["vrp"]["C13"] / x["mir"] for x in rows if x["c"].startswith("pos") and x["pub"]["C13"] and x["pub"]["M14"] and x["mir"] > 0]
print("   publicadas por los dos: n", len(rr2), "mediana", np.median(rr2))
# negativos publicados por C13: magnitud
neg = [(x["vrp"]["C13"], x["vol"], x["hora"], x["c"]) for x in rows if x["c"] in ("neg_pub", "neg_resto") and x["pub"]["C13"]]
print("   negativos que C13 publica:", len(neg), "VRP mediana", np.median([a for a, *_ in neg]), "max", max(neg)[0])
negr = [(round(x["vrp"]["C13"], 4), x["vol"], x["hora"]) for x in rows if x["c"] == "neg_resto" and x["pub"]["C13"]]
print("   neg_resto que C13 publica:", negr)

# 4. por volcan, C13 vs M14 negativos y positivos
print("\n== 4. por volcan: negativos (neg_pub+neg_resto) que publican M14/C13 y alertas bajo 1 MW recuperadas")
for vol in sorted({x["vol"] for x in rows}):
    sv = [x for x in rows if x["vol"] == vol]
    nm = sum(x["pub"]["M14"] for x in sv if x["c"].startswith("neg")); nc = sum(x["pub"]["C13"] for x in sv if x["c"].startswith("neg"))
    bm = sum(x["pub"]["M14"] for x in sv if x["c"] == "pos_bajo"); bc = sum(x["pub"]["C13"] for x in sv if x["c"] == "pos_bajo")
    print(f"   {vol:22s} neg M14 {nm:3d} C13 {nc:3d} | bajo M14 {bm:3d} C13 {bc:3d} de {sum(1 for x in sv if x['c']=='pos_bajo')}")
