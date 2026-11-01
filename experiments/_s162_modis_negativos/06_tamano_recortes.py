# -*- coding: utf-8 -*-
"""S162 MODIS negativos, paso 6: tamano en disco de los recortes nativos que guarda envoltorio_nativo.py.

Lo MEDIDO: bytes por pixel sin comprimir (48, de los tipos reales de cada capa, 05_prueba_envoltorio_salida.txt) y
el tamano de la grilla 51 x 51 que ya guardaba S159 (los grilla_*.npz del artefacto del run 39712862945).
Lo ESTIMADO (no hay granulo MODIS real en Windows: pyhdf no corre aqui): la forma del recorte de cada pasada, con un
modelo geometrico del barrido MODIS y la ventana de probe_portes._ventana (pixeles a < 60 km del centro, submuestra
de 1 en 8, margen de -8 y +16 lineas y columnas):
  - columnas: frames cuyo centro cae a < 60 km a lo largo del barrido; el tamano del pixel a lo largo del barrido
    crece con el angulo de barrido (orbita de 705 km, IFOV 1/705 rad, Tierra esferica de 6.371 km);
  - lineas: 120 (una por km de avance de la orbita) mas 9 veces el tamano del pixel a lo largo de la traza en ese
    angulo (los barridos de los bordes de la ventana entran enteros: el bow tie) mas el margen de 24.
No recorta por el borde del granulo ni del barrido: es una cota por arriba del recorte real. La compresion se
informa con la del granulo sintetico, que es mas compresible que uno real: el numero que planifica es el SIN
comprimir.

Uso: python -I 06_tamano_recortes.py [--art D:\\vrp-trabajo\\temporales\\s159_portes\\run_39712862945]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
R, H = 6371.0, 705.0
IFOV = 1.0 / H
BYTES_PX = 48.0          # medido: 05_prueba_envoltorio_salida.txt («48.0 por pixel»)
COMP_SINT = 20.9 / 48.0  # medido en el sintetico (cota optimista de compresion)
RADIO = 60.0             # probe_portes._ventana: radio + 15 = 45 + 15 km


def theta_de_z(z):
    return math.asin(R / (R + H) * math.sin(math.radians(z)))


def s_de_theta(t):
    z = math.asin((R + H) / R * math.sin(t))
    return R * (z - t)


def theta_de_s(s):
    lo, hi = 0.0, math.radians(56.0)
    for _ in range(60):
        m = (lo + hi) / 2
        if s_de_theta(m) < s:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def along_track(t):
    z = math.asin((R + H) / R * math.sin(t))
    rho = R * math.sin(z - t) / math.sin(t) if t > 1e-9 else H
    return rho * IFOV


def forma(z):
    t = theta_de_z(z)
    sv = s_de_theta(t)
    t_hi = theta_de_s(sv + RADIO)
    t_lo = theta_de_s(sv - RADIO) if sv > RADIO else -theta_de_s(RADIO - sv)
    cols = (t_hi - t_lo) / IFOV + 24
    rows = 120 + 9 * along_track(max(abs(t_hi), abs(t_lo))) + 24
    return int(math.ceil(rows)), int(math.ceil(cols))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", default=r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")
    a = ap.parse_args()
    print("control del modelo: nadir", forma(0.0), "| z 30", forma(30.0), "| z 50", forma(50.0), "| z 65", forma(65.0))
    print("  (el sintetico de 1 km sin bow tie dio 136 x 136; el modelo en nadir tiene que dar algo mayor por el bow tie)")
    obj = json.loads((AQUI / "objetivos_neg_resto_modis.json").read_text(encoding="utf-8"))
    zs = [o["z"] for o in obj]
    sin_z = sum(z is None for z in zs)
    zs = [z for z in zs if z is not None]
    px = np.array([np.prod(forma(z)) for z in zs], float)
    crudo = px * BYTES_PX
    print(f"\npasadas del lote: {len(obj)} (sin cenit: {sin_z}); cenit del sensor: min {min(zs):.1f}, mediana "
          f"{np.median(zs):.1f}, max {max(zs):.1f}")
    print(f"pixeles por recorte (cota): mediana {np.median(px):.0f}, max {px.max():.0f}")
    print(f"recorte SIN comprimir por pasada: mediana {np.median(crudo) / 1e6:.2f} MB, max {crudo.max() / 1e6:.2f} MB; "
          f"total {crudo.sum() / 1e6:.0f} MB (cota para planificar)")
    print(f"comprimido con la razon del sintetico ({COMP_SINT:.2f}): total ~{crudo.sum() * COMP_SINT / 1e6:.0f} MB "
          f"(optimista)")
    g = sorted(Path(a.art).rglob("grilla_*.npz"))
    gm = [f for f in g if "MODIS" in f.parent.name]
    if gm:
        tb = np.mean([f.stat().st_size for f in gm])
        print(f"grilla 51 x 51 que ya se guardaba (S159, {len(gm)} archivos MODIS): {tb / 1e3:.1f} KB por pasada -> "
              f"{tb * len(obj) / 1e6:.0f} MB en el lote")
    else:
        print("grillas de S159: SIN DATO (no se encontro el artefacto)")
    print(f"total del artefacto del lote (cota): ~{(crudo.sum() + (tb * len(obj) if gm else 0)) / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
