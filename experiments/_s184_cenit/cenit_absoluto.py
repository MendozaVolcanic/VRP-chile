# -*- coding: utf-8 -*-
"""Efecto absoluto del cenit en nuestras pasadas nocturnas (via): fraccion de pasadas con valor
publicado > 0 y mediana del valor, por volcan, sensor y tramo. Tambien la mediana del VRP de MIROVA
por tramo (cenit nuestro de la misma pasada) desde los pares de cenit_via.py.

Uso: python cenit_absoluto.py <raiz_repo> <pares_json> <salida_json> [desde=2026-03-01]
"""
import io, json, sys, statistics, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT, PARES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DESDE = sys.argv[4] if len(sys.argv) > 4 else "2026-03-01"
import yaml
from datetime import datetime

TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan", "Llaima",
          "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
BINS = [(0, 20), (20, 40), (40, 55), (55, 70), (70, 90)]


def bin_de(z):
    for a, b in BINS:
        if a <= z < b:
            return "%d-%d" % (a, b)
    return "SIN_CENIT"


def fam(s):
    s = s.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "V750"
    return "V375" if s.startswith("VIIRS") else None


def publicado(r, inner):
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw") or r.get("vrp_mir_mw") or 0
        return 0 if v > 50000 else v
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return 0
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


INNER = {v["name"]: v["inner_radius_km"] for v in yaml.safe_load(open(ROOT + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]
         if v["name"] in TIER_A}
d0 = datetime.strptime(DESDE, "%Y-%m-%d")
res = {}
for v in TIER_A:
    acc = collections.defaultdict(list)
    for r in json.load(open(ROOT + "/data/mirova_equivalent/%s.json" % v, encoding="utf-8"))["records"]:
        f = fam(r.get("sensor", ""))
        if f is None or not r.get("via_codigo_mirova"):
            continue
        if (r.get("solar_zenith_deg") or 0) <= 90 or r.get("sensor_zenith_deg") is None:
            continue
        if datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M") < d0:
            continue
        acc[(f, bin_de(r["sensor_zenith_deg"]))].append(publicado(r, INNER[v]))
    res[v] = {}
    for (f, b), L in sorted(acc.items()):
        pos = [x for x in L if x > 0]
        res[v].setdefault(f, {})[b] = dict(n=len(L), n_pos=len(pos), frac_pos=round(len(pos) / len(L), 3),
                                           med_pos=round(statistics.median(pos), 3) if pos else None)
pares = json.load(open(PARES, encoding="utf-8"))
mir = {}
for v in ["NevadosDeChillan", "Lascar", "PuyehueCordonCaulle", "Isluga", "Lastarria", "TODOS"]:
    mir[v] = {}
    for f in ["MODIS", "V375", "V750"]:
        S = [p for p in pares if p["fam"] == f and (v == "TODOS" or p["volcan"] == v) and p["src"] == "consolidado"
             and p["bin"] != "SIN_CENIT"]
        g = collections.defaultdict(list)
        for p in S:
            g[p["bin"]].append(p["mvrp"])
        mir[v][f] = {b: dict(n=len(L), mediana_mirova=round(statistics.median(L), 3)) for b, L in sorted(g.items())}
json.dump({"desde": DESDE, "nuestras_pasadas": res, "mirova_por_tramo": mir}, open(OUT, "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
for v in ["Lascar", "NevadosDeChillan", "Isluga", "Lastarria", "PuyehueCordonCaulle", "Villarrica", "PlanchonPeteroa", "Tupungatito"]:
    for f in ["MODIS", "V375", "V750"]:
        d = res[v].get(f, {})
        print(v, f, " | ".join("%s: %d/%d=%.2f med=%s" % (b, x["n_pos"], x["n"], x["frac_pos"], x["med_pos"]) for b, x in d.items()))
print()
for v, d in mir.items():
    for f, x in d.items():
        print("MIROVA", v, f, " | ".join("%s: n=%d med=%s" % (b, y["n"], y["mediana_mirova"]) for b, y in x.items()))
