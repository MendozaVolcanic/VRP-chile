# -*- coding: utf-8 -*-
"""I2 complemento: clase (iii) por umbral de separacion (tolerancia de la tarea, 2 km, 3 km) con origen comun.
Lee i2_pares.csv (salida de f5_medir.py). Salida: i2_fuertes_out.json."""
import csv, collections, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(H, "i2_pares.csv"), encoding="utf-8")))
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}
out = collections.defaultdict(collections.Counter)
casos = []
for r in rows:
    k = f"{r['vol']}|{r['b']}"
    out[k]["n"] += 1
    out[k]["prot"] += r["protegida"] == "True"
    if not r["dist_mirova"] or not r["d_desde_mirova_center"]:
        out[k]["iv"] += 1
        continue
    d = float(r["d_desde_mirova_center"]) - float(r["dist_mirova"])
    for nom, u in (("sep>tol", TOL[r["b"]]), ("sep>2km", 2.0), ("sep>3km", 3.0)):
        if abs(d) > u:
            out[k][nom] += 1
            if r["protegida"] == "True":
                out[k][nom + "_prot"] += 1
    if abs(d) > 2.0:
        casos.append({**{x: r[x] for x in ("vol", "sensor", "dt", "fecha_mirova", "vrp_mirova", "protegida", "dist_mirova",
                                         "fuente_dist", "estrato", "d_desde_mirova_center", "d_final_hotspot", "our_lat", "our_lon", "pc_vrp")},
                      "delta_km": round(d, 2)})
tot = collections.Counter()
for v in out.values():
    tot.update(v)
res = {"total": dict(tot), "por_vol_sensor": {k: dict(v) for k, v in sorted(out.items())}, "casos_sep_mayor_2km": casos}
json.dump(res, open(os.path.join(H, "i2_fuertes_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res["total"]))
for k, v in sorted(out.items()):
    print(k, dict(v))
print(len(casos), "casos > 2 km")
for c in casos:
    print(c["vol"], c["sensor"], c["dt"], c["vrp_mirova"], c["protegida"], c["fuente_dist"], c["estrato"], "mir", c["dist_mirova"], "nuestra(mc)", c["d_desde_mirova_center"], "delta", c["delta_km"])
