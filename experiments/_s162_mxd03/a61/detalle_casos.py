# -*- coding: utf-8 -*-
"""Detalle de los casos que la tabla A61 dejo marcados: (a) protegidas con residuo >= 0,3 km o cambio de pixeles y
el pixel mas caliente por indice; (b) la protegida fragil (R que la apagan) brazo por brazo; (c) uso estricto de la
`Distancia_km` 0,0 de MIROVA (misma celda); (d) corrimiento maximo en records sin relleno; (e) records con frame del
crater < 100 etiquetados 'otro' (lado del barrido)."""
import collections
import csv
import io
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cargar_a61 import NULOS, cargar_artefactos, haversine_km  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ok, _, _ = cargar_artefactos()
idx = {(r["vol"], r["dt"]): r for r in ok}
tab = list(csv.DictReader(open(Path(__file__).parent / "a61_protegidas.csv", encoding="utf-8")))

print("== (a) protegidas con residuo >= 0,3 km, o con cambio de pixeles, o cuyo cumulo no es el pixel mas caliente por indice")
for f in tab:
    marca = []
    if float(f["residuo_km"]) >= 0.3:
        marca.append("residuo")
    if f["K_npx"] != f["X_npx"]:
        marca.append("npx")
    if f["K_npx"] == "1" and f["pico_es_pcK"] != "True":
        marca.append("pico!=pcK")
    if f["X_npx"] == "1" and f["pico_es_pcX"] != "True":
        marca.append("pico!=pcX")
    if not marca:
        continue
    r = idx[(f["vol"], f["dt"])]
    K, X, p = r["brazos"]["K"], r["brazos"]["X"], r["pico"]
    print("  %s %s z=%s %s | %s | K dist %.2f npx %s vrp %s | X dist %.2f npx %s vrp %s | mov %s km res %s km | pico idx (%d,%d) exceso %.3f: dist crater C %s M %s; pico==pcK %s pico==pcX %s | t_bg K/X %s/%s | sigma K/X %s/%s" % (
        f["vol"], f["dt"], f["z"], f["lado"], ",".join(marca), float(f["K_dist"]), f["K_npx"], f["K_vrp"], float(f["X_dist"]), f["X_npx"], f["X_vrp"],
        f["mov_km"], f["residuo_km"], p["linea"], p["frame"], p["exceso"], f["pico_C_dist"], f["pico_M_dist"], f["pico_es_pcK"], f["pico_es_pcX"],
        K["t_bg_k"], X["t_bg_k"], K["diag_sigma_bg_k"], X["diag_sigma_bg_k"]))
    # distancia entre el centroide y el pico en cada grilla
    pc = p["pos_centro"]
    print("      |pcK - picoC| %.2f km | |pcX - picoM| %.2f km | first_pass K/X %s/%s summit %s/%s recaptura %s/%s | n_anom %s/%s | final_dist %s/%s" % (
        haversine_km(K["pc_lat"], K["pc_lon"], *pc["C"]), haversine_km(X["pc_lat"], X["pc_lon"], *pc["M"]),
        K["diag_n_first_pass_pixels"], X["diag_n_first_pass_pixels"], K["diag_n_first_pass_summit"], X["diag_n_first_pass_summit"],
        K["diag_n_second_pass_recapture"], X["diag_n_second_pass_recapture"], K["n_anom"], X["n_anom"], K["final_dist"], X["final_dist"]))

print("\n== (b) la protegida fragil: Lascar 2026-03-12 07:25, brazo por brazo")
r = idx[("Lascar", "2026-03-12 07:25")]
for b in ["K", "X"] + NULOS:
    br = r["brazos"].get(b)
    ang = next((n["angulo_grados"] for n in r["nulos"] if "R%02d" % n["k"] == b), None)
    print("   %-3s pub %d | rumbo %s | pc_dist %s dc %s pc_vrp %s npx %s n_anom %s | t_bg %s sigma %s | first %s summit %s recap %s | final_dist %s src %s" % (
        b, r["pub"][b], None if ang is None else round(ang), br["pc_dist"], br["dc"], br["pc_vrp"], br["pc_n_pixels"], br["n_anom"],
        br["t_bg_k"], br["diag_sigma_bg_k"], br["diag_n_first_pass_pixels"], br["diag_n_first_pass_summit"], br["diag_n_second_pass_recapture"],
        br["final_dist"], br["final_hotspot_source"]))

print("\n== (c) `Distancia_km` = 0,0 de MIROVA (misma celda de ~1 km que su referencia): cuantas protegidas quedan a <= 0,75 km del crater (media diagonal de la celda)")
cero = [f for f in tab if "0.0" in f["mirova_dist"]]
print("   protegidas con alguna fila 0,0: %d | K <= 0,75 km: %d | X <= 0,75 km: %d | K <= 1,5: %d | X <= 1,5: %d" % (
    len(cero), sum(1 for f in cero if float(f["K_dist"]) <= 0.75), sum(1 for f in cero if float(f["X_dist"]) <= 0.75),
    sum(1 for f in cero if float(f["K_dist"]) <= 1.5), sum(1 for f in cero if float(f["X_dist"]) <= 1.5)))
solo0 = [f for f in cero if f["mirova_dist"] == "[0.0]"]
print("   con 0,0 como UNICA distancia: %d | K <= 0,75: %d | X <= 0,75: %d" % (
    len(solo0), sum(1 for f in solo0 if float(f["K_dist"]) <= 0.75), sum(1 for f in solo0 if float(f["X_dist"]) <= 0.75)))
print("   advertencia: la referencia de MIROVA es su centro de grilla (D15), no nuestro `vent`; en Chillan `vent` = centroide del volcan (volcanoes.yaml), sin crater verificado en terreno.")
ch = [f for f in tab if f["vol"] == "NevadosDeChillan"]
print("   Chillan: K dist %s | X dist %s | MIROVA %s" % ([f["K_dist"] for f in ch], [f["X_dist"] for f in ch], [f["mirova_dist"] for f in ch]))

print("\n== (d) corrimiento interp menos MxD03 en records SIN relleno")
limp = sorted([r for r in ok if not r.get("n_fill_mxd03")], key=lambda r: -r["desplazamiento"]["km"])
print("   maximo %.2f km (%s %s z=%.1f frame %d) | > 10 km: %d | > 8 km: %d | mediana por tramo de cenit:" % (
    limp[0]["desplazamiento"]["km"], limp[0]["vol"], limp[0]["dt"], limp[0]["z"], limp[0]["desplazamiento"]["frame"],
    sum(1 for r in limp if r["desplazamiento"]["km"] > 10), sum(1 for r in limp if r["desplazamiento"]["km"] > 8)))
for lo, hi in ((0, 25), (25, 40), (40, 50), (50, 60), (60, 66)):
    for lado in ("f0", "otro"):
        sel = [r["desplazamiento"]["km"] for r in limp if lo <= r["z"] < hi and r["lado"] == lado]
        if sel:
            print("     z [%d,%d) %-4s n %4d mediana %.2f p90 %.2f max %.2f" % (lo, hi, lado, len(sel), statistics.median(sel), sorted(sel)[9 * len(sel) // 10], max(sel)))

print("\n== (e) records con el pixel del crater en frame < 100 y lado 'otro' (la etiqueta de lado sale del acimut del sensor en la poblacion)")
raro = [r for r in ok if r["desplazamiento"]["frame"] < 100 and r["lado"] == "otro"]
print("   n = %d de %d con frame < 100" % (len(raro), sum(1 for r in ok if r["desplazamiento"]["frame"] < 100)))
for r in raro[:12]:
    print("     %s %s %s z=%.1f az=%s frame %d n_fill %s desp %.1f" % (r["vol"], r["dt"], r["sensor"], r["z"], r["brazos"]["K"]["sensor_azimuth_deg"],
          r["desplazamiento"]["frame"], r.get("n_fill_mxd03"), r["desplazamiento"]["km"]))
raro2 = [r for r in ok if r["desplazamiento"]["frame"] > 1253 and r["lado"] == "f0"]
print("   y frame > 1253 con lado 'f0': %d de %d" % (len(raro2), sum(1 for r in ok if r["desplazamiento"]["frame"] > 1253)))
az = collections.Counter((r["sensor"], r["lado"], "az>0" if (r["brazos"]["K"]["sensor_azimuth_deg"] or 0) > 0 else "az<=0") for r in ok)
print("   cruce sensor x lado x signo del acimut:", dict(az))
