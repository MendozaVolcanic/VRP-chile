# Prueba sintetica de lo que probe_m.py agrega al instrumento de S151 (A116: mostrar que puede dar cada
# resultado antes de creerle). Sin red ni HDF. Reusa el barrido de mentira de S151 (espejo a 705 km).
#   1. grilla gruesa con la convencion documentada (offset 2): el desplazamiento por pixel de desplazamiento_pixeles
#      debe coincidir con MxD03 menos _interp_geo calculado a mano, y en el frame 190 pasar de 1 km.
#   2. grilla gruesa alineada con el zoom (sin defecto): el desplazamiento debe ser < 0,05 km.
#   3. nulo: _interp_geo contra si misma da 0 exacto.
# Uso: python probar_m.py   (sale con codigo 1 si algo falla)
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "experiments/_s151_probe_mod03"))
import probar_probe as S  # noqa: E402  barrido sintetico de S151
from pipeline.process_modis import _interp_geo  # noqa: E402

spec = importlib.util.spec_from_file_location("probe_m", AQUI / "probe_m.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def main():
    lat, lon, _saz, _szen = S.barrido()
    fallas = []
    for caso, (latc, lonc) in (
        ("offset2", (lat[2::5, 2::5][:406, :271], lon[2::5, 2::5][:406, :271])),
        ("alineada", (_interp_geo(lat, 406, 271), _interp_geo(lon, 406, 271))),
    ):
        ilat = _interp_geo(latc, S.NL, S.NS).astype(np.float64)
        ilon = _interp_geo(lonc, S.NL, S.NS).astype(np.float64)
        for (i, j) in ((1000, 190), (1000, 677), (1000, 1162), (20, 677)):
            pix = [{"lat": float(ilat[i, j]), "lon": float(ilon[i, j]), "bt_k": 300.0}]
            vent = (float(lat[i, j]), float(lon[i, j]))
            ventana = np.hypot((lat - vent[0]) * 111.32, (lon - vent[1]) * 111.32 * math.cos(math.radians(vent[0]))) < 60
            d = M.desplazamiento_pixeles(pix, ilat, ilon, lat, lon, ventana)[0]
            dn, de = M.ne_km(float(ilat[i, j]), float(ilon[i, j]), float(lat[i, j]), float(lon[i, j]))
            print("%-8s pixel (%4d,%4d)  desp %.3f km rumbo %5.1f  (i,j) hallado (%d,%d)  a mano %.3f"
                  % (caso, i, j, d["d_km"], d["rumbo"], d["i"], d["j"], math.hypot(dn, de)))
            if (d["i"], d["j"]) != (i, j):
                fallas.append(f"{caso}: ubicar no devolvio el mismo pixel en ({i},{j})")
            if abs(d["d_km"] - math.hypot(dn, de)) > 0.002:
                fallas.append(f"{caso}: desplazamiento distinto del calculado a mano en ({i},{j})")
            if caso == "offset2" and j == 190 and d["d_km"] < 1.0:
                fallas.append("offset2: en el frame 190 el desplazamiento deberia pasar de 1 km")
            if caso == "alineada" and d["d_km"] > 0.05:
                fallas.append(f"alineada: desplazamiento {d['d_km']} con grilla sin defecto en ({i},{j})")
            nulo = M.desplazamiento_pixeles(pix, ilat, ilon, ilat, ilon, ventana)[0]
            if nulo["d_km"] != 0.0:
                fallas.append(f"nulo distinto de 0 en ({i},{j}): {nulo['d_km']}")
    print("FALLAS:", fallas or "ninguna")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
