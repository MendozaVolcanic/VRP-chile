# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos. Chequeo de diseño (local, sin bajar nada): ¿el GeoTIFF geografico
(EPSG:4326) de MIROVA es MAS SUAVE que su GeoTIFF UTM nativo?

POR QUE IMPORTA. Del 2026-09-14 06:36 al 2026-09-15 06:24 MIROVA publico sus TIF de VIIRS 375 en UTM
nativo de 375 m (A106); antes y despues, en EPSG:4326. Aveni et al. 2024 (RSE 315, p. 5, §3.2) y
Fernandina 2025 (Remote Sens. 17, 1191, p. 9, §2.3.1) dicen que la grilla de trabajo es UTM. Si el TIF
geografico es una reproyeccion del UTM, tiene una interpolacion MAS que el campo donde MIROVA detecta,
y validar nuestro campo (c) contra el TIF geografico premiaria un suavizado que MIROVA no tiene al
detectar. Este script compara la textura de pixel a pixel (sd de dL relativa a la media de L, y la
autocorrelacion a una celda de L sin tendencia) entre los TIF UTM y los geograficos de los dias
vecinos, por volcan. Es descriptivo: decide si la validacion de la sonda necesita una salvedad.

  python textura_utm_vs_geo.py
"""
import io, statistics as st, sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DL = RAIZ / "experiments" / "_s144_conteo_tif" / "_dl_tif"
BASE = DL / "da4fe36e8920"
sys.path.insert(0, str(RAIZ))
from pipeline.detection_context import _nanmean_8neighbors_fast  # noqa: E402


def textura(ruta):
    with rasterio.open(ruta) as ds:
        L = ds.read(1).astype(np.float64); crs = str(ds.crs)
        if ds.nodata is not None:
            L[L == ds.nodata] = np.nan
    L[~(L > 0)] = np.nan
    dL = L - _nanmean_8neighbors_fast(L)
    m = np.isfinite(dL); m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = False
    if m.sum() < 1000:
        return None
    # autocorrelacion a una celda (horizontal) de dL: 0 si el ruido es independiente celda a celda,
    # negativa si es ruido blanco pasado por el kernel, positiva si el campo viene suavizado
    a, b = dL[:, :-1], dL[:, 1:]
    mm = m[:, :-1] & m[:, 1:]
    x, y = a[mm] - a[mm].mean(), b[mm] - b[mm].mean()
    ac = float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum()))
    return {"crs": crs, "sd_dL_rel": float(np.std(dL[m]) / np.nanmean(L[m])), "ac1_dL": ac}


def main():
    ix = pd.read_csv(DL / "da4fe36e8920_index.csv")
    ix = ix[(ix.sensor == "VIIRS375") & ix.acquisition_utc.notna() & (ix.size_bytes > 0)].copy()
    ix["t"] = pd.to_datetime(ix.acquisition_utc, utc=True)
    v = ix[(ix.t >= "2026-09-12") & (ix.t < "2026-09-18")]
    filas = []
    for _, x in v.iterrows():
        f = BASE / x.tif_path
        if not f.exists():
            continue
        r = textura(f)
        if r:
            hora = x.t.hour + x.t.minute / 60
            r.update({"vol": x.volcano, "t": str(x.t), "noche": hora < 11})
            filas.append(r)
    df = pd.DataFrame(filas)
    df = df[df.noche]
    print("TIF nocturnos VIIRS 375 del 12 al 17 de septiembre leidos:", len(df))
    for crs, g in df.groupby("crs"):
        print("  %-11s n %3d | sd(dL)/L mediana %.4f | autocorrelacion a 1 celda de dL mediana %+.3f"
              % (crs, len(g), g.sd_dL_rel.median(), g.ac1_dL.median()))
    print("por volcan (mediana de cada sistema):")
    for vol, g in df.groupby("vol"):
        u = g[g.crs.str.startswith("EPSG:327")]; gg = g[g.crs == "EPSG:4326"]
        if len(u) and len(gg):
            print("  %-20s UTM n %d sd %.4f ac %+.3f | 4326 n %d sd %.4f ac %+.3f" % (
                vol, len(u), u.sd_dL_rel.median(), u.ac1_dL.median(), len(gg), gg.sd_dL_rel.median(), gg.ac1_dL.median()))


if __name__ == "__main__":
    main()
