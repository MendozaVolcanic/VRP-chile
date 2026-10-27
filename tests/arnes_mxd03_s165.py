# -*- coding: utf-8 -*-
"""Arnés sintético de los tres flags MxD03 de MODIS (S165, plan 2026-10-25-flag-mxd03-modis).

POR QUÉ. Con los tres flags apagados, `calculate_vrp` de MODIS tiene que dar bit a bit lo que daba el código del tag
`pre-s165-mxd03-modis` (golden `tests/datos_s165_mxd03/apagado_antes.json`, congelado con pipeline/ sin tocar). Y para
que ese «bit a bit» no pase por construcción (A116), cada escena está armada para que un flag encendido SÍ cambie el
resultado:
  * `etiqueta`: el cráter está 0,68 km al norte del centro del volcán (Láscar, A61 H5) y el único píxel caliente está
    5,0 km al norte del centro y 4,32 km del cráter, con inner 4,6 km. Hoy sale `far`; midiendo desde el cráter, `summit`.
  * `mxd03_corrido`: la misma escena, pero el MxD03 ubica cada píxel 2 km más al sur que la grilla interpolada (el
    desfase 5i contra 5i+2, A61 H2). Con la posición del MxD03 cambian la latitud del píxel y su distancia.
  * `crater_relleno`: el MxD03 trae relleno (NaN tras limpiar el -999) en cinco líneas alrededor del cráter. Con MxD03 y
    el estado «sin dato», no hay record.
  * `crater_borde`: el MxD03 deja el cráter fuera de la imagen, más allá de la primera línea. Con MxD03 y «sin dato», no
    hay record.
Las escenas usan la malla y el cono térmico del arnés S142 (tests/arnes_sintetico_s142.py), sin modificarlo.

Uso (un proceso por combinación de flags, porque pipeline.profile se lee al importar):
    VRP_PROFILE=mirova_equivalent python tests/arnes_mxd03_s165.py --salida X.json [--flag NOMBRE=True ...]
Un flag que no existe en pipeline.process_modis hace fallar la corrida (patch.object levanta AttributeError): un brazo
que no lee su flag no puede pasar por control (S133).
"""
import argparse
import ast
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np  # noqa: E402

import arnes_sintetico_s142 as A  # noqa: E402

ESCENAS = ("etiqueta", "mxd03_corrido", "crater_relleno", "crater_borde")
N = 61
C = N // 2
KM_LAT = 1.0 / 111.0
VENT_NORTE_KM = 0.68
INNER_KM = 4.6


def escena(tipo, semilla=3):
    """(data de read_modis_l1b, (lat, lon) del MxD03 o None, vent_lat, vent_lon)."""
    import pipeline.process_modis as pm
    lat, lon, r = A._malla(N, 1.0)
    rng = np.random.default_rng(semilla)
    bt21 = A._cono(r, rng)
    bt31 = bt21 - 1.0 + rng.normal(0, 0.15, r.shape)
    # Píxel caliente 5 km al norte del centro: la fila crece hacia el norte en A._malla.
    bt21[C + 5, C], bt31[C + 5, C] = 290.0, 258.0

    def rad(bt, lam):
        return (pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * bt)) - 1))).astype(np.float32)

    lam21 = pm.BAND21_LAMBDA
    data = {"band21": rad(bt21, lam21), "band22": rad(bt21, lam21), "band31": rad(bt31, 11.03),
            "lat": lat, "lon": lon}
    vent_lat, vent_lon = A.LAT0 + VENT_NORTE_KM * KM_LAT, A.LON0
    lat_m, lon_m = lat.copy(), lon.copy()
    if tipo == "etiqueta":
        pass
    elif tipo == "mxd03_corrido":
        lat_m = (lat - 2.0 * KM_LAT).astype(np.float32)
    elif tipo == "crater_relleno":
        lat_m[C - 2:C + 3, :] = np.nan
        lon_m[C - 2:C + 3, :] = np.nan
    elif tipo == "crater_borde":
        # La última fila (la más al norte) queda en el centro del volcán: el cráter, 0,68 km más al norte, cae fuera.
        lat_m = (lat - C * KM_LAT).astype(np.float32)
    else:
        raise ValueError(tipo)
    return data, (lat_m, lon_m), vent_lat, vent_lon


def correr(tipo, flags):
    import pipeline.process_modis as pm
    data, mxd, vent_lat, vent_lon = escena(tipo)
    ctx = [patch.object(pm, "read_modis_l1b", return_value=data)]
    if hasattr(pm, "leer_mxd03"):
        ctx.append(patch.object(pm, "leer_mxd03", return_value=mxd))
    ctx += [patch.object(pm, k, v) for k, v in flags.items()]
    for p in ctx:
        p.start()
    try:
        return pm.calculate_vrp(
            hdf_path=Path("MOD021KM.A2026200.0300.061.hdf"), geo_path=Path("MOD03.A2026200.0300.061.hdf"),
            volcano_lat=A.LAT0, volcano_lon=A.LON0, radius_km=25.0,
            vent_lat=vent_lat, vent_lon=vent_lon, inner_radius_km=INNER_KM)
    finally:
        for p in ctx:
            p.stop()


def correr_en_subproceso(tmp_dir, flags=(), perfil="mirova_equivalent"):
    import subprocess
    salida = Path(tmp_dir) / f"mxd03_{perfil}_{'_'.join(sorted(flags)) or 'apagado'}.json"
    cmd = [sys.executable, str(ROOT / "tests" / "arnes_mxd03_s165.py"), "--salida", str(salida)]
    for f in flags:
        cmd += ["--flag", f"{f}=True"]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=900,
                       env={**os.environ, "VRP_PROFILE": perfil, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-4000:]
    return salida.read_text(encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--flag", action="append", default=[])
    a = ap.parse_args(argv)
    flags = {}
    for s in a.flag:
        k, v = s.split("=", 1)
        flags[k] = ast.literal_eval(v)
    texto = A.canonico({t: correr(t, flags) for t in ESCENAS})
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
