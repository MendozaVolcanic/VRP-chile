# -*- coding: utf-8 -*-
"""S159 frente GEO, parte R: inventario de la georreferencia de los TIF de MIROVA por volcan, sensor y epoca.

POR QUE: la ROI y la grilla de MIROVA por volcan pueden estar escritas en los encabezados de sus GeoTIFF. A106
dice que los VIIRS 375 fueron UTM nativo solo del 2026-09-14 06:36 al 2026-09-15 06:24; nadie miro si los
VIIRS 750 y MODIS de esa ventana tambien lo fueron, ni si la caja cambia entre volcanes o en el tiempo.

Instrumento (las dos preguntas):
1. Si la georreferencia cambiara entre volcanes o meses, esta medicion lo veria: lee CRS, transformada,
   ancho y alto de cada archivo y los tabula. Si el archivo bajado no fuera el del indice, se ve por md5.
2. Si la descarga estuviera muerta (archivo vacio, HTML de error), rasterio falla y la fila queda ERROR,
   no se confunde con "sin cambio".
Muestra: hasta 2 archivos de md5 distinto por volcan, sensor y mes (mayo a septiembre de 2026), mas TODOS los
archivos con last_modified entre 2026-09-13 18:00 y 2026-09-16 00:00 UTC (la ventana UTM de A106 y sus bordes).

Uso: python -I r1_inventario_tif.py <carpeta descargas> <csv salida>
"""
import hashlib
import os
import subprocess
import sys

import pandas as pd
import rasterio

REPO = "MendozaVolcanic/mirova-tif-archive"


def bajar(ruta, destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    r = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                        f"repos/{REPO}/contents/{ruta}"], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[:200])
    with open(destino, "wb") as f:
        f.write(r.stdout)


def muestra(idx):
    idx = idx.copy()
    idx["lm"] = pd.to_datetime(idx.last_modified_utc)
    idx["mes"] = idx.lm.dt.month
    filas = []
    for (_, _, _), g in idx.groupby(["volcano", "sensor", "mes"]):
        g = g.drop_duplicates("md5").sort_values("lm")
        if len(g) == 0:
            continue
        sel = [g.iloc[0]]
        if len(g) > 1:
            sel.append(g.iloc[len(g) // 2])
        filas += sel
    ven = idx[(idx.lm >= "2026-09-13T18:00:00Z") & (idx.lm <= "2026-09-16T00:00:00Z")]
    filas += [r for _, r in ven.iterrows()]
    m = pd.DataFrame(filas).drop_duplicates("tif_path")
    return m


def main(descargas, salida):
    idx = pd.read_csv(os.path.join(descargas, "index.csv"))
    m = muestra(idx)
    print(f"muestra: {len(m)} archivos", file=sys.stderr)
    out = []
    for _, r in m.iterrows():
        dest = os.path.join(descargas, r.tif_path.replace("/", os.sep))
        fila = dict(volcano=r.volcano, sensor=r.sensor, acquisition_utc=r.acquisition_utc,
                    last_modified_utc=r.last_modified_utc, md5_indice=r.md5, tif_path=r.tif_path)
        try:
            bajar(r.tif_path, dest)
            fila["md5_archivo"] = hashlib.md5(open(dest, "rb").read()).hexdigest()
            with rasterio.open(dest) as s:
                t = s.transform
                fila.update(epsg=s.crs.to_epsg() if s.crs else None, ancho=s.width, alto=s.height,
                            a=t.a, b=t.b, c=t.c, d=t.d, e=t.e, f=t.f, dtype=s.dtypes[0], nodata=s.nodata,
                            nbandas=s.count, tags=";".join(f"{k}={v}" for k, v in s.tags().items())[:300],
                            desc=str(s.descriptions)[:80])
                a = s.read(1)
                fila.update(vmin=float(a.min()), vmax=float(a.max()))
        except Exception as ex:  # noqa: BLE001
            fila["error"] = str(ex)[:200]
        out.append(fila)
    pd.DataFrame(out).to_csv(salida, index=False)
    print(f"escrito {salida}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
