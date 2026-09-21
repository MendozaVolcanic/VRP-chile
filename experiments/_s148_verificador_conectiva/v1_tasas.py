# -*- coding: utf-8 -*-
"""V1: recalculo independiente de P1 a P4, control negativo (B contra B) y efecto del filtro None.

Uso: python v1_tasas.py <dir_salidas_run> <dir_congelado> <fin>
"""
import sys
import collections
from verif_base import B, F, cargar_brazo, cargar_ref, etiquetar, zona

D, CONG, FIN = sys.argv[1], sys.argv[2], sys.argv[3]
rb, dupb = cargar_brazo(D + "/" + B)
rf, dupf = cargar_brazo(D + "/" + F)
print("records B", len(rb), "claves duplicadas", dupb, "| F", len(rf), "claves duplicadas", dupf)
filas = cargar_ref(CONG)
lab, _ = etiquetar(rb, filas, "2026-09-01", FIN)
labf, _ = etiquetar(rf, filas, "2026-09-01", FIN)
print("pasadas nocturnas etiquetadas: B", len(lab), "F", len(labf),
      "| solo en B", len(set(lab) - set(labf)), "| solo en F", len(set(labf) - set(lab)))
dif_lab = sum(1 for k in lab if k in labf and lab[k] != labf[k])
print("pasadas comunes con etiqueta distinta entre brazos:", dif_lab)
for nombre, recs, l in (("B", rb, lab), ("F", rf, labf)):
    n = sum(1 for k in l if k[1] == "VIIRS375" and recs[k].get("primary_cluster")
            and not isinstance(recs[k].get("f5_core_vrp_mw"), (int, float)))
    print(nombre, "V375 con cumulo y SIN f5_core persistido (mi port no cubre el respaldo JS):", n)


def razon(r):
    if r["nadir"][0] and r["borde"][1]:
        return round((r["borde"][0] / r["borde"][1]) / (r["nadir"][0] / r["nadir"][1]), 2)
    return "nan"


def tabla(recs, l, sensor, exigir=True):
    res = collections.OrderedDict()
    ks = [k for k in l if k[1] == sensor]
    if exigir:
        ks = [k for k in ks if recs[k].get("sensor_zenith_deg") is not None and recs[k].get("t_bg_k") is not None]
    neg = [k for k in ks if l[k] == "neg"]
    pos = [k for k in ks if l[k] == "pos"]

    def t(s):
        return (sum(recs[k]["_pub"] for k in s), len(s))
    res["neg"] = t(neg)
    if exigir:
        for z in ("nadir", "medio", "borde"):
            res[z] = t([k for k in neg if zona(recs[k]["sensor_zenith_deg"]) == z])
        res["borde_frio"] = t([k for k in neg if zona(recs[k]["sensor_zenith_deg"]) == "borde"
                               and recs[k]["t_bg_k"] < 260])
    res["pos"] = t(pos)
    return res


for s in ("VIIRS375", "VIIRS750", "MODIS"):
    print("\n==", s, "| ventana 2026-09-01 a", FIN)
    for nombre, recs, l in (("B", rb, lab), ("F", rf, labf), ("B-vs-B", rb, lab)):
        r = tabla(recs, l, s)
        print("  %-7s" % nombre, "  ".join("%s %d/%d" % (k, v[0], v[1]) for k, v in r.items()), " razon b/n:", razon(r))
    sb, sf = tabla(rb, lab, s, False), tabla(rf, labf, s, False)
    print("  sin exigir zenith ni t_bg: B neg", sb["neg"], "pos", sb["pos"], "| F neg", sf["neg"], "pos", sf["pos"])
print("\netiquetas V375 (B):", dict(collections.Counter(v for k, v in lab.items() if k[1] == "VIIRS375")))
