# -*- coding: utf-8 -*-
"""S193: una misma pasada sintética de Villarrica por los tres procesadores, con el perfil de VRP_PROFILE.

No es una prueba (pytest sólo recoge test_*.py): lo corre tests/test_laboratorio_paso1_s193.py en un subproceso por
perfil, porque pipeline.profile lee VRP_PROFILE al importarse y dos perfiles en un mismo proceso darían el primero.

POR QUÉ por los procesadores y no por calcular_vrp_granulo: los flags del perfil (qué sensor corre la vía, banda 22,
umbrales de K) se leen en process_modis.py, process_viirs.py y process_viirs_mod.py; el módulo de la vía no lee el
perfil. Comparar el record que sale de calculate_vrp es comparar lo que el almacén recibiría para esa pasada.

El gránulo es sintético (malla regular con un leve desorden de posición para que la triangulación no tenga empates,
S152; fondo de 268 K y un foco en el cráter). Las temperaturas son ilustrativas, no instrumentales: sólo tienen que
hacer que la vía detecte, para que la igualdad no sea la de dos escenas vacías. Se leen las radiancias reemplazando los
lectores de archivos del módulo de la vía; el resto del camino es el de producción.
Imprime una línea «@@» con {familia: record}.

S195 (paso 3): con el argumento «debil» la escena es otra: fondo más ruidoso (para que el término mu + s·sd del umbral
contextual mande sobre el piso de 0,003, como pasa de noche en ~70 % de las pasadas reales en NTI) y dos focos tibios
iguales, uno en el cráter (dentro de la zona A: círculo de inner_radius_km cortado por la región sensible) y otro a
FOCO_ANILLO_KM al este, dentro del círculo pero fuera de la región sensible en los tres sensores. Con la zona apagada o
con s = 5 no alerta ninguno; con s chico alerta el del cráter y no el del anillo (decisión (a) de Nicolás, 2026-11-22).
Con «debil» la línea «@@» lleva {familia: {"record": ..., "zona": [[fila, col], ...]}}, con la intersección calculada
aquí con las funciones de producción (caja y posición del cráter), no con la de la vía: así la prueba no se valida
con la misma función que prueba.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import process_modis as PM  # noqa: E402
from pipeline import process_viirs as PV  # noqa: E402
from pipeline import process_viirs_mod as PVM  # noqa: E402

V_LAT, V_LON = -39.42, -71.93      # volcanoes.yaml, Villarrica (volcan_por_coordenadas exige igualdad)
INNER_KM = 5.0                      # volcanoes.yaml, inner_radius_km de Villarrica
PASO_NATIVO_KM = {"MODIS": 1.0, "VIIRS750": 0.75, "VIIRS375": 0.375}
T_FOCO_K = {"MODIS": 420.0, "VIIRS750": 340.0, "VIIRS375": 340.0}
ARCHIVO = {"MODIS": "MYD021KM.A2026290.0600.061.2026290120000.hdf",
           "VIIRS750": "VJ102MOD.A2026290.0554.021.2026290120000.nc",
           "VIIRS375": "VJ102IMG.A2026290.0554.021.2026290120000.nc"}
PROCESADOR = {"MODIS": PM, "VIIRS750": PVM, "VIIRS375": PV}


FOCO_ANILLO_KM = 4.0   # dentro del círculo de 5 km de Villarrica y fuera de las cajas sensibles (±2,4 a ±2,6 km)
RUIDO_DEBIL_K = 2.0
DT_FOCO_DEBIL_K = {"MODIS": 6.0, "VIIRS750": 6.0, "VIIRS375": 6.0}


def granulo(familia, semilla=190, escena="calor"):
    # semilla 190: el gránulo de tests/test_via_dato_faltante_crater_s190.py, cuyo control prueba que la vía detecta el
    # foco en las tres familias (con la 193 la escena de VIIRS 375 salió sin alertados, n_abs, n_p1 y n_p2 en 0; no
    # investigué por qué: el control de G2 lo atrapó, que es su trabajo).
    paso = PASO_NATIVO_KM[familia]
    n = 2 * int(round(41.0 / paso)) + 1
    c = n // 2
    rng = np.random.default_rng(semilla)
    fil, col = np.indices((n, n))
    yn = (c - fil) * paso + rng.normal(0, 0.05 * paso, (n, n))
    xe = (col - c) * paso + rng.normal(0, 0.05 * paso, (n, n))
    lat = V_LAT + yn / 111.32
    lon = V_LON + xe / (111.32 * math.cos(math.radians(V_LAT)))
    lat[c, c], lon[c, c] = V_LAT, V_LON
    cfg = MV.FAMILIAS[familia]
    if escena == "debil":
        t = 268.0 + rng.normal(0, 0.4, (n, n))
        t_mir = t + rng.normal(0, RUIDO_DEBIL_K, (n, n))
        mir = MV.temperatura_a_radiancia(t_mir, cfg["lam_mir"])
        tir = MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])
        k_anillo = c + int(round(FOCO_ANILLO_KM / paso))
        for f, k in ((c, c), (c, k_anillo)):
            mir[f, k] = MV.temperatura_a_radiancia(268.0 + DT_FOCO_DEBIL_K[familia], cfg["lam_mir"])
    else:
        t = 268.0 + rng.normal(0, 0.4, (n, n))
        mir = MV.temperatura_a_radiancia(t, cfg["lam_mir"])
        tir = MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])
        mir[c, c] = MV.temperatura_a_radiancia(T_FOCO_K[familia], cfg["lam_mir"])
        tir[c, c] = MV.temperatura_a_radiancia(300.0, cfg["lam_tir"])
    ang = {"sensor_zenith": np.full((n, n), 20.0), "solar_zenith": np.full((n, n), 120.0),
           "sensor_azimuth": np.full((n, n), -100.0), "solar_azimuth": np.full((n, n), 50.0)}
    b_mir, b_tir = cfg["bandas"]
    return {b_mir: mir, b_tir: tir}, lat, lon, ang


def zona_independiente(familia):
    """Celdas de la grilla de la vía que son región sensible (BOX == 2) y están a <= INNER_KM del cráter, con la caja
    y la posición del cráter de producción (como calcular_vrp_granulo) y la distancia de distance_class."""
    cfg = MV.FAMILIAS[familia]
    nombre = MV.volcan_por_coordenadas(V_LAT, V_LON)
    g = MV.grilla_del_volcan(nombre, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
    if cfg.get("roi1_half_m") is not None:
        box = MV.caja_v375(g, V_LAT, V_LON, lado_sensible=cfg["lado_sensible"], half_roi1_m=cfg["roi1_half_m"])
    else:
        box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, V_LAT, V_LON), inner_km=INNER_KM,
                          lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
    pos = MV.posicion_de(g, V_LAT, V_LON)
    out = []
    for f in range(1, g["n"] - 1):           # el .m deja fuera el borde de la grilla (l. 102-103)
        for k in range(1, g["n"] - 1):
            if box[f, k] == 2 and math.hypot(f - pos[0], k - pos[1]) * g["paso"] / 1000.0 <= INNER_KM:
                out.append([f, k])
    return out


def correr(familia, escena="calor"):
    rad, lat, lon, ang = granulo(familia, escena=escena)
    MV.leer_radiancia_l1b = lambda *_a, **_k: rad
    MV.leer_radiancia_modis = lambda *_a, **_k: rad
    MV.leer_geo_l1b = lambda *_a, **_k: (lat, lon, ang)
    MV.leer_geo_mxd03 = lambda *_a, **_k: (lat, lon, ang)
    return PROCESADOR[familia].calculate_vrp(Path(ARCHIVO[familia]), Path("geo_sintetico"), V_LAT, V_LON,
                                             vent_lat=V_LAT, vent_lon=V_LON, inner_radius_km=INNER_KM)


if __name__ == "__main__":
    escena = sys.argv[1] if len(sys.argv) > 1 else "calor"
    if escena == "debil":
        salida = {f: {"record": correr(f, escena), "zona": zona_independiente(f)} for f in ("MODIS", "VIIRS750", "VIIRS375")}
    else:
        salida = {f: correr(f) for f in ("MODIS", "VIIRS750", "VIIRS375")}
    print("@@" + json.dumps(salida, default=float, sort_keys=True))
