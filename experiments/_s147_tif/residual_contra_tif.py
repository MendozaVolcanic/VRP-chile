"""S147 - en el regimen de HOY: hay calor, en la imagen de MIROVA, donde la replica publica y MIROVA calla?

DE DONDE SALE. Un agente con contexto limpio midio esto sobre la copia local del archivo de TIF
(2026-05-09 a 2026-05-20) y encontro que la imagen de MIROVA y la nuestra son la misma, y que en el
residual el pixel publicado esta a +0,31 K de su fondo (docs/audit_s147/INFORME_TIF_QUE_VE_MIROVA.md).
Pero mayo es anterior a #535 y a #571, que cambiaron el regimen de publicacion de VIIRS 375 (A104),
y en mayo produccion tenia el Test 1 integrado encendido. El agente lo declaro como lo que no pudo
medir. Este script repite la medicion central sobre la ventana del A/B (2026-09-01 a 2026-09-20) y
sobre el brazo SIN Test 1, con los TIF de septiembre bajados por la API de GitHub (sin pull: el
repo pesa 17 GB y un pull ya lleno el disco una vez; los 1.058 TIF de la ventana pesan 99 MB).

QUE SE MIDE, por pasada publicada del brazo sin Test 1:
  - la temperatura de brillo del pixel en nuestro record contra la de la MISMA celda en el TIF de
    MIROVA de esa pasada (inversion de Planck a 3,74 um): son la misma imagen?
  - el exceso del pixel sobre el fondo, en nuestro dato y en la imagen de MIROVA;
  - el percentil de la celda dentro de un disco de 5 km de la imagen de MIROVA, con su NULO medido
    sobre celdas sorteadas de la misma imagen (A110: un control se valida midiendo su nulo).

LAS CUATRO TRAMPAS DE ESTOS TIF, todas ya pagadas por el proyecto:
  1. El TIF no es VRP sumable (A24): aca solo se comparan radiancias celda a celda.
  2. El CRS cambia entre archivos (A106: hubo 8 adquisiciones en UTM el 14 y 15 de septiembre): se
     lee de CADA archivo y las coordenadas se transforman a ese CRS.
  3. La hora del nombre no es siempre la de la pasada: se usa SOLO `acquisition_utc`, y las filas
     que no la traen quedan fuera (se informa cuantas).
  4. El TIF sale del mismo granulo que nuestra deteccion (A109): esto DESCRIBE que hay en la imagen
     de MIROVA, no certifica nuestra deteccion.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si no hubiera diferencia entre lo que MIROVA alerto y lo que no, esto lo mostraria? SI: las dos
   columnas saldrian iguales. El control positivo son las pasadas que MIROVA SI alerto: ahi el
   pixel tiene que sobresalir, y si no sobresale el instrumento esta mal antes que cualquier otra cosa.
2. Si el instrumento estuviera muerto? El nulo (celdas al azar) tiene que dar percentil 0,50.

Uso: python experiments/_s147_tif/residual_contra_tif.py --brazo <dir con los JSON del brazo>
"""
from __future__ import annotations
import argparse
import json
import math
import random
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform as rio_transform

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo, clave  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

AQUI = Path(__file__).resolve().parent
CONGELADO = ROOT / "experiments" / "_s146_ab_sin_test1" / "_congelado"
VENTANA = ("2026-09-01", "2026-09-20")
TIF2VOL = {"ChillanNevadosde": "NevadosDeChillan"}
C1L, C2, LAM = 1.191042e8, 1.4387752e4, 3.74
TOL_S = 180


def bt_de_radiancia(L):
    return C2 / (LAM * math.log(1.0 + C1L / (LAM ** 5 * L))) if L and L > 0 else float("nan")


def indice_tif():
    ix = pd.read_csv(AQUI / "index_remoto.csv")
    ix = ix[(ix.sensor == "VIIRS375") & ix.acquisition_utc.notna()].drop_duplicates("tif_path")
    ix["t"] = pd.to_datetime(ix.acquisition_utc, utc=True, errors="coerce")
    ix["vol"] = ix.volcano.map(lambda v: TIF2VOL.get(v, v))
    ix["ruta"] = ix.tif_path.map(lambda p: AQUI / "tif" / p.replace("data/tif/", ""))
    return ix[ix.ruta.map(lambda p: p.exists())]


def celda(ds, lat, lon):
    xs, ys = rio_transform("EPSG:4326", ds.crs, [lon], [lat])
    r, c = ds.index(xs[0], ys[0])
    return (r, c) if 0 <= r < ds.height and 0 <= c < ds.width else None


def medir(ds, arr, lat, lon, rng):
    rc = celda(ds, lat, lon)
    if rc is None:
        return None
    r, c = rc
    v = arr[r, c]
    if not np.isfinite(v) or v <= 0:
        return None
    px = abs(ds.transform.a) * (111.32 * math.cos(math.radians(lat)) if ds.crs.is_geographic else 0.001)
    rad = max(3, int(round(5.0 / px)))
    yy, xx = np.ogrid[:ds.height, :ds.width]
    disco = ((yy - r) ** 2 + (xx - c) ** 2 <= rad ** 2) & np.isfinite(arr) & (arr > 0)
    vals = arr[disco]
    if vals.size < 30:
        return None
    # fondo de la imagen de MIROVA: mediana del anillo de 2 a 5 km alrededor de la celda
    anillo = disco & ((yy - r) ** 2 + (xx - c) ** 2 >= (0.4 * rad) ** 2)
    fondo = float(np.median(arr[anillo])) if anillo.sum() >= 20 else float("nan")
    # nulo: el mismo percentil para celdas sorteadas de la misma imagen, lejos de la nuestra
    nulos = []
    validas = np.argwhere(np.isfinite(arr) & (arr > 0))
    for _ in range(40):
        rr, cc = validas[rng.randrange(len(validas))]
        if (rr - r) ** 2 + (cc - c) ** 2 < (1.2 * rad) ** 2:
            continue
        d2 = ((yy - rr) ** 2 + (xx - cc) ** 2 <= rad ** 2) & np.isfinite(arr) & (arr > 0)
        if d2.sum() >= 30:
            nulos.append(float((arr[d2] < arr[rr, cc]).mean()))
    return {"bt_mirova": bt_de_radiancia(float(v)), "bt_fondo_mirova": bt_de_radiancia(fondo),
            "percentil": float((vals < v).mean()), "nulo": st.median(nulos) if nulos else None,
            "es_maximo": bool(v >= vals.max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brazo", required=True)
    a = ap.parse_args()
    rng = random.Random(147)

    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONGELADO / "registro_vrp_consolidado.csv",
                                        CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)
    recs = cargar_brazo(a.brazo, coords, inner, VENTANA)
    bp.etiquetar(recs, por_vb, ns, nv)
    raw = {}
    for vol in bp.VOLS:
        p = Path(a.brazo) / f"{vol}.json"
        if p.exists():
            for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
                b = bp.bucket(r.get("sensor"))
                if b:
                    raw[(vol, b, r.get("datetime_utc"))] = r

    ix = indice_tif()
    print(f"TIF de VIIRS 375 con hora de adquisicion y archivo en disco: {len(ix)}")
    out = {"pos": [], "neg_limpio": []}
    sin_tif = 0
    for r in recs:
        if r["b"] != "VIIRS375" or not r["pub"] or r["lab"] not in out:
            continue
        x = raw.get(clave(r))
        px = sorted((x or {}).get("anomaly_pixels") or [], key=lambda p: -(p.get("vrp_mw") or 0))
        if not px:
            continue
        p0 = px[0]
        cand = ix[(ix.vol == r["vol"]) & ((ix.t - r["dt"]).abs().dt.total_seconds() <= TOL_S)]
        if cand.empty:
            sin_tif += 1
            continue
        with rasterio.open(cand.iloc[0].ruta) as ds:
            arr = ds.read(1).astype("float64")
            m = medir(ds, arr, p0["lat"], p0["lon"], rng)
        if m is None:
            continue
        m.update({"bt_nuestro": p0.get("bt_k"), "t_bg": x.get("t_bg_k"), "vol": r["vol"],
                  "zen": x.get("sensor_zenith_deg")})
        out[r["lab"]].append(m)

    print(f"pasadas publicadas sin TIF de esa misma pasada (a +-{TOL_S} s): {sin_tif}\n")
    med = lambda xs: round(st.median([v for v in xs if v is not None and v == v]), 3) \
        if [v for v in xs if v is not None and v == v] else None
    print(f"{'':58} {'MIROVA alerto':>15} {'MIROVA no vio nada':>20}")
    print(f"{'n':58} {len(out['pos']):>15} {len(out['neg_limpio']):>20}")
    filas_t = [
        ("BT de MIROVA menos BT nuestra en la misma celda, K (mediana)",
         lambda m: m["bt_mirova"] - m["bt_nuestro"] if m["bt_nuestro"] else None),
        ("exceso del pixel sobre el fondo, EN NUESTRO DATO, K (mediana)",
         lambda m: m["bt_nuestro"] - m["t_bg"] if m["bt_nuestro"] and m["t_bg"] else None),
        ("exceso de la celda sobre su anillo, EN LA IMAGEN DE MIROVA, K",
         lambda m: m["bt_mirova"] - m["bt_fondo_mirova"]),
        ("percentil de la celda en el disco de 5 km de MIROVA (mediana)", lambda m: m["percentil"]),
        ("  NULO del percentil: celdas al azar de la misma imagen", lambda m: m["nulo"]),
    ]
    for nombre, f in filas_t:
        print(f"{nombre:58} {str(med([f(m) for m in out['pos']])):>15} "
              f"{str(med([f(m) for m in out['neg_limpio']])):>20}")
    for nombre, f in (("pixel MAS FRIO que nuestro propio fondo",
                       lambda m: (m["bt_nuestro"] - m["t_bg"]) < 0 if m["bt_nuestro"] and m["t_bg"] else None),
                      ("pixel excede el fondo en mas de 3 K",
                       lambda m: (m["bt_nuestro"] - m["t_bg"]) > 3 if m["bt_nuestro"] and m["t_bg"] else None),
                      ("la celda es el MAXIMO de su disco de 5 km en MIROVA", lambda m: m["es_maximo"])):
        fila = f"{nombre:58}"
        for lab in ("pos", "neg_limpio"):
            v = [f(m) for m in out[lab]]
            v = [q for q in v if q is not None]
            fila += f"{(str(round(100 * sum(v) / len(v), 1)) + '% de ' + str(len(v))) if v else 'n/a':>{15 if lab == 'pos' else 20}}"
        print(fila)


if __name__ == "__main__":
    main()
