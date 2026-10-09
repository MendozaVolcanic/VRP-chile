# -*- coding: utf-8 -*-
"""S150. Complemento de tif_contraste.py para las perdidas con TIF: medir en la celda de NUESTRO pixel no
dice nada si MIROVA alerto OTRO objeto (A107: una distancia escalar no identifica el objeto). Aca se
busca, en la imagen de MIROVA de esa pasada, la celda de mayor z dentro de un disco de 3 km alrededor de
nuestro pixel publicado, y se informa su z y su separacion. Mismo z que tif_contraste (dL contra media y
sd de dL de toda la imagen, sin borde).
Control: el mismo calculo sobre el residual (MIROVA callo) da la vara de "cuanto sobresale algo en un
disco de 3 km cuando MIROVA no vio nada".

  python tif_disco_perdidas.py tif_contraste.json --tmp <dir del paso 1>
"""
import argparse, io, json, math, statistics as st, sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform
# stdout utf-8: lo envuelve tif_contraste al importarse
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from tif_contraste import mean8, BASE  # noqa: E402


def disco(ruta, lat, lon, rad_km=3.0):
    with rasterio.open(ruta) as ds:
        L = ds.read(1).astype(float); L[L <= 0] = np.nan
        n0, n1 = L.shape
        rows, cols = np.mgrid[0:n0, 0:n1]
        xs, ys = rasterio.transform.xy(ds.transform, rows.ravel(), cols.ravel())
        if ds.crs.to_epsg() != 4326:
            xs, ys = rio_transform(ds.crs, "EPSG:4326", xs, ys)
    lo = np.array(xs).reshape(n0, n1); la = np.array(ys).reshape(n0, n1)
    d = np.hypot((la - lat) * 111.32, (lo - lon) * 111.32 * math.cos(math.radians(lat)))
    dl = L - mean8(L); m = np.zeros_like(L, bool); m[1:-1, 1:-1] = True
    pool = dl[m & np.isfinite(dl)]; mu, sd = pool.mean(), pool.std()
    z = (dl - mu) / sd
    sel = (d <= rad_km) & m & np.isfinite(z)
    i = np.nanargmax(np.where(sel, z, -np.inf))
    return float(z.ravel()[i]), float(d.ravel()[i])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("json"); ap.add_argument("--tmp", required=True); a = ap.parse_args()
    R = json.load(open(a.json, encoding="utf-8"))
    pos = {}
    for mes in ("mayo", "junio", "julio", "agosto"):
        T = json.loads((Path(a.tmp) / mes / "tabla.json").read_text(encoding="utf-8"))["pasadas"]
        for k, v in T.items():
            if len(v) == 2:
                pos[k] = (v["control"]["pc_lat"], v["control"]["pc_lon"])
    por_grupo = {}
    for m in R:
        lat, lon = pos[m["clave"]]
        zmax, dmax = disco(BASE / m["tif"], lat, lon)
        por_grupo.setdefault(m["grupo"], []).append((m, zmax, dmax))
    for g, xs in sorted(por_grupo.items()):
        zs = sorted(x[1] for x in xs if np.isfinite(x[1])); n = len(zs)  # sin finitos: disco fuera de la imagen
        print("== %s n=%d (de %d) | z max en disco de 3 km: p25 %.2f med %.2f p75 %.2f | > 5: %d (%.0f %%)" % (
            g, n, len(xs), zs[n // 4], st.median(zs), zs[(3 * n) // 4], sum(z > 5 for z in zs), 100 * sum(z > 5 for z in zs) / n))
    for m, z, d in sorted(por_grupo.get("perdida por F", []), key=lambda x: x[0]["clave"]):
        print("  %-42s z max disco %.2f a %.1f km de nuestro pixel (z en nuestra ventana %.2f)" % (m["clave"], z, d, m["z_ventana"]))


if __name__ == "__main__":
    main()
