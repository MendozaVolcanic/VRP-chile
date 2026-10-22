# -*- coding: utf-8 -*-
"""V02 (verificador S160 espacial): georreferencia de los GeoTIFF VIIRS 375 de MIROVA (archivo local mirova-tif-archive,
solo lectura) por dos caminos:
 (1) RELATIVO (solo TIF nocturnos, hora de adquisicion 03-10 UTC del indice remoto, md5 unico): 3 TIF al azar por volcan (semilla 160) contra la mediana de todos los TIF 4326 del mismo volcan: el
     desplazamiento entero (filas, cols) que maximiza la correlacion del campo de BT nocturno (el relieve frio/tibio es un
     rasgo fijo: cumbres frias, valles tibios). Si un TIF estuviera corrido 1 pixel (~375 m) respecto del resto, aparece.
 (2) ABSOLUTO: rasgo fijo con coordenada conocida independiente de MIROVA: el crater activo de Lascar (vent_lat/lon de
     volcanoes.yaml). En 3 TIF de Lascar elegidos al azar entre los que tienen un maximo local muy prominente (residuo de
     mediana movil 9x9 >= 8 sigma, sin mirar etiqueta de MIROVA), el pixel del maximo debe caer a <= 1 pixel (~0,4 km) del
     vent. Ademas la cuenta sobre TODOS los TIF de Lascar con >= 8 sigma.
P1: un TIF sintetico corrido 2 pixeles (np.roll) debe dar desplazamiento (2, 0) en el paso (1): control positivo del metodo.
P2: se imprime n de TIF leidos y descartados (no 4326, > 50 % NaN).
"""
from __future__ import annotations

import glob
import hashlib
import io
import os
import pandas as pd
import random
import sys
from pathlib import Path

import numpy as np
import rasterio
import yaml
from pyproj import Geod
from scipy.ndimage import median_filter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
ARCH = ROOT.parent / "mirova-tif-archive" / "data" / "tif"
G = Geod(ellps="WGS84")


def leer(f):
    with rasterio.open(f) as ds:
        if not ds.crs or ds.crs.to_epsg() != 4326:
            return None
        a = ds.read(1).astype(float)
        a[~np.isfinite(a) | (a <= 0)] = np.nan
        if np.isnan(a).mean() > 0.5:
            return None
        return a, ds.transform, ds.bounds, ds.res


def mejor_shift(a, ref, m=4):
    best = None
    for di in range(-m, m + 1):
        for dj in range(-m, m + 1):
            b = np.roll(np.roll(a, di, 0), dj, 1)
            s = slice(m, -m)
            x, y = b[s, s].ravel(), ref[s, s].ravel()
            ok = np.isfinite(x) & np.isfinite(y)
            if ok.sum() < 1000:
                continue
            c = np.corrcoef(x[ok], y[ok])[0, 1]
            if best is None or c > best[0]:
                best = (c, -di, -dj)
    return best


PAT = ["../mirova-tif-archive/data/tif/{v}/*VIIRS375*.tif", "experiments/_s147_tif/tif/{v}/*.tif",
       "experiments/_s144_conteo_tif/_dl_tif/*/data/tif/{v}/*.tif",
       "experiments/_s139_audit/distancia_tif/_dl_/data/tif/{v}/*VIIRS375*.tif", "experiments/_s142_ndc/_dl_tif/{v}/*.tif"]


def nocturnos(v, ix):
    """TIF VIIRS 375 unicos (md5) del volcan cuya hora de adquisicion (indice remoto) cae entre 03 y 10 UTC (noche en Chile)."""
    vistos, md5s, out = set(), set(), []
    for pt in PAT:
        for f in sorted(glob.glob(str(ROOT / pt.format(v=v)))):
            base = os.path.basename(f).replace("_lm", "")
            if base in vistos or "VIIRS375" not in base:
                continue
            vistos.add(base)
            h = hashlib.md5(open(f, "rb").read()).hexdigest()
            if h in md5s:
                continue
            md5s.add(h)
            row = ix[ix.base == base]
            if not len(row) or pd.isna(row.iloc[0].acq):
                continue
            if 3 <= row.iloc[0].acq.hour < 10:
                out.append(f)
    return out


def main():
    rnd = random.Random(160)
    ix = pd.read_csv(ROOT / "experiments/_s147_tif/index_remoto.csv")
    ix = ix[ix.sensor == "VIIRS375"].copy()
    ix["base"] = ix.tif_path.apply(os.path.basename)
    ix["acq"] = pd.to_datetime(ix.acquisition_utc, errors="coerce", utc=True)
    vy = yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))
    vy = vy["volcanoes"] if isinstance(vy, dict) else vy
    vent = {v["name"]: (v["vent_lat"], v["vent_lon"]) for v in vy if "vent_lat" in v}
    print("(1) desplazamiento relativo contra la mediana del volcan")
    for v in ("Tupungatito", "PuyehueCordonCaulle", "Isluga", "Lascar"):
        fs = nocturnos(v, ix)
        datos = [(f, leer(f)) for f in fs]
        ok = [(f, d) for f, d in datos if d is not None]
        print(f"  {v}: TIF VIIRS 375 nocturnos unicos {len(fs)}, utiles 4326 {len(ok)}; resoluciones {sorted(set(tuple(round(r, 6) for r in d[3]) for _, d in ok))}; "
              f"bounds distintos {len(set(tuple(round(x, 5) for x in d[2]) for _, d in ok))}")
        ref = np.nanmedian(np.stack([d[0] for _, d in ok]), axis=0)
        # control positivo: la mediana corrida 2 filas
        print(f"     control: mediana corrida (2,0) -> {mejor_shift(np.roll(ref, 2, 0), ref)[1:]}")
        for f, d in rnd.sample(ok, 3):
            c, di, dj = mejor_shift(d[0], ref)
            print(f"     {Path(f).name}: desplazamiento (filas, cols) = ({di}, {dj}), r = {c:.3f}")
    print("\n(2) crater activo de Lascar como rasgo fijo absoluto (vent de volcanoes.yaml)")
    fs = nocturnos("Lascar", ix)
    fuertes = []
    for f in fs:
        d = leer(f)
        if d is None:
            continue
        a, T, b, res = d
        fill = np.where(np.isnan(a), np.nanmedian(a), a)
        r = fill - median_filter(fill, size=9, mode="nearest")
        r[np.isnan(a)] = np.nan
        sd = np.nanstd(r)
        i, j = np.unravel_index(np.nanargmax(r), r.shape)
        if r[i, j] / sd < 8:
            continue
        lon, lat = rasterio.transform.xy(T, i, j)
        az, _, dm = G.inv(vent["Lascar"][1], vent["Lascar"][0], lon, lat)
        fuertes.append((Path(f).name, round(r[i, j] / sd, 1), round(dm / 1000, 2), round(az % 360)))
    print(f"  TIF de Lascar con maximo >= 8 sigma: {len(fuertes)}; distancia del maximo al vent: p50 "
          f"{np.median([x[2] for x in fuertes]):.2f} km; <= 0,4 km {sum(x[2] <= 0.4 for x in fuertes)}; <= 1 km {sum(x[2] <= 1 for x in fuertes)}")
    for x in rnd.sample(fuertes, min(3, len(fuertes))):
        print(f"     al azar: {x[0]} prominencia {x[1]} sigma, maximo a {x[2]} km del vent, rumbo {x[3]}")


if __name__ == "__main__":
    main()


def sesgo_lascar():
    """(3) Sesgo direccional absoluto: en TIF nocturnos de Lascar, maximo del residuo dentro de 5 km del vent con >= 8 sigma
    (sigma de toda la escena). Mediana del desplazamiento (este, norte) del pixel maximo respecto del vent, en km y en
    pixeles. Si la georreferencia tuviera un corrimiento sistematico, la mediana se alejaria de 0 mas de medio pixel."""
    ix = pd.read_csv(ROOT / "experiments/_s147_tif/index_remoto.csv")
    ix = ix[ix.sensor == "VIIRS375"].copy()
    ix["base"] = ix.tif_path.apply(os.path.basename)
    ix["acq"] = pd.to_datetime(ix.acquisition_utc, errors="coerce", utc=True)
    vy = yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))
    vy = vy["volcanoes"] if isinstance(vy, dict) else vy
    vl = next((v["vent_lat"], v["vent_lon"]) for v in vy if v["name"] == "Lascar")
    de, dn = [], []
    for f in nocturnos("Lascar", ix):
        d = leer(f)
        if d is None:
            continue
        a, T, b, res = d
        fill = np.where(np.isnan(a), np.nanmedian(a), a)
        r = fill - median_filter(fill, size=9, mode="nearest")
        r[np.isnan(a)] = np.nan
        sd = np.nanstd(r)
        rows, cols = np.indices(a.shape)
        lons, lats = rasterio.transform.xy(T, rows.ravel(), cols.ravel())
        lats, lons = np.array(lats).reshape(a.shape), np.array(lons).reshape(a.shape)
        _, _, dist = G.inv(np.full(a.shape, vl[1]), np.full(a.shape, vl[0]), lons, lats)
        m = (dist <= 5000) & np.isfinite(r)
        k = np.nanargmax(np.where(m, r, -np.inf))
        i, j = np.unravel_index(k, a.shape)
        if r[i, j] / sd < 8:
            continue
        dn.append((lats[i, j] - vl[0]) * 111.195)
        de.append((lons[i, j] - vl[1]) * 111.195 * np.cos(np.radians(vl[0])))
    print(f"\n(3) Lascar, maximo a <= 5 km del vent con >= 8 sigma: n = {len(de)} TIF nocturnos; desplazamiento mediano del maximo "
          f"respecto del vent: este {np.median(de):+.2f} km, norte {np.median(dn):+.2f} km "
          f"(pixel {0.003673*111.195*np.cos(np.radians(vl[0])):.2f} km E-O x {0.003391*111.195:.2f} km N-S); "
          f"|d| p50 {np.median(np.hypot(de, dn)):.2f} km")


sesgo_lascar()
