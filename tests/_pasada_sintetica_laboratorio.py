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


def granulo(familia, semilla=190):
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
    t = 268.0 + rng.normal(0, 0.4, (n, n))
    mir = MV.temperatura_a_radiancia(t, cfg["lam_mir"])
    tir = MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])
    mir[c, c] = MV.temperatura_a_radiancia(T_FOCO_K[familia], cfg["lam_mir"])
    tir[c, c] = MV.temperatura_a_radiancia(300.0, cfg["lam_tir"])
    ang = {"sensor_zenith": np.full((n, n), 20.0), "solar_zenith": np.full((n, n), 120.0),
           "sensor_azimuth": np.full((n, n), -100.0), "solar_azimuth": np.full((n, n), 50.0)}
    b_mir, b_tir = cfg["bandas"]
    return {b_mir: mir, b_tir: tir}, lat, lon, ang


def correr(familia):
    rad, lat, lon, ang = granulo(familia)
    MV.leer_radiancia_l1b = lambda *_a, **_k: rad
    MV.leer_radiancia_modis = lambda *_a, **_k: rad
    MV.leer_geo_l1b = lambda *_a, **_k: (lat, lon, ang)
    MV.leer_geo_mxd03 = lambda *_a, **_k: (lat, lon, ang)
    return PROCESADOR[familia].calculate_vrp(Path(ARCHIVO[familia]), Path("geo_sintetico"), V_LAT, V_LON,
                                             vent_lat=V_LAT, vent_lon=V_LON, inner_radius_km=INNER_KM)


if __name__ == "__main__":
    salida = {f: correr(f) for f in ("MODIS", "VIIRS750", "VIIRS375")}
    print("@@" + json.dumps(salida, default=float, sort_keys=True))
