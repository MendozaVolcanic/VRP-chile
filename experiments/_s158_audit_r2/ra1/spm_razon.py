# -*- coding: utf-8 -*-
"""RA1: single_pixel_mode (vrp del cumulo = max por pixel, no la suma) en VIIRS 750: cuanto baja la magnitud contra
MIROVA en cumulos de 2 a 3 pixeles frente a cumulos de 1 pixel (donde max = suma). Lee cruce_v750_salida.json."""
import json, os
AQUI = os.path.dirname(os.path.abspath(__file__))
cr = json.load(open(os.path.join(AQUI, "cruce_v750_salida.json"), encoding="utf-8"))
def q(v):
    v = sorted(v); n = len(v); return (round(v[n // 4], 3), round(v[n // 2], 3), round(v[3 * n // 4], 3)) if v else None
sel = [x for x in cr if x["dentro"] and not x["cero"] and x["alerta"] and x["vrp_mirova"]]
for etiqueta, cond in (("1 pixel", lambda p: p["n_pixels"] == 1), ("2-3 px con single_pixel_mode", lambda p: p["n_pixels"] >= 2 and p.get("single_pixel_mode")), ("sin single_pixel_mode (>=5 MW o >3 px)", lambda p: not p.get("single_pixel_mode"))):
    v = [x["pc"]["vrp_mw"] / x["vrp_mirova"] for x in sel if cond(x["pc"])]
    print("%-40s n=%d razon pc/MIROVA cuartiles %s" % (etiqueta, len(v), q(v)))
print("single_pixel_mode.py: vrp = max(per_pixel) si pc.vrp_mw < 5 MW y n_pixels <= 3 (flags SUB_MW_REGIME_THRESHOLD_MW=5, SINGLE_PIXEL_MAX_CLUSTER_PIXELS=3)")
