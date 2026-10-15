# Prueba sintetica del probe (A116: un instrumento se valida mostrando que PUEDE dar cada resultado).
# Sin red ni HDF: arma un barrido MODIS de mentira con geometria de espejo y 705 km de altura, saca la grilla
# gruesa como la saca MxD021KM (frame 2 + 5b, linea 2 + 5a) y corre el nucleo `comparar` con la
# `_interp_geo` REAL del pipeline. Tres casos:
#   1. grilla gruesa con la convencion documentada  -> el probe debe medir el corrimiento y decir CONFIRMA
#   2. grilla gruesa "alineada con el zoom"           -> no hay corrimiento: debe decir REFUTA
#   3. la deteccion de offsets debe devolver 2 en los dos ejes en el caso 1
# Uso: python probar_probe.py   (sale con codigo 1 si algo falla)
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1]))
import probe_mod03 as P  # noqa: E402
from pipeline.process_modis import _interp_geo  # noqa: E402

R, H = 6371.0, 705.0
NL, NS = 2030, 1354
C = (NS - 1) / 2.0


def x_suelo(s):
    b = (s - C) / H
    return R * (np.arcsin(np.clip((R + H) / R * np.sin(b), -1, 1)) - b)


def barrido():
    """Pasada descendente (lineas hacia el sur), frame 0 al oeste: con rumbo sur, el oeste es la derecha."""
    s = np.arange(NS, dtype=np.float64)
    li = np.arange(NL, dtype=np.float64)
    lat = np.repeat((-20.0 - li / 111.32)[:, None], NS, axis=1)
    lon = -68.0 + x_suelo(s)[None, :] / (111.32 * np.cos(np.radians(lat)))
    xs = np.broadcast_to(x_suelo(s)[None, :], lat.shape)
    saz = np.where(xs < 0, 90.0, 270.0)                  # del pixel al sensor: hacia el nadir
    szen = np.degrees(np.arcsin(np.clip((R + H) / R * np.sin(np.abs((s - C) / H)), 0, 1)))
    szen = np.broadcast_to(szen[None, :], lat.shape).copy()
    return lat, lon, saz, szen


def main():
    lat, lon, saz, szen = barrido()
    fallas = []
    # caso 1: convencion documentada
    latc, lonc = lat[2::5, 2::5][:406, :271], lon[2::5, 2::5][:406, :271]
    filas = []
    for (i, j) in ((1000, 190), (1000, 240), (1000, 1162), (1000, 900), (300, 337), (1500, 1015), (1000, 600)):
        vent = (float(lat[i, j]), float(lon[i, j]))
        rad = np.zeros_like(lat)
        rad[i, j] = 5.0
        f = P.comparar(lat, lon, latc, lonc, saz, szen, _interp_geo, rad, vent=vent)
        filas.append(f)
        print("caso 1  frame %4d cenit %4.1f  obs %+.3f pred %+.3f  hacia sensor %+.3f  traza obs %+.3f pred %+.3f  frame0 der %s"
              % (j, f["cenit"], f["obs_barrido_km"], f["pred_barrido_km"], f["obs_hacia_sensor_km"],
                 f["obs_traza_km"], f["pred_traza_km_offset2"], f["frame0_a_la_derecha_de_la_traza"]))
        if abs(f["obs_barrido_km"] - f["pred_barrido_km"]) > 0.05:
            fallas.append("caso 1: obs y pred no coinciden en frame %d" % j)
        if not f["frame0_a_la_derecha_de_la_traza"]:
            fallas.append("caso 1: no detecta el frame 0 a la derecha")
        if math.hypot(*f["pixel_brillante_b22_mxd03_dn_de_km"]) > 0.01:
            fallas.append("caso 1: el pixel brillante con MxD03 no cae en el crater")
    v1 = P.veredicto(filas)
    print("caso 1 veredicto:", v1)
    if v1 != "CONFIRMA":
        fallas.append("caso 1 debia dar CONFIRMA y dio %s" % v1)
    off = filas[0]["offsets_grilla_km"]
    print("caso 3 offsets:", off)
    for eje in ("frame", "linea"):
        if min(off[eje], key=off[eje].get) != 2:
            fallas.append("caso 3: el offset del eje %s no sale 2" % eje)
    # caso 2: grilla tomada donde el zoom la va a poner (sin corrimiento)
    jz = np.arange(271) * (NS - 1) / 270.0
    iz = np.arange(406) * (NL - 1) / 405.0
    from scipy.ndimage import map_coordinates
    gi, gj = np.meshgrid(iz, jz, indexing="ij")
    latc2 = map_coordinates(lat, [gi, gj], order=1).astype(np.float32)
    lonc2 = map_coordinates(lon, [gi, gj], order=1).astype(np.float32)
    filas2 = [P.comparar(lat, lon, latc2, lonc2, saz, szen, _interp_geo,
                         vent=(float(lat[1000, j]), float(lon[1000, j]))) for j in (190, 240, 1162, 900, 337, 1015, 600)]
    v2 = P.veredicto(filas2)
    print("caso 2 veredicto:", v2, " obs barrido:", [f["obs_barrido_km"] for f in filas2])
    if v2 != "REFUTA":
        fallas.append("caso 2 debia dar REFUTA y dio %s" % v2)
    if fallas:
        print("FALLAS:", *fallas, sep="\n  ")
        sys.exit(1)
    print("OK: el probe puede dar CONFIRMA y REFUTA, y detecta el offset y el lado")


if __name__ == "__main__":
    main()
