# -*- coding: utf-8 -*-
"""Tarea 1.14, parte D: el fondo de MIROVA medido en su propio campo de radiancia (GeoTIFF), pasada por pasada.

POR QUE: la parte A mide el factor de fondo con el OSF de 2025; la C, con el brazo de fondo por vecinos (D25)
de nuestro pipeline. Ninguna mira el fondo de MIROVA en 2026. El GeoTIFF VIIRS 375 que MIROVA publica de una
pasada es su campo de radiancia MIR ya remuestreado: la media de los 8 vecinos de la celda donde cae nuestro
pixel alertado (sin las celdas que ocupan nuestros otros alertados) es su definicion de fondo (Campus 2024,
D25). Comparada con el fondo que de verdad restamos, da F_bg en 2026 sin pasar por nuestro pipeline.

Limites (A24, A106, A109): el TIF no es VRP sumable y no trae la mascara de alertados, asi que de aca NO sale
el conteo de MIROVA, solo el fondo. Lectura LOCAL del archivo (sin pull, clone ni fetch): el checkout local
llega hasta el 2026-05-20, asi que la ventana es 2026-05-09 a 2026-05-20, regimen previo a #535.

Controles (escritos antes de correr esta parte):
  T1 atribucion: mediana de |BT del TIF (mejor celda 3x3) - bt nuestro| <= 1 K por pasada, si no se descarta.
  T2 campo comun: mediana de la radiancia del TIF a 5-25 km del volcan contra L(t_bg_k) de nuestro anillo,
     razon dentro de +-3 % en >= 80 % de las pasadas atribuidas. Si falla, el TIF no es comparable y F_bg_TIF
     queda SIN DATO.
Uso:  python d_tif_fondo.py [--tif-dir RUTA_ARCHIVO_TIF]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(AQUI))

import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
import comun as C  # noqa: E402
from b_regimen_actual import fila_alerta, MINIMA_V375  # noqa: E402

TIF_DEFECTO = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive")
ARCH2OURS = {"ChillanNevadosde": "NevadosDeChillan"}


def tif_bt(L):
    lam = C.LAM["VIIRS375"]
    return C.C2 / (lam * math.log(1.0 + C.C1 / (lam ** 5 * L))) if L > 0 else float("nan")


def km(lat, lon, lat0, lon0):
    x = (np.asarray(lon) - lon0) * 111.320 * math.cos(math.radians(lat0))
    y = (np.asarray(lat) - lat0) * 110.574
    return np.hypot(x, y)


def leer(path):
    with rasterio.open(path) as s:
        if not s.crs or not s.crs.is_geographic:
            return None
        a = s.read(1).astype("float64")
        h, w = a.shape
        rows, cols = np.mgrid[0:h, 0:w]
        xs, ys = rasterio.transform.xy(s.transform, rows.ravel(), cols.ravel())
    return {"a": a, "lat": np.asarray(ys).reshape(h, w), "lon": np.asarray(xs).reshape(h, w), "fin": np.isfinite(a) & (a > 0)}


def celda(R, lat, lon):
    d = km(R["lat"], R["lon"], lat, lon)
    k = int(np.argmin(d))
    r, c = np.unravel_index(k, d.shape)
    return (int(r), int(c)) if d[r, c] <= 0.375 else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tif-dir", default=str(TIF_DEFECTO))
    a = ap.parse_args(argv)
    tdir = Path(a.tif_dir)
    ix = pd.read_csv(tdir / "index.csv")
    ix = ix[(ix.sensor == "VIIRS375") & ix.acquisition_utc.notna() & (ix.size_bytes > 0)].copy()
    ix["vol"] = ix.volcano.map(lambda v: ARCH2OURS.get(v, v))
    ix["acq"] = pd.to_datetime(ix.acquisition_utc, utc=True)
    spread = ix.groupby(["vol", "md5"]).acq.agg(lambda s: (s.max() - s.min()).total_seconds())
    ambiguos = set(spread[spread > 120].index)
    ix = ix[[(v, m) not in ambiguos for v, m in zip(ix.vol, ix.md5)]]
    ventana = (ix.acq.min().strftime("%Y-%m-%d"), ix.acq.max().strftime("%Y-%m-%d"))
    coords = BP._coords_por_volcan()
    filas_ref = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
    por_vb, _, _, _ = BP.indexar_referencia(filas_ref, coords, ventana)
    out = {"ventana_tif_local": ventana, "md5_ambiguos": len(ambiguos), "pasadas": [], "motivos": Counter()}
    for vol in C.VOLS:
        ixv = ix[ix.vol == vol]
        if ixv.empty:
            continue
        lat0, lon0 = coords[vol]
        for r in json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
            if C.bucket(r.get("sensor")) != "VIIRS375" or not (ventana[0] <= r["datetime_utc"][:10] <= ventana[1]):
                continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            if BP.es_pasada_diurna_descartada("VIIRS375", lat0, lon0, dt):
                continue
            al = fila_alerta(BP.parear(por_vb.get((vol, "VIIRS375"), []), dt))
            if al is None or al["vrp_mw"] <= MINIMA_V375:
                continue
            c = ixv[(ixv.acq - pd.Timestamp(dt)).abs().dt.total_seconds() <= 120]
            if c.empty:
                out["motivos"]["sin_tif"] += 1
                continue
            R = leer(tdir / c.sort_values("captured_at_utc").iloc[0].tif_path)
            if R is None:
                out["motivos"]["tif_no_geografico"] += 1
                continue
            px_all = [p for p in r.get("anomaly_pixels") or [] if p.get("lat") is not None]
            pos = [p for p in px_all if p.get("dist_km") is not None and p["dist_km"] <= C.INNER[vol]
                   and (p.get("vrp_mw") or 0) > 0 and p.get("bt_k")]
            if not pos:
                out["motivos"]["sin_pixeles_inner"] += 1
                continue
            ocup = {celda(R, p["lat"], p["lon"]) for p in px_all} - {None}
            h, w = R["a"].shape
            dbt, num, den, nvec = [], 0.0, 0.0, []
            for p in pos:
                rc = celda(R, p["lat"], p["lon"])
                if rc is None:
                    continue
                r0, c0 = rc
                cand = [tif_bt(R["a"][i, j]) - p["bt_k"] for i in range(max(0, r0 - 1), min(h, r0 + 2))
                        for j in range(max(0, c0 - 1), min(w, c0 + 2)) if R["fin"][i, j]]
                if cand:
                    dbt.append(min(cand, key=abs))
                vec = [R["a"][i, j] for i in range(max(0, r0 - 1), min(h, r0 + 2)) for j in range(max(0, c0 - 1), min(w, c0 + 2))
                       if (i, j) != (r0, c0) and (i, j) not in ocup and R["fin"][i, j]]
                if not vec:
                    continue
                L = C.planck(p["bt_k"], "VIIRS375")
                lbg_ours = L - p["vrp_mw"] * 1e6 / C.KA["VIIRS375"]
                lbk = float(np.mean(vec))
                num += L - lbg_ours
                den += L - lbk
                nvec.append(len(vec))
            if not dbt:
                out["motivos"]["pixel_fuera_del_raster"] += 1
                continue
            d = km(R["lat"], R["lon"], lat0, lon0)
            anillo = R["a"][(d >= 5) & (d <= 25) & R["fin"]]
            lring = C.planck(r["t_bg_k"], "VIIRS375") if r.get("t_bg_k") else float("nan")
            fila = {"vol": vol, "t": r["datetime_utc"], "V_M": al["vrp_mw"], "dbt_med_K": float(np.median(np.abs(dbt))),
                    "anillo_tif_sobre_nuestro": float(np.median(anillo) / lring) if len(anillo) and lring > 0 else float("nan"),
                    "F_bg_tif": (num / den) if den > 0 and num > 0 else float("nan"), "n_px": len(pos),
                    "n_vecinos_med": float(np.median(nvec)) if nvec else 0}
            out["pasadas"].append(fila)
    pas = out["pasadas"]
    atrib = [f for f in pas if f["dbt_med_K"] <= 1.0]
    t2 = [abs(f["anillo_tif_sobre_nuestro"] - 1) <= 0.03 for f in atrib if np.isfinite(f["anillo_tif_sobre_nuestro"])]
    out["control_T1_atribucion"] = {"pasadas": len(pas), "atribuidas": len(atrib)}
    out["control_T2_campo_comun"] = {"n": len(t2), "frac_dentro_3pct": round(float(np.mean(t2)), 4) if t2 else None,
                                     "pasa": bool(t2) and float(np.mean(t2)) >= 0.80,
                                     "mediana_razon": round(float(np.nanmedian([f["anillo_tif_sobre_nuestro"] for f in atrib])), 4) if atrib else None}
    por = defaultdict(list)
    for f in atrib:
        if np.isfinite(f["F_bg_tif"]):
            por[f["vol"]].append(f["F_bg_tif"])
            por["todos"].append(f["F_bg_tif"])
    out["F_bg_tif_por_volcan"] = {}
    rng = np.random.default_rng(C.SEMILLA)
    for k, v in por.items():
        v = np.array(v)
        boots = [math.exp(np.log(rng.choice(v, len(v))).mean()) for _ in range(1000)]
        out["F_bg_tif_por_volcan"][k] = {"n": len(v), "gm": round(C.gm(v), 4),
                                         "ic": [round(float(np.percentile(boots, 2.5)), 4), round(float(np.percentile(boots, 97.5)), 4)]}
    out["motivos"] = dict(out["motivos"])
    (AQUI / "d_tif_fondo_salida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    txt = [f"ventana TIF local {ventana}; md5 ambiguos {len(ambiguos)}; motivos {out['motivos']}",
           f"T1 {out['control_T1_atribucion']}", f"T2 {out['control_T2_campo_comun']}",
           f"F_bg_TIF (fondo nuestro contra media de vecinos en el TIF de MIROVA): {out['F_bg_tif_por_volcan']}"]
    (AQUI / "d_tif_fondo_salida.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
