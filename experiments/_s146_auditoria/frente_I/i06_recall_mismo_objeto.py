# -*- coding: utf-8 -*-
"""I-06. El recall exigiendo que lo publicado pueda ser el MISMO objeto que alerto MIROVA.

El banco cuenta un acierto si publicamos CUALQUIER cosa en la cumbre en la pasada (o en la noche).
Aqui se exige ademas que el radio de nuestro cumulo y el radio que informa MIROVA difieran en no
mas de X km. La diferencia de radios es una cota INFERIOR de la separacion (A93, A107): si falla,
seguro son objetos distintos; si pasa, no prueba que sean el mismo.

P1: si el recall estuviera sostenido por publicaciones en otro sitio, cae al exigir radio.
P2: control: se baraja el radio de MIROVA entre las pasadas pos del mismo volcan y sensor; si el
    acuerdo barajado iguala al real, el acuerdo de radios no informa nada.
"""
import sys, io, json, collections, random
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(__file__).parent
RECS = json.load(open(A / "_cache_recs.json", encoding="utf-8"))
REF = [f for f in json.load(open(A / "_cache_ref.json", encoding="utf-8")) if not f["diurna"]]
ref_idx = collections.defaultdict(list)
for f in REF:
    ref_idx[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])].append(f)
pos = []
for r in RECS:
    filas = [f for f in ref_idx.get((r["vol"], r["b"], r["dt"][:16].replace("T", " ")), []) if f["tipo"].startswith("ALERTA")]
    if not filas:
        continue
    filas.sort(key=lambda f: f["source"])  # CONS antes que OCR: la tabla trae la distancia exacta
    d = next((f["dist_km"] for f in filas if f["dist_km"] is not None), None)
    pos.append({"vol": r["vol"], "b": r["b"], "noche": r["dt"][:10], "pub": r["pub"], "pc_dist": r["pc_dist"],
                "dist_ref": d, "vrp_ref": filas[0]["vrp_mw"], "disp": r["disp"]})
print("pasadas pos:", len(pos), "| con distancia de MIROVA:", sum(1 for p in pos if p["dist_ref"] is not None),
      "| con distancia 0.0 exacta:", sum(1 for p in pos if p["dist_ref"] == 0))


def resumen(pos, x):
    ok = [p for p in pos if p["pub"] and p["dist_ref"] is not None and p["pc_dist"] is not None and abs(p["pc_dist"] - p["dist_ref"]) <= x]
    noches = {(p["vol"], p["noche"]) for p in pos}
    noches_ok = {(p["vol"], p["noche"]) for p in ok}
    return len(ok), len(pos), len(noches_ok), len(noches)


for x in (1, 2, 3, 5):
    a, n, na, nn = resumen(pos, x)
    print(f" radios a <= {x} km: pasadas {a}/{n} = {100 * a / n:.1f}% | noches {na}/{nn} = {100 * na / nn:.1f}%")
print("\npor volcan, radios a <= 2 km (pasadas ok / pasadas pos ; noches ok / noches pos ; mediana radio MIROVA ; mediana radio nuestro)")
for vol in sorted({p["vol"] for p in pos}):
    s = [p for p in pos if p["vol"] == vol]
    a, n, na, nn = resumen(s, 2)
    dm = sorted(p["dist_ref"] for p in s if p["dist_ref"] is not None)
    do = sorted(p["pc_dist"] for p in s if p["pc_dist"] is not None)
    print(f"  {vol:22s} {a}/{n} ; {na}/{nn} ; MIROVA {dm[len(dm) // 2]:.2f} km ; nuestro {do[len(do) // 2]:.2f} km")
print("\npor sensor, radios a <= 2 km")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    s = [p for p in pos if p["b"] == b]
    if s:
        a, n, na, nn = resumen(s, 2)
        print(f"  {b}: pasadas {a}/{n} | noches {na}/{nn}")

rng = random.Random(146)
g = collections.defaultdict(list)
for i, p in enumerate(pos):
    g[(p["vol"], p["b"])].append(i)
acc = []
for _ in range(200):
    bar = [dict(p) for p in pos]
    for ii in g.values():
        d = [pos[i]["dist_ref"] for i in ii]
        rng.shuffle(d)
        for i, v in zip(ii, d):
            bar[i]["dist_ref"] = v
    acc.append(resumen(bar, 2)[0])
acc.sort()
print(f"\ncontrol barajado (radio de MIROVA permutado dentro de volcan-sensor), pasadas a <= 2 km: mediana {acc[100]} rango {acc[0]}-{acc[-1]} | real {resumen(pos, 2)[0]}")

print("\nrazon de magnitud nuestra / MIROVA en pasadas pos publicadas, por sensor (mediana)")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    v = sorted(p["disp"] / p["vrp_ref"] for p in pos if p["b"] == b and p["pub"] and p["vrp_ref"])
    if v:
        print(f"  {b}: n {len(v)} mediana {v[len(v) // 2]:.2f} p10 {v[len(v) // 10]:.2f} p90 {v[9 * len(v) // 10]:.2f}")


# ---------------------------------------------------------------------------------------------
# SEGUNDA PARTE (agregada tras ver la primera): los radios de arriba NO miden desde el mismo punto.
# MIROVA mide desde el centro de su grilla (mirova_center en volcanoes.yaml); nosotros desde el
# crater (vent). En PCC los dos origenes distan ~7,6 km y en Tupungatito ~4 km, asi que comparar
# radios crudos castiga a esos dos volcanes por construccion (A93: desde donde mide cada uno).
# Aqui se re-ancla NUESTRO cumulo al centro de MIROVA y se repite.
import math, yaml
ROOT = A.parents[2]
vy = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}


def hav(a, b, c, e):
    p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(e - b) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


pcpos = {}
for vol in {p["vol"] for p in pos}:
    for x in json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        pc = x.get("primary_cluster") or {}
        if pc.get("centroid_lat") is not None:
            pcpos[(vol, x.get("sensor"), x.get("datetime_utc"))] = (pc["centroid_lat"], pc["centroid_lon"])
print("\n=== SEGUNDA PARTE: nuestro cumulo medido desde el centro de grilla de MIROVA ===")
for vol in sorted({p["vol"] for p in pos}):
    v = vy[vol]
    print(f"  {vol:22s} distancia entre nuestro origen (crater) y el de MIROVA: {hav(v['vent_lat'], v['vent_lon'], v['mirova_center_lat'], v['mirova_center_lon']):.2f} km")
pos2 = []
for r in RECS:
    filas = [f for f in ref_idx.get((r["vol"], r["b"], r["dt"][:16].replace("T", " ")), []) if f["tipo"].startswith("ALERTA")]
    if not filas:
        continue
    filas.sort(key=lambda f: f["source"])
    d = next((f["dist_km"] for f in filas if f["dist_km"] is not None), None)
    ll = pcpos.get((r["vol"], r["sensor"], r["dt"][:16].replace("T", " ")))
    v = vy[r["vol"]]
    pos2.append({"vol": r["vol"], "b": r["b"], "noche": r["dt"][:10], "pub": r["pub"], "dist_ref": d,
                 "pc_dist": hav(ll[0], ll[1], v["mirova_center_lat"], v["mirova_center_lon"]) if ll else None})
for x in (1, 2, 3, 5):
    a, n, na, nn = resumen(pos2, x)
    print(f" radios (mismo origen) a <= {x} km: pasadas {a}/{n} = {100 * a / n:.1f}% | noches {na}/{nn} = {100 * na / nn:.1f}%")
print(" por volcan, a <= 2 km:")
for vol in sorted({p["vol"] for p in pos2}):
    s = [p for p in pos2 if p["vol"] == vol]
    a, n, na, nn = resumen(s, 2)
    dm = sorted(p["dist_ref"] for p in s if p["dist_ref"] is not None)
    do = sorted(p["pc_dist"] for p in s if p["pc_dist"] is not None)
    print(f"  {vol:22s} {a}/{n} ; noches {na}/{nn} ; MIROVA {dm[len(dm) // 2]:.2f} km ; nuestro re-anclado {do[len(do) // 2]:.2f} km")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    s = [p for p in pos2 if p["b"] == b]
    if s:
        a, n, na, nn = resumen(s, 2)
        print(f"  {b}: pasadas {a}/{n} | noches {na}/{nn}")
g2 = collections.defaultdict(list)
for i, p in enumerate(pos2):
    g2[(p["vol"], p["b"])].append(i)
acc = []
for _ in range(200):
    bar = [dict(p) for p in pos2]
    for ii in g2.values():
        d = [pos2[i]["dist_ref"] for i in ii]
        rng.shuffle(d)
        for i, vv in zip(ii, d):
            bar[i]["dist_ref"] = vv
    acc.append(resumen(bar, 2)[0])
acc.sort()
print(f" control barajado dentro de volcan-sensor, pasadas a <= 2 km: mediana {acc[100]} rango {acc[0]}-{acc[-1]} | real {resumen(pos2, 2)[0]}")
