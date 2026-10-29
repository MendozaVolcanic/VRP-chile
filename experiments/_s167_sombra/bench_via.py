"""Costo de CPU de la vía «código MIROVA» por gránulo, en local, con grillas reales de VIIRS 375 (tests/datos_s165_v375)
y un remuestreo sobre un recorte sintético del tamaño de un gránulo real. Sólo lectura del repo."""
import json, sys, time
from pathlib import Path
import numpy as np, yaml
REPO = Path(sys.argv[1]); sys.path.insert(0, str(REPO))
from pipeline import mirova_v750_codigo as MV
V = {x["name"]: x for x in yaml.safe_load((REPO/"volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
E = json.loads((REPO/"tests/datos_s165_v375/esperado.json").read_text(encoding="utf-8"))
print("== procesar_grilla VIIRS 375 sobre grillas reales (detector + fondo fillmissing2 + record)")
for p in E["pasadas"]:
    z = np.load(REPO/f"tests/datos_s165_v375/grilla_{p['id']}.npz"); mir, tir = z["mir"].astype(float), z["tir"].astype(float)
    v = V[p["volcan"]]; g = MV.grilla_del_volcan(p["volcan"], paso_m=375.0, clave_roi="roi_v375")
    vl, vo = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]); box = MV.caja_v375(g, vl, vo)
    t = time.perf_counter()
    rec = MV.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], MV.posicion_de(g, vl, vo), v["inner_radius_km"], "X", familia="VIIRS375")
    print(f"  {p['id']} {p['volcan']:20s} npix {rec['n_anomalous_pixels']:4d}  {time.perf_counter()-t:7.2f} s")
print("== remuestrear_grilla (recorte de 45 km + griddata lineal) con píxeles sintéticos a la resolución del sensor")
for fam, res_m, shape in (("VIIRS375", 375.0, (6464, 6400)), ("VIIRS750", 750.0, (3232, 3200)), ("MODIS", 1000.0, (2030, 1354))):
    cfg = MV.FAMILIAS[fam]; g = MV.grilla_del_volcan("Villarrica", paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
    # gránulo entero de la forma real: el volcán en el centro, paso del sensor en grados (aprox.), algo rotado
    f, c = np.indices(shape, dtype=float); f -= shape[0]/2; c -= shape[1]/2
    dlat = res_m/111320.0; dlon = res_m/(111320.0*np.cos(np.radians(g["centro_lat"])))
    lat = g["centro_lat"] + (f*0.98 + c*0.2)*dlat; lon = g["centro_lon"] + (c*0.98 - f*0.2)*dlon
    rng = np.random.default_rng(0); mir = 0.3 + 0.01*rng.standard_normal(shape); tir = 8 + 0.1*rng.standard_normal(shape)
    t = time.perf_counter(); dist = MV._haversine(lat, lon, g["centro_lat"], g["centro_lon"]); t_h = time.perf_counter()-t
    t = time.perf_counter(); a, b = MV.remuestrear_grilla(lat, lon, mir, tir, g); t_r = time.perf_counter()-t
    print(f"  {fam:9s} gránulo {shape}  haversine entero {t_h:5.2f} s  remuestreo {t_r:5.2f} s  (recorte {(dist<MV.RADIO_RECORTE_KM).sum()} px)")
    del lat, lon, mir, tir, f, c, dist
