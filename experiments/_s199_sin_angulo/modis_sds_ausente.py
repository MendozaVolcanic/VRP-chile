# -*- coding: utf-8 -*-
"""S199: ¿qué hace leer_geo_mxd03 (lector MODIS de la vía) si el MxD03 no trae uno de los cuatro ángulos?

R3F3-102 lo dijo leyendo el código («un ángulo ausente lanza excepción en sd.select»), sin ejecutar pyhdf. Aquí se
ejecuta: se escribe un HDF4 mínimo con Latitude, Longitude y los ángulos (int16, scale_factor 0,01, como el MxD03) y se
lee con el lector real, una vez completo y una vez sin SolarZenith. Además se escribe el relleno -32767 en el píxel
central para ver que el lector lo entrega escalado (-327,67), que la marca de S199 reconoce por rango.
Corre con el entorno conda vrp (pyhdf con HDF4), con su Library\\bin en el PATH (memoria reference_pyhdf_windows_conda_vrp):
  PATH=<vrp>;<vrp>/Library/bin;$PATH <vrp>/python.exe modis_sds_ausente.py <raíz del repo> <carpeta temporal>
Salida guardada: modis_sds_ausente_salida.txt.
"""
import sys
import traceback
from pathlib import Path

import numpy as np

raiz, tmp = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(raiz))
tmp.mkdir(parents=True, exist_ok=True)
from pyhdf.SD import SD, SDC  # noqa: E402

from pipeline import mirova_v750_codigo as MV  # noqa: E402


def escribir(ruta, omitir=None):
    sd = SD(str(ruta), SDC.WRITE | SDC.CREATE)
    n = 5
    for nm, val in (("Latitude", -39.42), ("Longitude", -71.93)):
        s = sd.create(nm, SDC.FLOAT32, (n, n))
        s[:] = np.full((n, n), val, np.float32)
        s.endaccess()
    for nm, val in (("SensorZenith", 2000), ("SensorAzimuth", -10000), ("SolarZenith", 12000), ("SolarAzimuth", 5000)):
        if nm == omitir:
            continue
        a = np.full((n, n), val, np.int16)
        if nm == "SolarZenith":
            a[2, 2] = -32767
        s = sd.create(nm, SDC.INT16, (n, n))
        s[:] = a
        s.scale_factor = 0.01
        s.endaccess()
    sd.end()


for omitir in (None, "SolarZenith"):
    ruta = tmp / f"mxd03_{omitir or 'completo'}.hdf"
    if ruta.exists():
        ruta.unlink()
    escribir(ruta, omitir)
    print(f"--- MxD03 sintético {'sin ' + omitir if omitir else 'completo'}: {ruta.name}")
    try:
        lat, lon, ang = MV.leer_geo_mxd03(ruta)
        print("lee sin error; claves:", sorted(ang), "; solar_zenith[2,2] =", ang["solar_zenith"][2, 2],
              "; solar_zenith[0,0] =", ang["solar_zenith"][0, 0])
        geom = {k: float(v[2, 2]) for k, v in ang.items()}
        print("angulos_invalidos_de en el píxel de relleno:", MV.angulos_invalidos_de(geom))
    except Exception as e:  # noqa: BLE001
        print("EXCEPCION:", type(e).__module__ + "." + type(e).__name__, "-", e)
        print("".join(traceback.format_exception(e)[-3:]).strip())
