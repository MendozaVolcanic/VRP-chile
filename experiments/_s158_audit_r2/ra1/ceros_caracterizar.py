# -*- coding: utf-8 -*-
"""RA1: caracteriza los ceros de cumbre de VIIRS 750 (de donde sale t_max_k, cuanto mas frio que el anillo esta el
pixel alertado) y el control de magnitud (razon pc.vrp_mw / VRP de MIROVA en los no ceros pareados).
Lee cruce_v750_salida.json (de contar_ceros_v750.py) y los JSON de data/.
"""
import glob
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
cr = json.load(open(os.path.join(AQUI, "cruce_v750_salida.json"), encoding="utf-8"))
idx = {(x["volcano"], x["datetime_utc"], x["sensor"]): x for x in cr}
tmd_c, tmd_n, bt_alert_c, delta_c, delta_n, razones = [], [], [], [], [], []
razones_reg = {"pre-K": [], "K": []}
for f in glob.glob("data/mirova_equivalent/*.json"):
    vol = os.path.basename(f)[:-5]
    d = json.load(open(f, encoding="utf-8"))
    recs = d if isinstance(d, list) else d["records"]
    for r in recs:
        x = idx.get((vol, r["datetime_utc"], r["sensor"]))
        if not x or not x["dentro"]:
            continue
        tmd = r.get("diag_t_max_dist_km")
        ap = r.get("anomaly_pixels") or []
        # el pixel del cumulo: el anomaly_pixel mas cercano al centroide (lat/lon iguales redondeados)
        pc = r["primary_cluster"]
        px = [p for p in ap if abs(p["lat"] - pc["centroid_lat"]) < 1e-4 and abs(p["lon"] - pc["centroid_lon"]) < 1e-4]
        if x["cero"]:
            if tmd is not None:
                tmd_c.append(tmd)
            if px and r.get("t_bg_k") is not None:
                bt_alert_c.append(px[0]["bt_k"]); delta_c.append(px[0]["bt_k"] - r["t_bg_k"])
        else:
            if tmd is not None:
                tmd_n.append(tmd)
            if px and r.get("t_bg_k") is not None:
                delta_n.append(px[0]["bt_k"] - r["t_bg_k"])
            if x["alerta"] and x["vrp_mirova"]:
                rz = pc["vrp_mw"] / x["vrp_mirova"]
                razones.append(rz); razones_reg[x["reg"]].append(rz)


def q(v):
    v = sorted(v); n = len(v)
    return (round(v[n // 4], 3), round(v[n // 2], 3), round(v[3 * n // 4], 3)) if v else None


print("CEROS de cumbre (n=%d con diag): diag_t_max_dist_km cuartiles %s ; fraccion con t_max a <=5 km: %.3f" % (
    len(tmd_c), q(tmd_c), sum(1 for t in tmd_c if t <= 5) / len(tmd_c)))
print("NO ceros de cumbre (n=%d): diag_t_max_dist_km cuartiles %s ; <=5 km: %.3f" % (
    len(tmd_n), q(tmd_n), sum(1 for t in tmd_n if t <= 5) / len(tmd_n)))
print("CEROS: bt del pixel del cumulo (centroide 1 px) cuartiles %s ; bt - t_bg cuartiles %s (n=%d; cuantos > 0: %d)" % (
    q(bt_alert_c), q(delta_c), len(delta_c), sum(1 for d in delta_c if d > 0)))
print("NO ceros (1 px al centroide): bt - t_bg cuartiles %s (n=%d)" % (q(delta_n), len(delta_n)))
print("CONTROL razon pc.vrp_mw/VRP_MIROVA en cumbre no cero con alerta de MIROVA: n=%d cuartiles %s ; pre-K n=%d %s ; K n=%d %s" % (
    len(razones), q(razones), len(razones_reg["pre-K"]), q(razones_reg["pre-K"]), len(razones_reg["K"]), q(razones_reg["K"])))
al = [x for x in cr if x["dentro"] and x["alerta"]]
alc = [x for x in al if x["cero"]]
pr = [x for x in al if x["protegida"]]
prc = [x for x in pr if x["cero"]]
print("alertas MIROVA V750 pareadas a cumulo de cumbre: %d ; en 0 MW: %d (%.1f%%) ; protegidas: %d ; en 0: %d (%.1f%%)" % (
    len(al), len(alc), 100 * len(alc) / len(al), len(pr), len(prc), 100 * len(prc) / len(pr)))
for reg in ("pre-K", "K"):
    a = [x for x in al if x["reg"] == reg]; c = [x for x in a if x["cero"]]
    print("  %s: alertas %d, en 0: %d" % (reg, len(a), len(c)))
a = [x for x in al if x["datetime_utc"] >= "2026-03-01"]; c = [x for x in a if x["cero"]]
print("  desde 2026-03-01 (tabla sana, A119): alertas %d, en 0: %d (%.1f%%) ; protegidas en 0: %d de %d" % (
    len(a), len(c), 100 * len(c) / len(a), sum(1 for x in c if x["protegida"]), sum(1 for x in a if x["protegida"])))
# noches: de las noches (volcan, fecha) con alerta V750 de MIROVA pareada a cumbre, cuantas quedan SIN ningun record V750 visible
noches = {}
for x in cr:
    if not x["dentro"]:
        continue
    k = (x["volcano"], x["datetime_utc"][:10])
    noches.setdefault(k, {"alerta": False, "visible": False})
    noches[k]["alerta"] |= x["alerta"]
    noches[k]["visible"] |= (not x["cero"])
na = [k for k, v in noches.items() if v["alerta"]]
print("noches (volcan, dia UTC) con cumulo de cumbre V750 y alerta V750 de MIROVA: %d ; sin ningun V750 visible esa noche: %d" % (
    len(na), sum(1 for k in na if not noches[k]["visible"])))
