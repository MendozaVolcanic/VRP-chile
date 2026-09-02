"""Librería común del eje ground-truth exógeno S131 (read-only).

POR QUÉ: la auditoría necesita emparejar PASADA a PASADA nuestras detecciones
con el archivo TIF/KMZ de MIROVA. Toda la lógica de nombres, familias de sensor
y carga de datos vive acá para que las 5 mediciones usen exactamente el mismo
universo (A90: mismo denominador y misma ventana en todas las tablas).
"""
import io
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

import pandas as pd
import yaml

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ARCHIVE = os.path.abspath(os.path.join(REPO, "..", "mirova-tif-archive"))
OUT = os.path.join(REPO, "experiments", "_s131_audit", "ground_truth")

TIER_A = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
          "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
          "Tupungatito", "Villarrica"]

# El archivo MIROVA usa el nombre-código de mirovaweb; nosotros el nuestro.
ARCH2OURS = {"ChillanNevadosde": "NevadosDeChillan"}
OURS2ARCH = {v: k for k, v in ARCH2OURS.items()}


def arch_name(v):
    return OURS2ARCH.get(v, v)


def our_name(v):
    return ARCH2OURS.get(v, v)


def sensor_family(s):
    """Convención del proyecto (A48): VIIRS_<plat> sin sufijo = I-band 375 m."""
    if s is None:
        return None
    s = str(s)
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def load_volcanoes():
    y = yaml.safe_load(open(os.path.join(REPO, "volcanoes.yaml"), encoding="utf-8"))
    return {v["name"]: v for v in y["volcanoes"]}


def load_records(volcanoes=None, start=None, end=None):
    """Records nuestros de mirova_equivalent, opcionalmente acotados en fecha."""
    rows = []
    for v in (volcanoes or TIER_A):
        p = os.path.join(REPO, "data", "mirova_equivalent", f"{v}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        for r in d["records"]:
            dt = pd.to_datetime(r["datetime_utc"], utc=True, errors="coerce")
            if pd.isna(dt):
                continue
            if start is not None and dt < start:
                continue
            if end is not None and dt > end:
                continue
            r = dict(r)
            r["volcano"] = v
            r["dt"] = dt
            r["family"] = sensor_family(r.get("sensor"))
            rows.append(r)
    return pd.DataFrame(rows)


_TS_RE = re.compile(r"(\d{8}_\d{6})")


def load_tif_index():
    """index.csv deduplicado por md5 (misma adquisición republicada = 1 pasada)."""
    d = pd.read_csv(os.path.join(ARCHIVE, "index.csv"))
    d["volcano"] = d["volcano"].map(our_name)
    # timestamp efectivo de adquisición: acquisition_utc si existe, si no el
    # del nombre de archivo (README: el nombre lleva el acquisition time).
    acq = pd.to_datetime(d["acquisition_utc"], utc=True, errors="coerce")
    fn = d["tif_path"].str.extract(_TS_RE, expand=False)
    fnts = pd.to_datetime(fn, format="%Y%m%d_%H%M%S", utc=True, errors="coerce")
    d["acq_source"] = ["acquisition_utc" if not pd.isna(a) else "filename"
                       for a in acq]
    d["acq"] = acq.fillna(fnts)
    d = d.dropna(subset=["acq"])
    d = d.sort_values("captured_at_utc")
    d = d.drop_duplicates(subset=["volcano", "sensor", "md5"], keep="first")
    d = d.drop_duplicates(subset=["volcano", "sensor", "acq"], keep="first")
    return d.reset_index(drop=True)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def offset_m(lat_ref, lon_ref, lat, lon):
    """Offset local en metros (dnorte, deste) y rumbo en grados desde el norte."""
    dn = (lat - lat_ref) * 111320.0
    de = (lon - lon_ref) * 111320.0 * math.cos(math.radians(lat_ref))
    dist = math.hypot(dn, de)
    brg = (math.degrees(math.atan2(de, dn)) + 360.0) % 360.0
    return dn, de, dist, brg


def quadrant(brg):
    if brg >= 315 or brg < 45:
        return "N"
    if brg < 135:
        return "E"
    if brg < 225:
        return "S"
    return "O"


def _keys_to_str(o):
    if isinstance(o, dict):
        return {("|".join(str(x) for x in k) if isinstance(k, tuple) else str(k)):
                _keys_to_str(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_keys_to_str(v) for v in o]
    return o


def dump(name, obj):
    obj = _keys_to_str(obj)
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, default=str)
    print(f"[escrito] {p}")
    return p


# ─────────────────────────── lectura de GeoTIFF ───────────────────────────
# POR QUÉ: el TIF público de MIROVA trae UNA sola banda (MIR: B21 / M13 / I04),
# en EPSG:4326, sobre su grilla fija. No trae TIR, así que el NTI no se puede
# reconstruir (guard S128). Todo lo que se derive de acá es MIR ABSOLUTO — la
# variable que A69 declara contaminada por el gradiente topográfico.

import numpy as np


def read_tif(path):
    import rasterio
    with rasterio.open(path) as s:
        a = s.read(1).astype(float)
        T = s.transform
        h, w = a.shape
    j, i = np.meshgrid(np.arange(w), np.arange(h))
    lon = T.c + (j + 0.5) * T.a + (i + 0.5) * T.b
    lat = T.f + (j + 0.5) * T.d + (i + 0.5) * T.e
    return a, lat, lon


def local_excess(a, k):
    """L menos su mediana en una ventana k×k: el realce local sobre el terreno."""
    from scipy.ndimage import median_filter
    return a - median_filter(a, size=k, mode="nearest")


def dist_grid_km(lat, lon, lat0, lon0):
    dn = (lat - lat0) * 111.320
    de = (lon - lon0) * 111.320 * np.cos(np.radians(lat0))
    return np.hypot(dn, de)


def load_mirova_rows(t0, t1):
    """Filas crudas de MIROVA (CONS ∪ OCR) en la ventana, con hora y distancia.

    A11: el universo de MIROVA es CONS ∪ OCR. A14: alias completos de nombre.
    Se conservan también FALSO_POSITIVO (etiqueta NUESTRA del scraper = fuera del
    radio, ver reference_mirova_csv_scraper_tags): son detecciones de MIROVA.
    """
    import csv as _csv
    import sys as _sys
    _sys.path.insert(0, os.path.join(REPO, "experiments"))
    from _s126_lib import ALIAS, SENSOR_MAP
    out = []
    for fname in ("latest_consolidado.csv",
                  "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        p = os.path.join(REPO, fname)
        if not os.path.exists(p):
            continue
        for r in _csv.DictReader(open(p, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None:
                continue
            fam = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
            fam = {"v375": "VIIRS375", "v750": "VIIRS750", "modis": "MODIS"}.get(fam)
            if fam is None:
                continue
            ts = pd.to_datetime(r.get("Fecha_Satelite_UTC"), utc=True, errors="coerce")
            if pd.isna(ts) or not (t0 <= ts <= t1):
                continue

            def _f(k):
                try:
                    return float(r.get(k) or "nan")
                except ValueError:
                    return float("nan")
            out.append(dict(volcano=vol, sensor=fam, dt=ts,
                            tipo=(r.get("Tipo_Registro") or "").strip(),
                            vrp=_f("VRP_MW"), dist_km=_f("Distancia_km"),
                            clase=(r.get("Clasificacion Mirova") or "").strip(),
                            fuente="OCR" if "OCR" in (r.get("Tipo_Registro") or "") else "CONS"))
    d = pd.DataFrame(out)
    return d.sort_values("dt").reset_index(drop=True)
