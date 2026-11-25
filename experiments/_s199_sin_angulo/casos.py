# -*- coding: utf-8 -*-
"""S199: qué hace la vía con cada caso de ángulo inválido, antes y después de la marca «angulo_ausente».

Corre el gránulo sintético de tests/test_via_angulo_ausente_s199.py (foco de 2 x 2 a 600 K sobre el cráter de
Villarrica, de noche) por `calcular_vrp_granulo` real en los tres sensores y escribe, por caso, el motivo, la potencia,
dayflag y sunglint. Uso: python experiments/_s199_sin_angulo/casos.py > salida.txt (desde la raíz del repo).
Salidas: casos_salida_main.txt (origin/main 643cd7ec7) y casos_salida_rama.txt (rama s199-sin-angulo).
"""
import io
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import test_via_angulo_ausente_s199 as T  # noqa: E402

CASOS = [
    ("validos, satelite 20", 20.0, {}),
    ("sin cenit solar, satelite 5", 5.0, {"solar_zenith": "ausente"}),
    ("cenit solar NaN, satelite 5", 5.0, {"solar_zenith": np.nan}),
    ("cenit solar relleno, satelite 5", 5.0, {"solar_zenith": T.RELLENO}),
    ("sin cenit solar, satelite 30", 30.0, {"solar_zenith": "ausente"}),
    ("cenit solar NaN, satelite 30", 30.0, {"solar_zenith": np.nan}),
    ("cenit solar relleno, satelite 30", 30.0, {"solar_zenith": T.RELLENO}),
    ("sin ningun angulo", 20.0, {k: "ausente" for k in T.CLAVES}),
    ("cenit satelite NaN", 20.0, {"sensor_zenith": np.nan}),
    ("azimut solar ausente", 20.0, {"solar_azimuth": "ausente"}),
]

for fam in T.FAMILIAS:
    for nombre, sat, cambios in CASOS:
        gr = T._granulo(fam, sat_zen=sat)
        for k, v in cambios.items():
            if isinstance(v, str):
                del gr["ang"][k]
            else:
                gr["ang"][k][:] = v
        r = T._correr(gr, fam)
        d = r["diag_codigo_mirova"]
        print(f"{fam:9s} | {nombre:34s} | motivo={d.get('motivo_vacio')!s:16s} | vrp_mw={r['vrp_mw']:<9} | "
              f"dayflag={d.get('dayflag')!s:4s} | sunglint={d.get('sunglint')!s:7s} | "
              f"invalidos={d.get('angulos_invalidos')}")
