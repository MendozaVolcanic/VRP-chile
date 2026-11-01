# -*- coding: utf-8 -*-
"""Verificador S165, A9: la vía compartida (pipeline/mirova_v750_codigo.py) del TAG contra la de HEAD, sobre las
fixtures de VIIRS 750 (8 escenas de O2, tests/data/fillmissing2_matlab_o2.npz) y de MODIS (6 grillas de
tests/datos_s164_modis), con cada float por repr. Cubre procesar_grilla, caja_roi, vrp_mirova y grilla_del_volcan."""
import importlib.util, io, json, sys
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import pipeline  # noqa
def cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(f"pipeline.{nombre}", ruta)
    m = importlib.util.module_from_spec(spec); m.__package__ = "pipeline"; spec.loader.exec_module(m); return m
TAG = cargar(r"D:\vrp-trabajo\temporales\s165_v375_via\verificador_tag\pipeline\mirova_v750_codigo.py", "mv_tag")
HOY = cargar(RAIZ / "pipeline/mirova_v750_codigo.py", "mv_hoy")
def crudo(o):
    if isinstance(o, dict): return {str(k): crudo(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [crudo(v) for v in o]
    if isinstance(o, np.ndarray): return crudo(o.tolist())
    if isinstance(o, np.generic): return crudo(o.item())
    if isinstance(o, float): return repr(o)
    return o
def igual(a, b): return json.dumps(crudo(a), sort_keys=True) == json.dumps(crudo(b), sort_keys=True)
n_ok = n = 0
# VIIRS 750: 8 escenas de O2 con la caja "def" y Láscar, como test_mirova_v750_codigo_s162
z = np.load(RAIZ / "tests/data/fillmissing2_matlab_o2.npz")
for k in range(len(z["k_o2"])):
    # escena sintética con foco (como _escena de test_mirova_v750_codigo_s162) sobre las tres cajas de 750
    rng = np.random.default_rng(162 + k)
    T15 = 265.0 + rng.normal(0, 0.3, (67, 67)); T13 = T15 - 3 + rng.normal(0, 0.3, (67, 67)); T13[33, 33] += 25; T13[33, 40] += 12
    m13 = HOY.temperatura_a_radiancia(T13, HOY.LAMBDA_M13); m15 = HOY.temperatura_a_radiancia(T15, HOY.LAMBDA_M15)
    for tipo in ("def", "sens", "corona"):
        recs = []
        for M in (TAG, HOY):
            g = M.grilla_del_volcan("Lascar"); box = M.caja_roi(tipo)
            recs.append(M.procesar_grilla(m13, m15, g, box, 0, 40.0, (33.0, 33.0), 5.0, "VIIRS_NOAA20_750"))
        n += 1; n_ok += igual(*recs)
        print(f"V750 sintetica {k} caja {tipo}: npix tag={recs[0]['n_anomalous_pixels']} hoy={recs[1]['n_anomalous_pixels']} vrp tag={recs[0]['vrp_mw']} hoy={recs[1]['vrp_mw']} igual={igual(*recs)}")
# el mismo oráculo de VRP sobre la máscara de MATLAB (vrp_mirova directo)
for k in range(len(z["k_o2"])):
    m13 = z[f"m13_{k}"].astype(float); mask = z[f"mask_{k}"].astype(bool)
    a, b = TAG.vrp_mirova(m13, mask), HOY.vrp_mirova(m13, mask)
    n += 1; n_ok += igual(a, b)
    print(f"V750 vrp_mirova escena {k}: tag={a['VRP_MW']!r} hoy={b['VRP_MW']!r} matlab={float(z[f'vrp_{k}'])!r} igual={igual(a, b)}")
# MODIS: 6 grillas de S164
import yaml
V = {x["name"]: x for x in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
esp = json.loads((RAIZ / "tests/datos_s164_modis/esperado.json").read_text(encoding="utf-8"))["pasadas"]
for p in esp:
    zz = np.load(RAIZ / f"tests/datos_s164_modis/grilla_{p['id']}.npz"); mir, tir = zz["mir"].astype(float), zz["tir"].astype(float)
    v = V[p["vol"]]; vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    recs = []
    for M in (TAG, HOY):
        cfg = M.FAMILIAS["MODIS"]; g = M.grilla_del_volcan(p["vol"], paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
        box = M.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=M.celda_de(g, vlat, vlon), inner_km=v["inner_radius_km"], lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
        recs.append(M.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], M.posicion_de(g, vlat, vlon), v["inner_radius_km"], p["sensor"], familia="MODIS"))
    n += 1; n_ok += igual(*recs)
    print(f"MODIS {p['id']} {p['vol']}: npix tag={recs[0]['n_anomalous_pixels']} hoy={recs[1]['n_anomalous_pixels']} vrp tag={recs[0]['vrp_mw']} hoy={recs[1]['vrp_mw']} igual={igual(*recs)}")
# grilla_del_volcan: HEAD agrega x0, y0; lo demás idéntico
for nombre in ("Lascar", "Villarrica", "PuyehueCordonCaulle"):
    for paso, roi in ((750.0, "roi_v750"), (1000.0, "roi_modis")):
        a, b = TAG.grilla_del_volcan(nombre, paso_m=paso, clave_roi=roi), HOY.grilla_del_volcan(nombre, paso_m=paso, clave_roi=roi)
        extra = set(b) - set(a); n += 1; ok = all(a[k] == b[k] for k in a) and extra == {"x0", "y0"}; n_ok += ok
        print(f"grilla {nombre} {paso}: claves nuevas={sorted(extra)} resto igual={ok}")
print(f"\nTOTAL: {n_ok} de {n} comparaciones idénticas (repr de cada float)")
