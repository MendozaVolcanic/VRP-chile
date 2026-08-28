# -*- coding: utf-8 -*-
"""S126 — la prueba geometrica: lo que E agrega, ?es un foco o es el terreno?

El dato que cierra el caso es una coincidencia de geometria:

    TEST1_ROI_KM              = 3,0 km   -> el Test 1 vive en el disco r<3 km
    TEST1_INTERMEDIATE_BG_RING_KM = [1,5 - 3,0] km

El anillo que hace de FONDO es la corona exterior del MISMO disco que se mide.
Su area es (9 - 2,25)/9 = 75 % del ROI. O sea: se compara cada pixel contra la
media de los tres cuartos exteriores de su propia vecindad, y el clip a cero
(`maximum(L - L_bg, 0)`, process_viirs.py:1729) se queda con la mitad de arriba.

De ahi sale la prueba falsable mas limpia posible:

  · Si E recupera ENERGIA VOLCANICA, los pixeles agregados tienen que apinarse
    cerca del crater: sobre-representados en los bins internos respecto del area.
  · Si E integra el TERRENO, los pixeles agregados se reparten como el AREA de
    cada corona: 2,8 % en 0-0,5 km, 30,6 % en 2,5-3 km, etc.

Se contrasta bin a bin el observado contra el esperado por area, y se mide el
RUMBO (A70: la distancia sola escondio el sesgo direccional en S104; hay que
mirar la mediana direccional).

Persiste en 07_prueba_geometrica.json.
"""
import io, json, math, os, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
ROI_KM = 3.0                      # TEST1_ROI_KM
RING = (1.5, 3.0)                 # TEST1_INTERMEDIATE_BG_RING_KM
VOLS = {
    "Villarrica":          {"vent": (-39.420227, -71.939876), "reg": "nevado"},
    "PlanchonPeteroa":     {"vent": (-35.241099, -70.573345), "reg": "nevado"},
    "PuyehueCordonCaulle": {"vent": (-40.525499, -72.146137), "reg": "nevado"},
    "Lascar":              {"vent": (-23.362930, -67.731416), "reg": "desierto"},
}
BINS = [(0, .5), (.5, 1), (1, 1.5), (1.5, 2), (2, 2.5), (2.5, 3)]


def hav(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def rumbo(vent, p):
    """Rumbo geografico del pixel visto desde el crater (0=N, 90=E)."""
    (la1, lo1), (la2, lo2) = vent, p
    r = math.pi / 180.0
    y = math.sin((lo2 - lo1) * r) * math.cos(la2 * r)
    x = (math.cos(la1 * r) * math.sin(la2 * r) -
         math.sin(la1 * r) * math.cos(la2 * r) * math.cos((lo2 - lo1) * r))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def cargar(subdir, vol):
    recs = json.load(open(os.path.join(ROOT, "data", subdir, vol + ".json"),
                          encoding="utf-8"))["records"]
    out = {}
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        if not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        out[(r["datetime_utc"], r.get("sensor"))] = r
    return out


area_esp = {}
for lo, hi in BINS:
    area_esp[(lo, hi)] = (hi ** 2 - lo ** 2) / (ROI_KM ** 2)

res = {"roi_km": ROI_KM, "anillo_fondo_km": list(RING),
       "area_del_anillo_sobre_el_roi": round((RING[1] ** 2 - RING[0] ** 2) / ROI_KM ** 2, 4),
       "esperado_por_area": {("%.1f-%.1f" % k): round(v, 4) for k, v in area_esp.items()},
       "por_regimen": {}, "rumbos": {}, "control_pixel_unico": {}}

print("PRUEBA GEOMETRICA — ROI del Test 1 = disco de %.1f km" % ROI_KM)
print("anillo de fondo [%.1f-%.1f] km = %.1f %% del area del ROI\n"
      % (RING[0], RING[1], 100 * res["area_del_anillo_sobre_el_roi"]))

agg = defaultdict(lambda: {"d": [], "brg": [], "npx": 0})
ctrl_d = defaultdict(list)

for vol, cfg in VOLS.items():
    c, e = cargar("_s125_mag_control", vol), cargar("_s125_viirs_e", vol)
    for k in sorted(set(c) & set(e)):
        px_c = {(round(p["lat"], 5), round(p["lon"], 5))
                for p in (c[k].get("anomaly_pixels") or [])}
        for p in (e[k].get("anomaly_pixels") or []):
            if (round(p["lat"], 5), round(p["lon"], 5)) in px_c:
                continue
            agg[cfg["reg"]]["d"].append(hav((p["lat"], p["lon"]), cfg["vent"]))
            agg[cfg["reg"]]["brg"].append(rumbo(cfg["vent"], (p["lat"], p["lon"])))
        # el pixel unico que sobrevive HOY (control): ?donde esta?
        ap = c[k].get("anomaly_pixels") or []
        if (c[k].get("primary_cluster") or {}).get("vrp_mw") and len(ap) == 1:
            ctrl_d[vol].append((hav((ap[0]["lat"], ap[0]["lon"]), cfg["vent"]),
                                rumbo(cfg["vent"], (ap[0]["lat"], ap[0]["lon"]))))

print("REPARTO RADIAL de los pixeles que E agrega — observado contra el area")
print("%-12s %10s %12s %12s %10s" % ("bin (km)", "esperado", "nevado obs", "desierto obs", "n/e nevado"))
for lo, hi in BINS:
    fila = ["%.1f-%.1f" % (lo, hi), "%.1f%%" % (100 * area_esp[(lo, hi)])]
    vals = {}
    for reg in ("nevado", "desierto"):
        ds = agg[reg]["d"]
        f = sum(1 for x in ds if lo <= x < hi) / len(ds) if ds else 0
        vals[reg] = f
        fila.append("%.1f%%" % (100 * f))
    fila.append("%.2f" % (vals["nevado"] / area_esp[(lo, hi)]))
    print("%-12s %10s %12s %12s %10s" % tuple(fila))

for reg in ("nevado", "desierto"):
    ds, bs = agg[reg]["d"], agg[reg]["brg"]
    if not ds:
        continue
    obs = {("%.1f-%.1f" % (lo, hi)): round(sum(1 for x in ds if lo <= x < hi) / len(ds), 4)
           for lo, hi in BINS}
    razon = {k: round(obs[k] / res["esperado_por_area"][k], 3) for k in obs}
    res["por_regimen"][reg] = {"n_pixeles": len(ds), "observado": obs,
                               "observado_sobre_esperado": razon,
                               "dist_mediana_km": round(st.median(ds), 3)}
    # rumbo: cuadrantes
    cuad = {"N (315-45)": 0, "E (45-135)": 0, "S (135-225)": 0, "W (225-315)": 0}
    for b in bs:
        if b >= 315 or b < 45:
            cuad["N (315-45)"] += 1
        elif b < 135:
            cuad["E (45-135)"] += 1
        elif b < 225:
            cuad["S (135-225)"] += 1
        else:
            cuad["W (225-315)"] += 1
    res["rumbos"][reg] = {k: round(100 * v / len(bs), 1) for k, v in cuad.items()}

print("\nRUMBO de los pixeles agregados (%% por cuadrante; uniforme = 25 %% c/u)")
for reg, c in res["rumbos"].items():
    print("  %-10s %s" % (reg, "  ".join("%s %.1f%%" % (k.split()[0], v) for k, v in c.items())))

print("\nEL PIXEL QUE SOBREVIVE HOY (control, clusters de 1 pixel)")
print("%-22s %6s %10s %10s %10s %8s" % ("volcan", "n", "d_med km", "p25", "p75", "rumbo"))
for vol, xs in ctrl_d.items():
    if not xs:
        continue
    ds = sorted(x[0] for x in xs)
    bs = [x[1] for x in xs]
    # rumbo mediano circular
    sx = sum(math.sin(math.radians(b)) for b in bs) / len(bs)
    cy = sum(math.cos(math.radians(b)) for b in bs) / len(bs)
    br = (math.degrees(math.atan2(sx, cy)) + 360) % 360
    res["control_pixel_unico"][vol] = {
        "n": len(ds), "dist_mediana_km": round(st.median(ds), 3),
        "p25": round(ds[len(ds) // 4], 3), "p75": round(ds[3 * len(ds) // 4], 3),
        "rumbo_medio_deg": round(br, 1),
        "pct_en_el_anillo_de_fondo": round(
            100 * sum(1 for d in ds if RING[0] <= d <= RING[1]) / len(ds), 1)}
    d = res["control_pixel_unico"][vol]
    print("%-22s %6d %10.2f %10.2f %10.2f %8.0f  (en el anillo: %.0f%%)"
          % (vol, d["n"], d["dist_mediana_km"], d["p25"], d["p75"],
             d["rumbo_medio_deg"], d["pct_en_el_anillo_de_fondo"]))

dest = os.path.join(os.path.dirname(__file__), "07_prueba_geometrica.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
