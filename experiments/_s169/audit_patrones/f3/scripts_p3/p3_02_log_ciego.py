# -*- coding: utf-8 -*-
"""Sonda de la linea de log de scripts/run_pipeline.py para las tres vias (arbol cc3887290).

PREGUNTA 1: si la linea de log de VIIRS 375 estuviera ciega, esta medicion la veria? Si: se compara su texto para un
record CON deteccion y otro SIN deteccion, ambos construidos por la funcion REAL pipeline.mirova_v750_codigo.procesar_grilla
sobre una grilla sintetica (no un dict armado a mano). Control positivo: la linea de MODIS y la de VIIRS 750 (mismos
registros) SI cambian entre los dos casos.
PREGUNTA 2: si el instrumento estuviera muerto (p. ej. no ejecutara la f-string real) el resultado seria igual para
los tres sensores; aqui las f-strings se EXTRAEN del archivo con ast y se ejecutan, no se copian.
Datos: sinteticos (grilla de Villarrica, 134 x 134 celdas de 375 m, un pixel de 330 K en la celda del crater).
"""
import ast
import os
import sys

ARBOL = r"D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/arbol"
sys.path.insert(0, ARBOL)
os.environ["VRP_PROFILE"] = "sombra_codigo_mirova"
import numpy as np
from pipeline import mirova_v750_codigo as MV

# --- 1. lineas reales de run_pipeline.py: dentro de process_date, los pares (vent_str = ..., print(...)) por sensor
src = open(ARBOL + "/scripts/run_pipeline.py", encoding="utf-8").read()
tree = ast.parse(src)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "process_date")
pares = []
for node in ast.walk(fn):
    b = getattr(node, "body", None)
    if isinstance(b, list):
        for i, st in enumerate(b):
            if isinstance(st, ast.Assign) and getattr(st.targets[0], "id", "") == "vent_str":
                pares.append((st, b[i + 1]))
assert len(pares) == 3, len(pares)
nombres = ["MODIS", "VIIRS375", "VIIRS750"]  # orden de aparicion en el archivo
lineas = {}
for nom, (a, p) in zip(nombres, pares):
    mod = ast.Module(body=[a, p], type_ignores=[])
    ast.fix_missing_locations(mod)
    lineas[nom] = compile(mod, "run_pipeline.py", "exec")
    print(f"[{nom}] lineas {a.lineno}-{p.end_lineno} de run_pipeline.py")

def linea(nom, result, vent=True):
    import io, contextlib
    ns = {"result": result, "eff_vent_lat": -39.42 if vent else None, "volcano": {"vent_lat": -39.42}}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(lineas[nom], ns)
    return buf.getvalue().strip()

# --- 2. records reales de la via sobre una grilla sintetica
def grilla_y_box(familia):
    cfg = MV.FAMILIAS[familia]
    g = MV.grilla_del_volcan("Villarrica", paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
    n = g["n"]
    if familia == "VIIRS375":
        box = MV.caja_v375(g, -39.42055, -71.93075)
    else:
        box = MV.caja_roi("def", n=n, celda_crater=MV.celda_de(g, -39.42055, -71.93075), inner_km=5,
                          lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
    return g, box, cfg

def record(familia, caliente):
    g, box, cfg = grilla_y_box(familia)
    n = g["n"]
    mir = np.full((n, n), MV.temperatura_a_radiancia(np.array([278.0]), cfg["lam_mir"])[0])
    tir = np.full((n, n), MV.temperatura_a_radiancia(np.array([270.0]), cfg["lam_tir"])[0])
    pos = MV.posicion_de(g, -39.42055, -71.93075)
    i, j = int(round(pos[0])), int(round(pos[1]))
    rng = np.random.default_rng(1)
    mir = mir * (1 + rng.normal(0, 0.002, mir.shape))
    if caliente:
        mir[i, j] = MV.temperatura_a_radiancia(np.array([340.0]), cfg["lam_mir"])[0]
    sensor = {"MODIS": "MODIS_AQUA", "VIIRS375": "VIIRS_NOAA20", "VIIRS750": "VIIRS_NOAA20_750"}[
        {"VIIRS750": "VIIRS750", "VIIRS375": "VIIRS375", "MODIS": "MODIS"}[familia]]
    return MV.procesar_grilla(mir, tir, g, box, 0, 90.0, pos, 5.0, sensor, familia=familia)

for fam in ("VIIRS375", "MODIS", "VIIRS750"):
    r1, r0 = record(fam, True), record(fam, False)
    print(f"\n== {fam}: record CON deteccion: vrp_mw={r1['vrp_mw']} n_anomalous_pixels={r1['n_anomalous_pixels']} t_max_k={r1['t_max_k']}"
          f" | record SIN deteccion: vrp_mw={r0['vrp_mw']} n={r0['n_anomalous_pixels']}")
    l1, l0 = linea(fam, r1), linea(fam, r0)
    print("   log CON :", l1)
    print("   log SIN :", l0)
    print("   las dos lineas son identicas:", l1 == l0)
