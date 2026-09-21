# -*- coding: utf-8 -*-
"""Verificador S148 del resultado: analisis sobre tabla.json (salida de r1_tabla.py). Solo lee."""
import json, math, statistics as st, collections
from pathlib import Path
AQUI = Path(__file__).resolve().parent
T = json.loads((AQUI / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"


def zona(z):
    return "nadir" if z < 36 else ("medio" if z < 52 else "borde")


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


rows = []
for k, v in T.items():
    vol, b, dt = k.split("|")
    rows.append((vol, b, dt, v[B], v[F]))

print("== 0. cruce de instrumentos: pub node vs port propio; etiqueta evaluador vs port propio")
for arm, i in ((B, 3), (F, 4)):
    print(arm, "pub distinto:", sum(r[i]["pub"] != r[i]["pub2"] for r in rows),
          "| etiquetas:", dict(collections.Counter((r[i]["lab"], r[i]["lab2"]) for r in rows)))
print("etiqueta distinta entre brazos:", sum(r[3]["lab"] != r[4]["lab"] for r in rows))

print("\n== 1. granulos y product_version entre brazos, por tramo")
for tramo, f in (("01-17", lambda d: d[:10] < "2026-09-18"), ("18-20", lambda d: d[:10] >= "2026-09-18")):
    s = [r for r in rows if f(r[2])]
    print(tramo, "n", len(s), "granule distinto", sum(r[3]["granule"] != r[4]["granule"] for r in s),
          "pv distinto", sum(r[3]["pv"] != r[4]["pv"] for r in s),
          "pv ctrl", dict(collections.Counter(r[3]["pv"] for r in s)),
          "pv brazo", dict(collections.Counter(r[4]["pv"] for r in s)),
          "z distinto(>0.01)", sum(abs((r[3]["z"] or 0) - (r[4]["z"] or 0)) > 0.01 for r in s),
          "t_bg distinto(>0.01)", sum(1 for r in s if r[3]["t_bg"] is not None and r[4]["t_bg"] is not None
                                       and abs(r[3]["t_bg"] - r[4]["t_bg"]) > 0.01),
          "t_bg None en uno solo", sum((r[3]["t_bg"] is None) != (r[4]["t_bg"] is None) for r in s))
rep = {"Chaiten", "Tupungatito", "Villarrica"}
s = [r for r in rows if r[0] in rep]
print("reparados: n", len(s), "granule distinto", sum(r[3]["granule"] != r[4]["granule"] for r in s),
      "pv distinto", sum(r[3]["pv"] != r[4]["pv"] for r in s))
for r in rows:
    if r[3]["granule"] != r[4]["granule"] or r[3]["pv"] != r[4]["pv"]:
        print("  DIF", r[0], r[1], r[2], r[3]["granule"], r[3]["pv"], "|", r[4]["granule"], r[4]["pv"],
              "| lab", r[3]["lab"], "pub", r[3]["pub"], r[4]["pub"])
o = [r for r in rows if r[0] not in rep]
print("processed_utc ctrl reparados min/max:", min(r[3]["proc"] for r in s if r[3]["proc"]), max(r[3]["proc"] for r in s if r[3]["proc"]))
print("processed_utc ctrl resto     min/max:", min(r[3]["proc"] for r in o if r[3]["proc"]), max(r[3]["proc"] for r in o if r[3]["proc"]))
print("processed_utc brazo todos    min/max:", min(r[4]["proc"] for r in rows if r[4]["proc"]), max(r[4]["proc"] for r in rows if r[4]["proc"]))
for tramo, f in (("01-17", lambda d: d[:10] < "2026-09-18"), ("18-20", lambda d: d[:10] >= "2026-09-18")):
    q = [r for r in s if f(r[2])]
    print("  reparados", tramo, "z distinto", sum(abs((r[3]["z"] or 0) - (r[4]["z"] or 0)) > 0.01 for r in q),
          "t_bg distinto", sum(1 for r in q if r[3]["t_bg"] is not None and r[4]["t_bg"] is not None and abs(r[3]["t_bg"] - r[4]["t_bg"]) > 0.01),
          "t_max distinto", sum(1 for r in q if r[3]["t_max"] is not None and r[4]["t_max"] is not None and abs(r[3]["t_max"] - r[4]["t_max"]) > 0.01), "de", len(q))
q = [r for r in o]
print("  NO reparados: z distinto", sum(abs((r[3]["z"] or 0) - (r[4]["z"] or 0)) > 0.01 for r in q),
      "t_bg distinto", sum(1 for r in q if r[3]["t_bg"] is not None and r[4]["t_bg"] is not None and abs(r[3]["t_bg"] - r[4]["t_bg"]) > 0.01),
      "t_max distinto", sum(1 for r in q if r[3]["t_max"] is not None and r[4]["t_max"] is not None and abs(r[3]["t_max"] - r[4]["t_max"]) > 0.01), "de", len(q))


def tabla_P(sel, titulo, b="VIIRS375"):
    s = [r for r in sel if r[1] == b]
    neg = [r for r in s if r[3]["lab"] == "neg_limpio"]
    pos = [r for r in s if r[3]["lab"] == "pos"]
    print("--", titulo, b, "| neg", len(neg), "pos", len(pos))
    for nom, i in (("B", 3), ("F", 4)):
        out = {}
        for zn in ("nadir", "medio", "borde"):
            q = [r for r in neg if r[i]["z"] is not None and zona(r[i]["z"]) == zn]
            out[zn] = (sum(r[i]["pub"] for r in q), len(q))
        n_none = sum(1 for r in neg if r[i]["z"] is None)
        tn = out["nadir"][0] / out["nadir"][1] if out["nadir"][1] else float("nan")
        tb = out["borde"][0] / out["borde"][1] if out["borde"][1] else float("nan")
        print("  %s P1 %d/%d=%.1f%% | zonas %s | z None %d | P2 %.2f | P4 %d/%d" % (
            nom, sum(r[i]["pub"] for r in neg), len(neg), 100 * sum(r[i]["pub"] for r in neg) / max(1, len(neg)),
            out, n_none, (tb / tn if tn else float("nan")), sum(r[i]["pub"] for r in pos), len(pos)))


print("\n== 2. P1-P4 ventana completa, y sin 18-20, y solo 18-20")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    tabla_P(rows, "COMPLETA", b)
tabla_P([r for r in rows if r[2][:10] < "2026-09-18"], "SIN 18-20")
tabla_P([r for r in rows if r[2][:10] >= "2026-09-18"], "SOLO 18-20")
tabla_P([r for r in rows if r[3]["pv"] == "standard" and r[4]["pv"] == "standard"], "SOLO standard")
tabla_P([r for r in rows if r[3]["pv"] == "nrt"], "SOLO nrt")
tabla_P([r for r in rows if r[0] not in rep], "SIN los tres reparados")

print("\n== 2b. P3 borde con fondo frio, varios cortes de t_bg (no se cual uso el documento)")
neg = [r for r in rows if r[1] == "VIIRS375" and r[3]["lab"] == "neg_limpio" and r[3]["t_bg"] is not None and r[3]["z"] is not None]
tb = sorted(r[3]["t_bg"] for r in neg)
c1, c2 = tb[len(tb) // 3], tb[2 * len(tb) // 3]
print("cortes terciles t_bg:", round(c1, 2), round(c2, 2), "n con t_bg", len(neg))
for corte in (c1, 255, 260, 262, 265, 270):
    q = [r for r in neg if zona(r[3]["z"]) == "borde" and r[3]["t_bg"] <= corte]
    print("  borde y t_bg<=%.2f: B %d/%d  F %d/%d" % (corte, sum(r[3]["pub"] for r in q), len(q), sum(r[4]["pub"] for r in q), len(q)))

print("\n== 3. positivas: transiciones y calidad de lo publicado")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    pos = [r for r in rows if r[1] == b and r[3]["lab"] == "pos"]
    print(b, dict(collections.Counter((r[3]["pub"], r[4]["pub"]) for r in pos)))
    for r in pos:
        if r[3]["pub"] and not r[4]["pub"]:
            print("   PERDIDA", r[0], r[2], "ref", r[3]["vrp_ref"], "dispB", r[3]["disp"], "z", r[3]["z"])
        if r[4]["pub"] and not r[3]["pub"]:
            print("   GANADA", r[0], r[2], "ref", r[3]["vrp_ref"])
pos = [r for r in rows if r[1] == "VIIRS375" and r[3]["lab"] == "pos" and r[3]["pub"] and r[4]["pub"]]
print("pares pos V375 publicados por ambos:", len(pos))
deg = []
for r in pos:
    d = hav(r[3]["pc_lat"], r[3]["pc_lon"], r[4]["pc_lat"], r[4]["pc_lon"]) if None not in (r[3]["pc_lat"], r[4]["pc_lat"]) else None
    q = r[4]["disp"] / r[3]["disp"] if r[3]["disp"] else None
    deg.append((r, d, q))
print("  razon disp F/B: mediana %.3f min %.3f | <0.5: %d | <0.25: %d | <0.9: %d | >1.1: %d" % (
    st.median(x[2] for x in deg), min(x[2] for x in deg), sum(x[2] < 0.5 for x in deg),
    sum(x[2] < 0.25 for x in deg), sum(x[2] < 0.9 for x in deg), sum(x[2] > 1.1 for x in deg)))
print("  movidas >0.5 km entre positivas:", sum(1 for x in deg if x[1] is not None and x[1] > 0.5),
      "| >2 km:", sum(1 for x in deg if x[1] is not None and x[1] > 2))
print("  las 12 con mayor desplome de magnitud:")
for r, d, q in sorted(deg, key=lambda x: x[2])[:12]:
    print("    ", r[0], r[2], "ref %.3f dispB %.4f dispF %.4f q %.2f mov %.2f km distB %.2f distF %.2f npxB %s npxF %s" % (
        r[3]["vrp_ref"] or -1, r[3]["disp"], r[4]["disp"], q, d if d is not None else -1, r[3]["pc_dist"] or -1, r[4]["pc_dist"] or -1, r[3]["pc_npx"], r[4]["pc_npx"]))
print("  positivas con desplazamiento >0.5 km:")
for r, d, q in deg:
    if d is not None and d > 0.5:
        print("    ", r[0], r[2], "mov %.2f km q %.2f ref %.3f dispB %.4f dispF %.4f distB %.2f distF %.2f" % (
            d, q, r[3]["vrp_ref"] or -1, r[3]["disp"], r[4]["disp"], r[3]["pc_dist"], r[4]["pc_dist"]))
# error contra MIROVA: cuantas positivas pasan a estar a mas de un factor 2 y 4 de MIROVA
for nom, i in (("B", 3), ("F", 4)):
    rr = [r[i]["disp"] / r[i]["vrp_ref"] for r in pos if r[i]["vrp_ref"]]
    print("  %s razon contra MIROVA: <0.5: %d | <0.25: %d | >2: %d | n %d" % (nom, sum(x < 0.5 for x in rr), sum(x < 0.25 for x in rr), sum(x > 2 for x in rr), len(rr)))

print("\n== 4. todos los cumulos movidos >500 m (cualquier etiqueta, cualquier sensor)")
par = [r for r in rows if r[3]["pub"] and r[4]["pub"] and None not in (r[3]["pc_lat"], r[4]["pc_lat"])]
mov = [(r, hav(r[3]["pc_lat"], r[3]["pc_lon"], r[4]["pc_lat"], r[4]["pc_lon"])) for r in par]
mov = [x for x in mov if x[1] > 0.5]
print("pares", len(par), "(publican ambos, con o sin posicion:", sum(1 for r in rows if r[3]["pub"] and r[4]["pub"]), ") movidos", len(mov),
      dict(collections.Counter((x[0][0], x[0][1]) for x in mov)))
for r, d in sorted(mov, key=lambda x: -x[1]):
    print("    ", r[0], r[1], r[2], "%.2f km" % d, "lab", r[3]["lab"], "dispB %.4f dispF %.4f" % (r[3]["disp"], r[4]["disp"]))

print("\n== 5. magnitud pareada contra MIROVA, V375, por volcan (todas las n, sin piso de 5)")
g = collections.defaultdict(list)
for r in pos:
    if r[3]["vrp_ref"] and r[4]["vrp_ref"]:
        g[r[0]].append((r[3]["disp"] / r[3]["vrp_ref"], r[4]["disp"] / r[4]["vrp_ref"]))
allp = [x for v in g.values() for x in v]
print("TODOS n %d mediana B %.4f F %.4f" % (len(allp), st.median(x[0] for x in allp), st.median(x[1] for x in allp)))
for v, xs in sorted(g.items()):
    print("  %-22s n %3d B %.4f F %.4f | pares que cambian %d" % (v, len(xs), st.median(x[0] for x in xs), st.median(x[1] for x in xs), sum(abs(x[0] - x[1]) > 1e-9 for x in xs)))

print("\n== 6. por volcan: negativos y positivos, los tres sensores")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    print(b)
    for v in sorted({r[0] for r in rows}):
        n = [r for r in rows if r[0] == v and r[1] == b and r[3]["lab"] == "neg_limpio"]
        p = [r for r in rows if r[0] == v and r[1] == b and r[3]["lab"] == "pos"]
        gan = sum(1 for r in n if r[4]["pub"] and not r[3]["pub"])
        print("  %-22s neg %3d: B %3d F %3d (ganadas por F %d) | pos %3d: B %3d F %3d" % (
            v, len(n), sum(r[3]["pub"] for r in n), sum(r[4]["pub"] for r in n), gan, len(p), sum(r[3]["pub"] for r in p), sum(r[4]["pub"] for r in p)))

print("\n== 7. todas las etiquetas V375: publicacion B y F")
for lab in sorted({r[3]["lab"] for r in rows}):
    q = [r for r in rows if r[1] == "VIIRS375" and r[3]["lab"] == lab]
    print("  ", lab, len(q), "B", sum(r[3]["pub"] for r in q), "F", sum(r[4]["pub"] for r in q), "F gana", sum(1 for r in q if r[4]["pub"] and not r[3]["pub"]))

print("\n== 8. dependencia 6.1: positivas V375 publicadas por F sin pixeles de primer pase")
q = [r for r in rows if r[1] == "VIIRS375" and r[3]["lab"] == "pos" and r[4]["pub"]]
print("  F publicadas", len(q), "con n_fp==0:", sum(1 for r in q if r[4]["n_fp"] == 0), "| n_fp None:", sum(1 for r in q if r[4]["n_fp"] is None))
q2 = [r for r in q if r[2][:10] < "2026-09-18"]
print("  tramo 01-17: F publicadas", len(q2), "con n_fp==0:", sum(1 for r in q2 if r[4]["n_fp"] == 0))
print("  positivas por volcan V375:", dict(collections.Counter(r[0] for r in rows if r[1] == "VIIRS375" and r[3]["lab"] == "pos")))
print("  negativos sobrevivientes en F (V375):")
for r in rows:
    if r[1] == "VIIRS375" and r[3]["lab"] == "neg_limpio" and r[4]["pub"]:
        print("    ", r[0], r[2], "z %.1f t_bg %s dispF %.4f pubB %d" % (r[4]["z"], r[4]["t_bg"], r[4]["disp"], r[3]["pub"]))
