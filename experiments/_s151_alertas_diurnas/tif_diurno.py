# -*- coding: utf-8 -*-
"""Tarea 1.13 (estudio C), pregunta 2, via imagen: que muestra el GeoTIFF MIR de MIROVA de dia en el crater.

POR QUE. El GeoTIFF que MIROVA publica (I04, 3,74 um, para VIIRS 375) es el campo de radiancia MIR de la
pasada (A24: no es VRP sumable). De noche, un crater con calor se ve como un pico local sobre un fondo
frio y parejo. De dia el fondo es luz solar reflejada: si el crater se destaca IGUAL en todas las pasadas
diurnas, tenga o no alerta, lo que se ve es una superficie que brilla o se calienta con el Sol (campo
fumarolico, azufre, roca oscura), no un foco que aparece y desaparece.

QUE SE MIDE. Para cada TIF local de VIIRS 375 (solo lectura local: mirova-tif-archive SIN pull, mas las
copias que ya bajaron experimentos anteriores), el contraste del crater:
    S(p) = (max a <= 1,5 km de p  -  mediana del anillo 3 a 8 km) / (1,4826 * MAD del anillo)
y se le resta la mediana de S en 30 puntos al azar a 8-20 km del crater en el MISMO raster:
    D = S(crater) - mediana(S(azar)).
Control que se cancela por construccion (A110 c): D medido sobre un punto al azar contra los otros puntos
al azar del mismo raster; su mediana debe ser ~0. Si no lo es, el estadistico mide textura y no calor.
Control positivo: las pasadas NOCTURNAS en que la tabla de MIROVA publico alerta >= 1 MW (misma hora,
0 min) deben dar D claramente mayor que las nocturnas RUTINA.
Limite declarado: el archivo local solo tiene TIF diurnos del 2026-05-08 al 2026-05-20 y de algunas
fechas sueltas; las filas OCR caen 18 min antes que el TIF mas cercano, y ese TIF es OTRA pasada
(reference_ocr_imagen_de_otra_pasada; A106), asi que una alerta OCR diurna NO tiene su propia imagen aca.
Salida: tif_diurno_salida.txt.
"""
from __future__ import annotations

import io
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np  # noqa: E402
import rasterio  # noqa: E402
import yaml  # noqa: E402
from rasterio.warp import transform as warp_transform  # noqa: E402

from pipeline.store import _solar_elevation  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402

AQUI = Path(__file__).resolve().parent
VOLC = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia")
FUENTES = [VOLC / "mirova-tif-archive" / "data" / "tif",
           VOLC / "VRP Chile" / "experiments"]
ALIAS = {"ChillanNevadosde": "NevadosDeChillan"}
VOLCANES = ("Lascar", "Lastarria", "Isluga")
PAT = re.compile(r"[\\/]([A-Za-z]+)[\\/](2026\d{4}_\d{6})_VIIRS375\.tif$")
RNG = np.random.default_rng(1513)


def listar_tifs():
    vistos = {}
    for base in FUENTES:
        for dirpath, _d, files in os.walk(base):
            for fn in files:
                ruta = os.path.join(dirpath, fn)
                m = PAT.search(ruta)
                if not m:
                    continue
                vol = ALIAS.get(m.group(1), m.group(1))
                if vol not in VOLCANES:
                    continue
                vistos.setdefault((vol, m.group(2)), ruta)
    return vistos


def km_grid(src, lat, lon):
    """Distancias en km de cada pixel a (lat, lon), en el CRS del raster."""
    h, w = src.height, src.width
    cols, rows = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    xs, ys = rasterio.transform.xy(src.transform, rows.ravel(), cols.ravel(), offset="ul")
    xs, ys = np.asarray(xs).reshape(h, w), np.asarray(ys).reshape(h, w)
    if src.crs.to_epsg() == 4326:
        dy = (ys - lat) * 111.32
        dx = (xs - lon) * 111.32 * np.cos(np.radians(lat))
    else:
        (px,), (py,) = warp_transform("EPSG:4326", src.crs, [lon], [lat])
        dx, dy = (xs - px) / 1000.0, (ys - py) / 1000.0
    return dx, dy


def S(a, dx, dy, x0, y0):
    d = np.hypot(dx - x0, dy - y0)
    nucleo = a[(d <= 1.5) & np.isfinite(a)]
    anillo = a[(d >= 3) & (d <= 8) & np.isfinite(a)]
    if nucleo.size == 0 or anillo.size < 30:
        return None
    mad = 1.4826 * np.median(np.abs(anillo - np.median(anillo)))
    if mad <= 0:
        return None
    return (nucleo.max() - np.median(anillo)) / mad


def medir(ruta, lat, lon):
    with rasterio.open(ruta) as src:
        a = src.read(1).astype(float)
        dx, dy = km_grid(src, lat, lon)
    sc = S(a, dx, dy, 0.0, 0.0)
    if sc is None:
        return None
    nulos = []
    for _ in range(200):
        if len(nulos) >= 30:
            break
        r, th = RNG.uniform(8, 20), RNG.uniform(0, 2 * np.pi)
        v = S(a, dx, dy, r * np.cos(th), r * np.sin(th))
        if v is not None:
            nulos.append(v)
    if len(nulos) < 10:
        return None
    nulos = np.array(nulos)
    # control que se cancela: un punto al azar contra los demas puntos al azar
    ctrl = nulos[0] - np.median(nulos[1:])
    return sc - np.median(nulos), ctrl


def main():
    out = []
    p = out.append
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        co = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}
    ref = {}
    for f in cargar_referencia_unificada():
        if f["sensor_bucket"] != "VIIRS375" or f["source"] != "CONS":
            continue
        ref[(f["volcano"], f["fecha_utc"][:16])] = f
    tifs = listar_tifs()
    p("TIF VIIRS 375 locales de %s: %d" % (", ".join(VOLCANES), len(tifs)))
    grupos = defaultdict(list)
    ctrls = []
    por_stamp = {}
    for (vol, stamp), ruta in sorted(tifs.items()):
        dt = datetime.strptime(stamp, "%Y%m%d_%H%M%S")
        lat, lon = co[vol]
        dia = _solar_elevation(lat, lon, dt) > 0
        fila = ref.get((vol, dt.strftime("%Y-%m-%d %H:%M")))
        if fila is None:
            etiqueta = "sin fila de tabla a la misma hora"
        elif alerta_protegida(fila, lectura="A"):
            etiqueta = "tabla: alerta >= 1 MW"
        elif fila["tipo"] == "ALERTA_TERMICA":
            etiqueta = "tabla: alerta < 1 MW"
        elif fila["tipo"] == "RUTINA":
            etiqueta = "tabla: RUTINA"
        else:
            etiqueta = "tabla: " + fila["tipo"]
        try:
            r = medir(ruta, lat, lon)
        except Exception as e:  # noqa: BLE001
            p("   error %s: %s" % (ruta, e))
            continue
        if r is None:
            continue
        D, c = r
        ctrls.append(c)
        por_stamp[(vol, dt)] = (D, etiqueta)
        grupos[(vol, "dia" if dia else "noche", etiqueta)].append(D)
        grupos[(vol, "dia" if dia else "noche", "TODAS")].append(D)
    p("Control que se cancela (punto al azar contra los demas, %d rasters): mediana %.3f, p10 %.3f, p90 %.3f"
      % (len(ctrls), np.median(ctrls), np.percentile(ctrls, 10), np.percentile(ctrls, 90)))
    p("\nD = contraste del crater menos mediana de 30 puntos al azar (unidades de MAD del anillo)")
    p("   %-10s %-6s %-36s %5s %8s %8s %8s %10s" % ("volcan", "luz", "grupo", "n", "p25", "mediana", "p75", "frac D>3"))
    for k in sorted(grupos):
        x = np.array(grupos[k])
        p("   %-10s %-6s %-36s %5d %8.2f %8.2f %8.2f %10.2f" % (k[0], k[1], k[2], len(x), np.percentile(x, 25),
                                                              np.median(x), np.percentile(x, 75), np.mean(x > 3)))
    # Alertas diurnas de la poblacion con un TIF de la MISMA hora (0 min) o 18 min despues (otra pasada).
    import json
    dia = json.load(open(AQUI / "poblacion_filas.json", encoding="utf-8"))["dia"]
    p("\nAlertas diurnas de %s con TIF local a 0 min o a +18 min (esta ultima es OTRA pasada):" % ", ".join(VOLCANES))
    for f in dia:
        if f["volcano"] not in VOLCANES or f["sensor_bucket"] != "VIIRS375":
            continue
        t = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S")
        for (vol, dt), (D, et) in por_stamp.items():
            off = (dt - t).total_seconds() / 60.0
            if vol == f["volcano"] and (abs(off) <= 1 or abs(off - 18) <= 1):
                p("   %s %-9s %-4s %6.2f MW  TIF %+5.1f min  D = %6.2f  (%s)" % (
                    f["fecha_utc"][:16], vol, f["source"], f["vrp_mw"], off, D, et))
    (AQUI / "tif_diurno_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
