# -*- coding: utf-8 -*-
"""Verificador S173 (ver_ablmodis): recalculo de brazos desde los recortes nativos/*.npz con piezas.py de f4ec1061d
(copia en repo_f4ec1061d/, extraida con git archive; el codigo de pipeline/ es el del commit medido).

Que mide (pregunta 1): si el JSON del runner no saliera de estas piezas sobre estos recortes, V0 / NAT / G5
recalculados aqui no calzarian con el JSON (vrp_mw, npix, celdas). Brazos propios, por otro camino que el auditor:
  NAT_G5   el detector nativo (correr_nativo) con la geolocalizacion de 5 km interpolada (la de K) en vez del MxD03:
           si NAT y G5 compartieran causa por la geolocalizacion, NAT_G5 deberia caer mucho mas que NAT.
  despl    desplazamiento (km) entre MxD03 y la geolocalizacion de 5 km en el pixel mas cercano al crater, por pasada,
           contra el cenit (A61: eje espacial).
  t_max_k  del record V0 (la via) para 2026-10-01 08:35, para la regla de cirrus del tablero (t_max_k < 273,15 K y
           VRP > 10 MW); y el predicado del tablero con node sobre V0 y X2 de esa pasada.
Pregunta 2: si el instrumento estuviera muerto, V0 no calzaria con el JSON en 27 de 27 (control positivo de la
reproduccion). Denominador: 27 pasadas, 2026-09-29 a 2026-11-02.
"""
import io
import json
import os
import sys
import time

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = "C:/Users/nmend/vrp-wt/s173_cenit/ver_ablmodis/repo_f4ec1061d"
for p in (R, R + "/scripts", R + "/experiments/_s151_mxd03_etiquetas", R + "/experiments/_s173_cenit_modis"):
    sys.path.insert(0, p)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np  # noqa: E402
import yaml  # noqa: E402
import piezas as PZ  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

NPZ = "D:/vrp-trabajo/temporales/s173_aud/ablacion_modis_run/s173-cenit-modis/nativos"
J = "D:/vrp-trabajo/temporales/s173_aud/ablacion_modis_run/s173-cenit-modis/s173_cenit_modis.json"
P = json.load(open(J, encoding="utf-8"))["pasadas"]
vs = yaml.safe_load(open(R + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]
volcan = [v for v in vs if v["name"] == "NevadosDeChillan"][0]
vent = get_detection_anchor(volcan)
inner = volcan.get("inner_radius_km")
grilla = MV.grilla_del_volcan("NevadosDeChillan", paso_m=1000.0, clave_roi="roi_modis")
print("vent (ancla):", vent, "| volcan lat/lon:", (volcan["lat"], volcan["lon"]), "| inner_km:", inner)
print("grilla:", grilla)

solo = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
salida = []
t0 = time.time()
for e in P:
    tag = e["dt"].replace(" ", "_").replace(":", "")
    if solo and tag not in solo:
        continue
    z = np.load(f"{NPZ}/{tag}.npz")
    rad = {"MIR": z["mir"].astype(float), "TIR": z["tir"].astype(float)}
    lat, lon = z["lat_mxd03"].astype(float), z["lon_mxd03"].astype(float)
    lat5, lon5 = z["lat_5km"].astype(float), z["lon_5km"].astype(float)
    sz = z["sensor_zenith"].astype(float)
    dayflag, sg = int(z["dayflag"]), float(z["sunglint"])
    vl = (volcan["lat"], volcan["lon"])
    # V0 (la via) y X2
    m13g, m15g, box, pos = PZ.preparar_grilla(rad, lat, lon, grilla, vent, inner)
    rv0 = PZ.correr_en_grilla("V0", m13g, m15g, grilla, box, dayflag, sg, pos, inner, e["sensor"], vl)
    rx2 = PZ.correr_en_grilla("X2", m13g, m15g, grilla, box, dayflag, sg, pos, inner, e["sensor"], vl)
    s0 = PZ.resumen(rv0)
    # G5 (la via con la geolocalizacion de 5 km)
    m13g5, m15g5, box5, pos5 = PZ.preparar_grilla(rad, lat5, lon5, grilla, vent, inner)
    rg5 = PZ.correr_en_grilla("V0", m13g5, m15g5, grilla, box5, dayflag, sg, pos5, inner, e["sensor"], vl)
    s5 = PZ.resumen(rg5)
    # NAT y NAT con la geolocalizacion de 5 km (brazo propio)
    nat = PZ.correr_nativo(rad, lat, lon, grilla, vent, inner, dayflag, sg, sz, area_real=False)
    nat5 = PZ.correr_nativo(rad, lat5, lon5, grilla, vent, inner, dayflag, sg, sz, area_real=False)
    # desplazamiento MxD03 vs 5 km en el pixel mas cercano al crater (segun MxD03)
    d = MV._haversine(lat, lon, vent[0], vent[1])
    i, j = np.unravel_index(np.nanargmin(d), d.shape)
    despl = float(MV._haversine(np.array([lat[i, j]]), np.array([lon[i, j]]), lat5[i, j], lon5[i, j])[0])
    jv0, jn, jg5 = e["brazos"]["V0"], e["brazos"]["NAT"], e["brazos"]["G5"]
    rep_v0 = (s0["vrp_mw"] == jv0["vrp_mw"] and s0["npix"] == jv0["npix"] and s0["celdas"] == [tuple(c) for c in jv0["celdas"]])
    rep_nat = (nat["vrp_mw"] == jn["vrp_mw"] and nat["npix"] == jn["npix"])
    rep_g5 = (s5["vrp_mw"] == jg5["vrp_mw"] and s5["npix"] == jg5["npix"])
    fila = {"dt": e["dt"], "z": e["z_record"], "mirova": e["vrp_mirova_mw"],
            "V0_vrp": s0["vrp_mw"], "V0_npix": s0["npix"], "V0_t_max_k": rv0.get("t_max_k"), "V0_t_bg_k": rv0.get("t_bg_k"),
            "X2_vrp": rx2.get("vrp_mw"), "X2_t_max_k": rx2.get("t_max_k"),
            "G5_vrp": s5["vrp_mw"], "G5_npix": s5["npix"], "G5_pc_dist_km": s5["pc_dist_km"],
            "NAT_vrp": nat["vrp_mw"], "NAT_npix": nat["npix"], "NAT_dcum": nat["dist_min_cumulo_km"],
            "NAT_G5_vrp": nat5["vrp_mw"], "NAT_G5_npix": nat5["npix"], "NAT_G5_dcum": nat5["dist_min_cumulo_km"],
            "despl_km_mxd03_vs_5km": round(despl, 3), "sz_crater": round(float(sz[i, j]), 2),
            "repro_V0": rep_v0, "repro_NAT": rep_nat, "repro_G5": rep_g5,
            "json_V0": jv0["vrp_mw"], "json_NAT": jn["vrp_mw"], "json_G5": jg5["vrp_mw"]}
    salida.append(fila)
    print(json.dumps(fila, ensure_ascii=False), flush=True)
    if e["dt"] == "2026-10-01 08:35":
        # predicado del tablero con node sobre V0 y X2 (banco_paridad.publica)
        try:
            import probe_etiquetas as PE
            import banco_paridad as bp
            innerh = bp.inner_desde_html()["NevadosDeChillan"]
            pub = PE.publica([rv0, rx2], innerh)
            print("  PREDICADO node 2026-10-01 08:35: inner_html", innerh, "publica V0, X2 =", pub,
                  "| V0 t_max_k", rv0.get("t_max_k"), "vrp", rv0.get("vrp_mw"), "| X2 t_max_k", rx2.get("t_max_k"), "vrp", rx2.get("vrp_mw"))
        except Exception as ex:
            print("  PREDICADO node no corrio:", repr(ex))
print(f"\n{len(salida)} pasadas en {time.time() - t0:.0f} s")
print("repro V0:", sum(f["repro_V0"] for f in salida), "| repro NAT:", sum(f["repro_NAT"] for f in salida), "| repro G5:", sum(f["repro_G5"] for f in salida), "de", len(salida))
json.dump(salida, open("C:/Users/nmend/vrp-wt/s173_cenit/ver_ablmodis/recalcular_npz.json", "w", encoding="utf-8"), indent=1)
