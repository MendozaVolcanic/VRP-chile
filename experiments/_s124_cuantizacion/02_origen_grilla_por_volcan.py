# -*- coding: utf-8 -*-
"""Tarea 3d del plan — el origen de la grilla de MIROVA, volcan por volcan.

READ-ONLY, de los GeoTIFF del archivo (`../mirova-tif-archive`). Sale gratis y
alimenta el analisis espacial: si el centro de SU grilla no coincide con
nuestro ancla, nuestras celdas no coinciden con las suyas y el fondo de los
ocho vecinos se calcula sobre vecindarios distintos aunque la resolucion sea
la misma (relevante para leer el residual de F70).
"""
import glob, io, math, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
ARCHIVO = ROOT.parent / "mirova-tif-archive/data/tif"


def hav(a, b, c, d):
    p = math.pi / 180
    x = (math.sin((c - a) * p / 2) ** 2
         + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(x))


if __name__ == "__main__":
    try:
        import rasterio
        import yaml
    except ImportError as e:
        print(f"falta dependencia: {e}")
        sys.exit(0)

    cfg = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
    vents = {v["name"]: (v.get("vent_lat") or v.get("lat"),
                         v.get("vent_lon") or v.get("lon"))
             for v in cfg["volcanoes"] if v.get("name")}

    print(f"{'carpeta TIF':24s} {'grilla':>9s} {'celda m':>8s} "
          f"{'centro grilla':>24s} {'d(vent)':>9s}")
    print("-" * 80)
    for carpeta in sorted(ARCHIVO.glob("*")):
        tifs = sorted(glob.glob(str(carpeta / "*VIIRS375.tif")))
        if not tifs:
            continue
        with rasterio.open(tifs[-1]) as src:
            t, H, W = src.transform, src.height, src.width
        clat = t.f - H / 2 * abs(t.e)
        clon = t.c + W / 2 * t.a
        celda = abs(t.e) * 111.32 * 1000
        # match laxo del nombre de carpeta contra los del yaml
        cand = [n for n in vents
                if n.lower().replace("de", "") in carpeta.name.lower().replace("de", "")
                or carpeta.name.lower()[:6] in n.lower()]
        dv = ""
        if cand and all(vents[cand[0]]):
            dv = f"{hav(clat, clon, *vents[cand[0]]) * 1000:7.0f} m"
        print(f"{carpeta.name:24s} {H:4d}x{W:<4d} {celda:8.0f} "
              f"{clat:11.6f},{clon:11.6f} {dv:>9s}")
    print("\nd(vent) = distancia del centro de SU grilla a NUESTRO ancla.")
    print("Un offset grande significa celdas desalineadas: mismo tamano, distinta")
    print("particion del terreno, y por lo tanto vecindarios distintos.")
