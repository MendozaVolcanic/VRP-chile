# -*- coding: utf-8 -*-
"""S162 MODIS: corre experiments/_s159/portes/probe_portes.py SIN MODIFICARLO y ademas guarda, por pasada MODIS,
el RECORTE NATIVO del granulo alrededor del volcan, para la ablacion del bow tie (tarea MOD-E, D28).

POR QUE. El lote de S159 guardo solo la grilla 51 x 51 ya remuestreada: los pixeles nativos del barrido no estan, y
sin ellos no se puede saber cuales son duplicados del bow tie (los barridos de 10 lineas de MODIS se solapan lejos
del nadir, y el mismo punto del terreno aparece en dos barridos). Para identificarlos hacen falta, en cada pixel, su
geolocalizacion (la del MxD03 y la interpolada de 5 km que usa produccion), las radiancias que el port remuestrea y
el indice de LINEA y de FRAME del granulo (barrido = linea // 10, detector = linea % 10).

COMO, sin tocar el probe ni cambiar su resultado:
  1. `probe_portes._ventana` se envuelve para anotar las rebanadas (filas, columnas) del recorte, solo mientras corre
     `leer_modis` (leer_viirs y el resto no se tocan).
  2. `pipeline.process_modis.read_modis_l1b` se envuelve para quedarse con el dict completo del L1B (band21, band22,
     band31 y lat/lon de 5 km) de esa misma lectura. Devuelve el MISMO objeto: produccion (K) llama a la misma
     funcion despues y recibe lo mismo; fuera de leer_modis la envoltura no anota nada.
  3. `probe_portes.leer_modis` se envuelve: llama a la original, NO modifica el recorte que devuelve, y guarda
     `nativo_<id>.npz` con los arreglos del L1B cortados con las mismas rebanadas, la lat/lon del MxD03 del recorte
     (el probe ya la corto con esas rebanadas) y los indices de linea y frame de cada pixel.
  4. `probe_portes.procesar` se envuelve solo para saber el id de la pasada y anotar en el resultado `nativo`
     (archivo, forma, bytes, rebanadas) o el motivo por el que no se guardo.
Si el envoltorio cambiara el resultado del port, la prueba 05_prueba_envoltorio.py lo detecta (mismo npix, mismo
VRP, mismos pixeles con y sin envoltorio), y la prueba falla con mutaciones del envoltorio.

Uso (igual que probe_portes.py): python envoltorio_nativo.py --objetivos objetivos_neg_resto_modis.json --out out
     --sensor MODIS --chunk 0 --nchunks 8
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
PORTES = Path(os.environ.get("VRP_S159_PORTES", str(RAIZ / "experiments/_s159/portes")))
sys.path.insert(0, str(PORTES))
import probe_portes as P  # noqa: E402

_MUTACION = ""          # solo para la prueba de mutaciones (05_prueba_envoltorio.py); vacio en el lote
_CTX = {"activo": False, "w": None, "d": None, "id": None, "outdir": None, "info": None}
_ORIG = {}


def _ventana_espia(lat, lon, lat0, lon0, radio):
    w, dmin = _ORIG["_ventana"](lat, lon, lat0, lon0, radio)
    if _CTX["activo"]:
        _CTX["w"] = w
    return w, dmin


def _read_l1b_espia(hdf_path):
    d = _ORIG["read_modis_l1b"](hdf_path)
    if _CTX["activo"]:
        _CTX["d"] = d
    return d


def _guardar(crop, l1b, geo):
    w, d = _CTX["w"], _CTX["d"]
    r0, r1, c0, c1 = (int(v) for v in (w[0].start, w[0].stop, w[1].start, w[1].stop))
    forma = tuple(int(v) for v in np.asarray(d["band21"]).shape)
    linea = np.broadcast_to(np.arange(r0, r1, dtype=np.int16)[:, None], (r1 - r0, c1 - c0)).copy()
    frame = np.broadcast_to(np.arange(c0, c1, dtype=np.int16)[None, :], (r1 - r0, c1 - c0)).copy()
    arr = {
        "lat_mxd03": crop["lat"], "lon_mxd03": crop["lon"],           # MxD03, ya cortada por el probe con w
        "lat_5km": np.asarray(d["lat"])[w], "lon_5km": np.asarray(d["lon"])[w],
        "b21": np.asarray(d["band21"])[w], "b22": np.asarray(d["band22"])[w], "b31": np.asarray(d["band31"])[w],
        "linea": linea, "frame": frame,
        "sensor_zenith": np.asarray(crop["sensor_zenith"], np.float32),
        "sensor_azimuth": np.asarray(crop["sensor_azimuth"], np.float32),
        "rebanadas": np.array([r0, r1, c0, c1], np.int32), "forma_granulo": np.array(forma, np.int32),
    }
    # --- mutaciones de la prueba (nunca activas en el lote) ---
    if _MUTACION == "linea_mas_uno":
        arr["linea"] = arr["linea"] + 1
    elif _MUTACION == "frame_al_reves":
        arr["frame"] = arr["frame"][:, ::-1].copy()
    elif _MUTACION == "b21_como_b22":
        arr["b22"] = arr["b21"]
    elif _MUTACION == "lat5_como_mxd03":
        arr["lat_5km"] = crop["lat"]
    elif _MUTACION == "altera_recorte":
        crop["mir"] *= 1.0001
    elif _MUTACION == "recorte_corrido":
        arr["b31"] = np.asarray(d["band31"])[r0 + 1:r1 + 1, c0:c1]
    elif _MUTACION == "angulos_intercambiados":      # verificador VCD-08
        arr["sensor_zenith"], arr["sensor_azimuth"] = arr["sensor_azimuth"], arr["sensor_zenith"]
    elif _MUTACION == "cenit_corrido":
        arr["sensor_zenith"] = np.roll(arr["sensor_zenith"], 1, axis=0)
    f = Path(_CTX["outdir"]) / f"nativo_{_CTX['id']:04d}.npz"
    t0 = time.time()
    np.savez_compressed(f, **arr)
    return {"archivo": f.name, "forma": [r1 - r0, c1 - c0], "rebanadas": [r0, r1, c0, c1],
            "forma_granulo": list(forma), "bytes": f.stat().st_size, "segundos_guardar": round(time.time() - t0, 2),
            "l1b": Path(l1b).name, "geo": Path(geo).name}


def leer_modis_nativo(l1b, geo, lat0, lon0):
    _CTX.update(activo=True, w=None, d=None)
    try:
        crop, dmin = _ORIG["leer_modis"](l1b, geo, lat0, lon0)
    finally:
        _CTX["activo"] = False
    if crop is None:
        _CTX["info"] = {"guardado": False, "motivo": f"leer_modis devolvio None ({dmin})"}
    elif _CTX["w"] is None or _CTX["d"] is None:
        _CTX["info"] = {"guardado": False, "motivo": "no se capturaron la ventana o el L1B"}
    else:
        try:
            _CTX["info"] = {"guardado": True, **_guardar(crop, l1b, geo)}
        except Exception as e:  # noqa: BLE001  (guardar el recorte nunca debe tumbar la pasada)
            _CTX["info"] = {"guardado": False, "motivo": f"{type(e).__name__}: {e}"}
    _CTX["w"] = _CTX["d"] = None
    return crop, dmin


def procesar_nativo(o, destino, outdir, sin_k=False):
    _CTX.update(id=o["id"], outdir=outdir, info=None)
    r = _ORIG["procesar"](o, destino, outdir, sin_k)
    if o["b"] == "MODIS":
        r["nativo"] = _CTX["info"] or {"guardado": False, "motivo": "no se llego a leer el granulo"}
    return r


def instalar():
    import pipeline.process_modis as PM
    if _ORIG:
        return
    _ORIG.update(_ventana=P._ventana, leer_modis=P.leer_modis, procesar=P.procesar, read_modis_l1b=PM.read_modis_l1b)
    P._ventana = _ventana_espia
    P.leer_modis = leer_modis_nativo
    P.procesar = procesar_nativo
    PM.read_modis_l1b = _read_l1b_espia


def desinstalar():
    import pipeline.process_modis as PM
    if not _ORIG:
        return
    P._ventana, P.leer_modis, P.procesar = _ORIG["_ventana"], _ORIG["leer_modis"], _ORIG["procesar"]
    PM.read_modis_l1b = _ORIG["read_modis_l1b"]
    _ORIG.clear()


if __name__ == "__main__":
    instalar()
    sys.exit(P.main())
