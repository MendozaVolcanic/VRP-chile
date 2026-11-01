"""VB v01: corrimiento MODIS hacia el satelite, medido por PAREO con VIIRS 375 de la misma noche.

Camino distinto al del auditor (que proyecta centroide - crater por sensor): aca no uso el crater.
Para cada record MODIS con cumulo, busco el record VIIRS 375 (geolocalizacion por pixel, VNP03IMG)
del mismo volcan mas cercano en tiempo (<= 60 min) con cumulo, y proyecto
(centroide MODIS - centroide VIIRS) sobre la direccion al satelite MODIS (sensor_azimuth_deg).
La posicion real de la fuente se cancela en la diferencia.

Pregunta 1 (si lo medido estuviera roto, lo veria?): si MODIS estuviera corrido hacia el satelite,
la mediana pareada sale positiva y crece con el cenit. Si no lo estuviera, ~0.
Pregunta 2 (instrumento muerto?): control positivo: sumo +1,0 km sinteticos hacia el satelite al
centroide MODIS y el estimador tiene que subir ~1,0. Control nulo: pareo VIIRS 750 contra VIIRS 375
(los dos con su propio archivo de geolocalizacion) proyectado igual: tiene que dar ~0.
Proyeccion perpendicular (az+90) como control de direccion.
Denominador: pares encontrados. Ventana: todo el corpus data/mirova_equivalent al checkout de hoy.
"""
import glob, json, os, sys, io, math
from datetime import datetime
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))

def grp(s):
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "V750"
    return "V375"

def t(r):
    return datetime.fromisoformat(r["datetime_utc"].replace("Z", "").split("+")[0])

def proj(lat1, lon1, lat2, lon2, az_deg):
    # vector 1 - 2 en km, proyectado sobre az (desde el norte, horario) y su perpendicular
    dn = (lat1 - lat2) * 111.195
    de = (lon1 - lon2) * 111.195 * math.cos(math.radians(0.5 * (lat1 + lat2)))
    a = math.radians(az_deg)
    return dn * math.cos(a) + de * math.sin(a), -dn * math.sin(a) + de * math.cos(a)

def offset_km(lat, lon, az_deg, km):
    a = math.radians(az_deg)
    return lat + km * math.cos(a) / 111.195, lon + km * math.sin(a) / (111.195 * math.cos(math.radians(lat)))

res = {"MODIS": [], "V750": []}
for f in sorted(glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json"))):
    vol = os.path.basename(f)[:-5]
    recs = json.load(open(f))["records"]
    by = {"MODIS": [], "V375": [], "V750": []}
    for r in recs:
        pc = r.get("primary_cluster") or {}
        if pc.get("centroid_lat") is None or r.get("sensor_azimuth_deg") is None:
            continue
        by[grp(r["sensor"])].append((t(r), r, pc))
    v375 = sorted(by["V375"], key=lambda x: x[0])
    tt = np.array([x[0].timestamp() for x in v375])
    if len(tt) == 0:
        continue
    for g in ("MODIS", "V750"):
        for (ti, r, pc) in by[g]:
            i = np.searchsorted(tt, ti.timestamp())
            best = None
            for j in (i - 1, i):
                if 0 <= j < len(tt):
                    dt = abs(tt[j] - ti.timestamp())
                    if dt <= 3600 and (best is None or dt < best[0]):
                        best = (dt, j)
            if best is None:
                continue
            _, rv, pv = v375[best[1]]
            # Exijo los dos cumulos a <= 10 km entre si (misma fuente, no cumulos distintos)
            a, p = proj(pc["centroid_lat"], pc["centroid_lon"], pv["centroid_lat"], pv["centroid_lon"], r["sensor_azimuth_deg"])
            if math.hypot(a, p) > 10:
                continue
            la, lo = offset_km(pc["centroid_lat"], pc["centroid_lon"], r["sensor_azimuth_deg"], 1.0)
            ac, _ = proj(la, lo, pv["centroid_lat"], pv["centroid_lon"], r["sensor_azimuth_deg"])
            res[g].append((vol, r["sensor_zenith_deg"], a, p, ac, r["sensor"], r["datetime_utc"]))

def resumen(lst, nombre):
    print(f"== {nombre}: pares n={len(lst)}")
    for lo, hi in ((0, 20), (20, 40), (40, 55), (55, 70)):
        s = [x for x in lst if lo <= x[1] < hi]
        if not s:
            print(f"  cenit [{lo},{hi}): SIN DATO"); continue
        a = np.array([x[2] for x in s]); p = np.array([x[3] for x in s]); c = np.array([x[4] for x in s])
        vols = {}
        for x in s: vols[x[0]] = vols.get(x[0], 0) + 1
        print(f"  cenit [{lo},{hi}): n={len(s)} mediana hacia_satelite={np.median(a):+.2f} km "
              f"(p25 {np.percentile(a,25):+.2f}, p75 {np.percentile(a,75):+.2f}) | perpendicular={np.median(p):+.2f} | "
              f"control +1km -> {np.median(c):+.2f} | volcanes {dict(sorted(vols.items(), key=lambda kv:-kv[1]))}")

resumen(res["MODIS"], "MODIS - VIIRS375 (<=60 min, <=10 km)")
resumen([x for x in res["MODIS"] if x[0] == "Lascar"], "  solo Lascar")
resumen([x for x in res["MODIS"] if x[0] not in ("Lascar", "PuyehueCordonCaulle", "Lastarria")], "  sin Lascar, PCC ni Lastarria")
resumen(res["V750"], "CONTROL NULO V750 - VIIRS375 (<=60 min, <=10 km)")
