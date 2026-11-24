# -*- coding: utf-8 -*-
"""V5-B: tamano del efecto de 303 en la metrica que el hallazgo cita (banco_paridad.py::metrica_far_ref l. 450).

Preguntas del instrumento: 1) si el origen mezclado distorsionara frac_radio_a_2km, ¿esto lo veria? Si: recalcula la misma fraccion con el
radio de NUESTRO centroide medido desde mirova_center (mismo origen que MIROVA, supuesto verificado en V5-A con 715 pares CONS) y compara.
2) Instrumento muerto: control positivo = reproducir exactamente la fraccion del banco con el origen original (tiene que coincidir con
metrica_far_ref de la base); placebo = origen mirova_center desplazado 10 km al azar, que debe mover la fraccion.
Universo: recs 'far_ref' del banco con pc_dist y dist_ref (f5_base.pkl, ventana 2026-06-11..2026-11-07). pc = primary_cluster del record.
"""
import collections, math, os, pickle, random, sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import yaml
import banco_paridad as bp
B = pickle.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f5\f5_base.pkl", "rb"))
V = {v["name"]: v for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
def hav(a, b, c, d):
    p = math.radians
    return 2 * 6371.0 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))
far = [r for r in B["recs"] if r["lab"] == "far_ref"]
print("far_ref recs:", len(far), collections.Counter(r["b"] for r in far))
# control positivo: la metrica de la base
metrica = bp.metrica_far_ref(B["recs"], {})
print("metrica base:", {b: (v["n"], v["n_con_distancia"], v["frac_radio_a_2km"]) for b, v in metrica.items() if isinstance(v, dict)})
rng = random.Random(3)
filas = collections.defaultdict(lambda: collections.Counter())
for r in far:
    if r["dist_ref"] is None or r["pc_dist"] is None:
        continue
    c = B["crudos"].get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")), {})
    pc = c.get("pc") or {}
    mc = V[r["vol"]].get("mirova_center_lat"), V[r["vol"]].get("mirova_center_lon")
    k = (r["b"], r["vol"])
    filas[k]["n"] += 1
    filas[k]["orig_a2km"] += abs(r["pc_dist"] - r["dist_ref"]) <= 2
    if pc.get("centroid_lat") is not None and mc[0] is not None:
        d_mc = hav(pc["centroid_lat"], pc["centroid_lon"], mc[0], mc[1])
        filas[k]["n_mc"] += 1
        filas[k]["mc_a2km"] += abs(d_mc - r["dist_ref"]) <= 2
        # placebo: centro corrido 10 km en un rumbo al azar
        ang = rng.uniform(0, 2 * math.pi)
        la = mc[0] + (10 / 111.0) * math.cos(ang); lo = mc[1] + (10 / (111.0 * math.cos(math.radians(mc[0])))) * math.sin(ang)
        d_pl = hav(pc["centroid_lat"], pc["centroid_lon"], la, lo)
        filas[k]["placebo_a2km"] += abs(d_pl - r["dist_ref"]) <= 2
tot = collections.defaultdict(collections.Counter)
for (b, vol), c in sorted(filas.items()):
    print(b, vol, dict(c))
    for kk, vv in c.items():
        tot[b][kk] += vv
for b, c in sorted(tot.items()):
    print("TOTAL", b, dict(c), "frac_orig", round(c["orig_a2km"] / c["n"], 3), "frac_mc", round(c["mc_a2km"] / c["n_mc"], 3) if c["n_mc"] else None,
          "frac_placebo", round(c["placebo_a2km"] / c["n_mc"], 3) if c["n_mc"] else None)
