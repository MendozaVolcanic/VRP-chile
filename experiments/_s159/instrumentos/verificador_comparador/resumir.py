# -*- coding: utf-8 -*-
"""Resume experimentos_salida.json: por ventana, estrato y familia, cuántos brazos dan MEJORA final, MEJORA por d
(sin comparador) y MEJORA por d', y cuántas veces falla la calibración de d' por cola."""
import json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
R = json.load(open("experimentos_salida.json", encoding="utf-8"))
agg = collections.defaultdict(list)
for x in R:
    agg[(x["w"], x["nom"], x["fam"], x["et"].split(" seed")[0])].append(x)
print("ventana estrato familia brazo | n | MEJORA final | MEJORA por d | d' MEJORA | d' cal falla (cola M, cola E) | volcanes d'<0 | d'med")
for k in sorted(agg):
    v = agg[k]
    c = lambda f: sum(1 for x in v if f(x))
    print("%s %-26s %-3s %-24s | %2d | %2d | %2d | %2d | %d (%d,%d) | %s | %s" % (
        k[0], k[1], k[2], k[3], len(v), c(lambda x: x["final"] == "MEJORA"), c(lambda x: x["r_d"] == "MEJORA"),
        c(lambda x: x["r_dp"] == "MEJORA"), c(lambda x: x["calib_dp"] is False),
        c(lambda x: (x["fm_dp"] or 0) > 0.05), c(lambda x: (x["fe_dp"] or 0) > 0.05),
        sorted(collections.Counter(x["vols_dp"] for x in v).items()),
        "%+.3f" % (sum(x["dp_med"] or 0 for x in v) / len(v))))
