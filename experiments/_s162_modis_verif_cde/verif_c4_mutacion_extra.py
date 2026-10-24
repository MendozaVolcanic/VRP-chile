# -*- coding: utf-8 -*-
"""Verificador CDE, C4: ¿qué NO ve la prueba 05_prueba_envoltorio.py? Mutaciones extra del envoltorio, fuera de las 6
del auditor, para medir el alcance de `comprobar`. Reusa el arnés del auditor (importa 05 como módulo, mismo gránulo
sintético, mismo port) y envuelve `envoltorio_nativo._guardar` para alterar el .npz DESPUÉS de que el envoltorio lo arma.

Las dos preguntas del instrumento:
1. Si la prueba del auditor fuera ciega a una capa, ¿se vería? Sí: una mutación en esa capa pasaría `comprobar`.
2. Si el arnés estuviera muerto, ¿se vería? Control: una de las 6 mutaciones del auditor (b21_como_b22) tiene que caer
   por aserción también por este camino.
Mutaciones extra: (m7) sensor_zenith y sensor_azimuth intercambiados; (m8) sensor_zenith en ceros; (m9) lon_mxd03
negada... no: (m9) lat_mxd03 y lon_mxd03 intercambiadas (sí la ve: están en `pares`); (m10) forma_granulo mal.
Uso: con VRP_S159_PORTES apuntando a experiments/_s159/portes del árbol base,
     python -I verif_c4_mutacion_extra.py --prueba <carpeta de 05_prueba_envoltorio.py>
"""
import argparse
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ap = argparse.ArgumentParser()
ap.add_argument("--prueba", required=True)
a = ap.parse_args()
sys.path.insert(0, a.prueba)
spec = importlib.util.spec_from_file_location("prueba05", Path(a.prueba) / "05_prueba_envoltorio.py")
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
E = T.E

MUT = {"m7_zenit_azimut_intercambiados": lambda arr: arr.update(sensor_zenith=arr["sensor_azimuth"], sensor_azimuth=arr["sensor_zenith"]),
       "m8_zenit_en_ceros": lambda arr: arr.update(sensor_zenith=np.zeros_like(arr["sensor_zenith"])),
       "m9_lat_lon_mxd03_intercambiadas": lambda arr: arr.update(lat_mxd03=arr["lon_mxd03"], lon_mxd03=arr["lat_mxd03"]),
       "m10_forma_granulo_mal": lambda arr: arr.update(forma_granulo=arr["forma_granulo"][::-1].copy()),
       "control_b21_como_b22": lambda arr: arr.update(b22=arr["b21"])}
_orig_savez = np.savez_compressed
activa = {"m": None}


def savez_mutante(f, **arr):
    if activa["m"] and "linea" in arr:      # solo el nativo_*.npz; la grilla del probe pasa intacta
        MUT[activa["m"]](arr)
    return _orig_savez(f, **arr)


o, full, geo, nfoco = T.preparar()
res = {}
with tempfile.TemporaryDirectory(prefix="s162_vcd_") as td:
    base = Path(td)
    r0, out0 = T.correr(o, base, "sin_envoltorio")
    E.instalar()
    E.np.savez_compressed = savez_mutante
    try:
        for m in MUT:
            activa["m"] = m
            try:
                rm, outm = T.correr(o, base, f"mut_{m}")
                T.comprobar(r0, out0, rm, outm, o, full, geo)
                res[m] = "NO ATRAPADA"
            except AssertionError as e:
                res[m] = f"atrapada por aserción: {e}"
            except Exception as e:  # noqa: BLE001
                res[m] = f"CAE sin aserción ({type(e).__name__}: {e})"
            finally:
                activa["m"] = None
    finally:
        E.np.savez_compressed = _orig_savez
        E.desinstalar()
for m, v in res.items():
    print(f"  {m:<34} {v}")
print("control OK" if res["control_b21_como_b22"].startswith("atrapada") else "CONTROL FALLA: el arnés no ve ni la mutación del auditor")
