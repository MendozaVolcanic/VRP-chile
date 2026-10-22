"""M2 (S158 r2): ¿se ve en los records la firma del corrimiento hacia el nadir de MODIS?

Fenómeno: si a cada píxel MODIS se le asigna la posición de un píxel más cercano al nadir
(02_interp_geo_sintetico.py), el cúmulo del cráter aparece corrido en la dirección del satélite.
El ángulo acimutal del sensor (persistido en cada record desde S122, `sensor_azimuth_deg`, del
píxel al satélite, desde el norte en sentido horario) da esa dirección en cada pasada.

Instrumento: para cada record con cúmulo dentro del inner_radius_km (Tier A), proyecto el vector
(centroide del cúmulo - cráter) sobre la dirección al satélite. Si hay corrimiento hacia el nadir,
la mediana de esa proyección es POSITIVA y crece con el cenit. Control: VIIRS 375 y VIIRS 750 usan
la geolocalización de su propio archivo de geolocalización (VNP03), así que no deben mostrarla.
Control de instrumento: la proyección sobre la dirección PERPENDICULAR (az + 90) no debe mostrar
sesgo en ningún sensor.

Numerador: records con pc dentro del inner y ángulos presentes. Ventana: todo el corpus.
Sesgo conocido que NO es error de geolocalización: Lastarria (campo Lazufre al N) y PCC (lacolito a
~7 km): se informan por volcán para que no contaminen el total.
"""
import glob, json, os, sys, io, math
import numpy as np
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
import yaml
vols = {v["name"]: v for v in yaml.safe_load(open(os.path.join(REPO, "volcanoes.yaml")))["volcanoes"]}

def grupo(s):
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"

rows = []
for f in sorted(glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json"))):
    name = os.path.basename(f)[:-5]
    v = vols[name]
    inner = v.get("inner_radius_km")
    if not inner: continue
    vlat = v.get("vent_lat", v["lat"]); vlon = v.get("vent_lon", v["lon"])
    for r in json.load(open(f))["records"]:
        pc = r.get("primary_cluster") or {}
        if (pc.get("vrp_mw") or 0) <= 0: continue
        if pc.get("centroid_dist_km") is None or pc["centroid_dist_km"] > inner: continue
        az = r.get("sensor_azimuth_deg"); zen = r.get("sensor_zenith_deg")
        if az is None or zen is None: continue
        dn = (pc["centroid_lat"] - vlat) * 111.32
        de = (pc["centroid_lon"] - vlon) * 111.32 * math.cos(math.radians(vlat))
        a = math.radians(az)
        p_sat = de * math.sin(a) + dn * math.cos(a)        # hacia el satélite (hacia el nadir)
        p_perp = de * math.cos(a) - dn * math.sin(a)       # perpendicular
        rows.append((grupo(r["sensor"]), name, abs(zen), p_sat, p_perp, r["datetime_utc"]))

print("records usados:", len(rows))
import statistics as st
def resumen(sel, titulo):
    if not sel: print(titulo, "SIN DATO"); return
    ps = [x[3] for x in sel]; pp = [x[4] for x in sel]
    print(f"{titulo}: n={len(sel)} mediana hacia_nadir={st.median(ps):+.2f} km (p25 {np.percentile(ps,25):+.2f}, p75 {np.percentile(ps,75):+.2f}) | mediana perpendicular={st.median(pp):+.2f} km | fraccion >0: {sum(1 for p in ps if p>0)/len(ps):.2f}")

for g in ("MODIS", "VIIRS375", "VIIRS750"):
    sel = [x for x in rows if x[0] == g]
    resumen(sel, f"\n[{g}] todos los Tier A")
    for lo, hi in ((0, 20), (20, 40), (40, 55), (55, 70)):
        resumen([x for x in sel if lo <= x[2] < hi], f"  cenit [{lo},{hi})")
    sin_sesgo_conocido = [x for x in sel if x[1] not in ("Lastarria", "PuyehueCordonCaulle")]
    resumen(sin_sesgo_conocido, f"  sin Lastarria ni PCC")
    for lo, hi in ((0, 20), (20, 40), (40, 55), (55, 70)):
        resumen([x for x in sin_sesgo_conocido if lo <= x[2] < hi], f"    cenit [{lo},{hi})")

print("\nPor volcán (MODIS vs VIIRS375), mediana hacia el nadir en km:")
for name in sorted(set(x[1] for x in rows)):
    m = [x[3] for x in rows if x[1] == name and x[0] == "MODIS"]
    i = [x[3] for x in rows if x[1] == name and x[0] == "VIIRS375"]
    k = [x[3] for x in rows if x[1] == name and x[0] == "VIIRS750"]
    f = lambda a: f"{st.median(a):+.2f} (n={len(a)})" if a else "SIN DATO"
    print(f"  {name:22s} MODIS {f(m):18s} VIIRS375 {f(i):18s} VIIRS750 {f(k)}")
