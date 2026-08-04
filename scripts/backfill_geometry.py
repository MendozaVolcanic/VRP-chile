#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════════════
# FICHA SDA · backfill_geometry.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Rellenar la geometría de observación (zenith/azimut de satélite y sol) en
#                 records YA existentes, sin reprocesarlos.
# Lógica        : Descarga SOLO el archivo de geolocalización de cada granule (no la radiancia) y
#                 muestrea los 4 ángulos en el punto que el record ya reporta.
# Modelo/método : Sin modelo. Lectura directa del producto de geolocalización NASA (MOD03/MYD03,
#                 VNP03/VJ103/VJ203). Determinista.
# Datos entrada : JSON de records + productos de geolocalización L1B. SIN datos personales.
# Variables     : Solo ESCRIBE sensor_zenith_deg, sensor_azimuth_deg, solar_zenith_deg,
#                 solar_azimuth_deg. NUNCA toca VRP, detección, clasificación ni ningún otro campo.
# Limitaciones  : Requiere que el record tenga un punto donde muestrear (final_hotspot o el cráter).
#                 MODIS necesita pyhdf → solo corre en Linux (GitHub Actions).
# Refs/datos    : docs/AUDIT_S122.md; misma procedencia L1B que los records nuevos. Entrenamiento: No aplica.
#                 Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""Rellena la geometría de observación en records históricos (S122).

POR QUÉ existe: el pipeline recién persiste los ángulos desde S122, así que los
records anteriores no los tienen. Reprocesarlos completo re-descargaría las
bandas de radiancia Y recalcularía el VRP con el código de hoy — los valores
históricos cambiarían y dejaría de ser aditivo. Este script baja SOLO la
geolocalización (mucho más liviana) y agrega los 4 ángulos sin tocar nada más.

Uso:
    python scripts/backfill_geometry.py --volcano Villarrica \\
        --start 2026-06-01 --end 2026-07-31 [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline import fetch  # noqa: E402
from pipeline.scan_geometry import (  # noqa: E402
    OBSERVATION_ANGLE_KEYS, attr_scale_factor, observation_geometry,
)

# Sensor del record → clave del producto de geolocalización en fetch.PRODUCTS.
GEO_KEY = {
    "MODIS_TERRA": "MODIS_TERRA_GEO",
    "MODIS_AQUA": "MODIS_AQUA_GEO",
    "VIIRS_SNPP": "VIIRS_SNPP_GEO",
    "VIIRS_NOAA20": "VIIRS_NOAA20_GEO",
    "VIIRS_NOAA21": "VIIRS_NOAA21_GEO",
    "VIIRS_SNPP_750": "VIIRS_SNPP_MOD_GEO",
    "VIIRS_NOAA20_750": "VIIRS_NOAA20_MOD_GEO",
    "VIIRS_NOAA21_750": "VIIRS_NOAA21_MOD_GEO",
}

# Token de adquisición compartido entre el L1B y su geolocalización: A<YYYYDDD>.<HHMM>
ACQ_RE = re.compile(r"A(\d{7})\.(\d{4})")


def acq_token(filename: str) -> str | None:
    m = ACQ_RE.search(filename or "")
    return f"{m.group(1)}.{m.group(2)}" if m else None


def read_geo_angles(path: Path) -> dict | None:
    """Lee lat/lon + los 4 ángulos de un archivo de geolocalización.

    Soporta VIIRS (HDF5/NetCDF4, grupo geolocation_data) y MODIS (HDF4, SDS a
    1 km). Devuelve None si no se pudo leer (nunca lanza).
    """
    name = path.name
    try:
        if name.startswith(("VNP03", "VJ103", "VJ203")):
            import h5py
            with h5py.File(path, "r") as f:
                g = f["geolocation_data"]
                lat = g["latitude"][:].astype(np.float32)
                lon = g["longitude"][:].astype(np.float32)
                lat[lat < -90] = np.nan
                lon[lon < -180] = np.nan

                def rd(*cands):
                    for c in cands:
                        if c in g:
                            a = g[c][:].astype(np.float32) * attr_scale_factor(g[c].attrs)
                            a[np.isnan(lat)] = np.nan
                            return a
                    return None

                angles = {
                    "sensor_zenith_deg": rd("sensor_zenith", "satellite_zenith"),
                    "sensor_azimuth_deg": rd("sensor_azimuth", "satellite_azimuth"),
                    "solar_zenith_deg": rd("solar_zenith"),
                    "solar_azimuth_deg": rd("solar_azimuth"),
                }
            return {"lat": lat, "lon": lon, "angles": angles}

        # MODIS MOD03/MYD03 (HDF4) — ya viene a 1 km, sin interpolar.
        from pyhdf.SD import SD, SDC
        sd = SD(str(path), SDC.READ)
        try:
            lat = sd.select("Latitude").get().astype(np.float32)
            lon = sd.select("Longitude").get().astype(np.float32)
            angles = {}
            for key, sds_name in (("sensor_zenith_deg", "SensorZenith"),
                                  ("sensor_azimuth_deg", "SensorAzimuth"),
                                  ("solar_zenith_deg", "SolarZenith"),
                                  ("solar_azimuth_deg", "SolarAzimuth")):
                try:
                    sds = sd.select(sds_name)
                    angles[key] = sds.get().astype(np.float32) * attr_scale_factor(
                        sds.attributes())
                    sds.endaccess()
                except Exception:
                    angles[key] = None
        finally:
            sd.end()
        return {"lat": lat, "lon": lon, "angles": angles}
    except Exception as exc:
        print(f"    WARN: no se pudo leer {name}: {type(exc).__name__}: {exc}")
        return None


def sample_point(rec: dict, vent_lat: float, vent_lon: float):
    """Punto donde muestrear: el hotspot reportado; si no hay, el cráter."""
    lat = rec.get("final_hotspot_lat")
    lon = rec.get("final_hotspot_lon")
    if lat is None or lon is None:
        return vent_lat, vent_lon
    return lat, lon


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--data-subdir", default="mirova_equivalent")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
    vols = cfg.get("volcanoes", cfg)
    vols = list(vols.values()) if isinstance(vols, dict) else vols
    vc = next((v for v in vols if v.get("name") == args.volcano), None)
    if vc is None:
        print(f"ERROR: volcán '{args.volcano}' no está en volcanoes.yaml")
        return 2
    vlat = vc.get("vent_lat") or vc["lat"]
    vlon = vc.get("vent_lon") or vc["lon"]
    radius = float(vc.get("radius_km", 25))

    jpath = REPO / "data" / args.data_subdir / f"{args.volcano}.json"
    store = json.load(open(jpath, encoding="utf-8"))
    recs = store["records"] if isinstance(store, dict) and "records" in store else store

    # Records de la ventana que faltan geometría y tienen granule reconocible.
    pend = {}
    for r in recs:
        dt = r.get("datetime_utc", "")
        if not (args.start <= dt[:10] <= args.end):
            continue
        if r.get("sensor_zenith_deg") is not None:
            continue
        key = GEO_KEY.get(r.get("sensor", ""))
        tok = acq_token(r.get("granule", ""))
        if not key or not tok:
            continue
        pend.setdefault((dt[:10], key), []).append((tok, r))

    n_pend = sum(len(v) for v in pend.values())
    print(f"{args.volcano}: {n_pend} records sin geometría en {args.start}..{args.end} "
          f"({len(pend)} combinaciones fecha×producto)")
    if args.dry_run or not n_pend:
        return 0

    tmp = REPO / "data" / "_geo_tmp" / args.volcano
    tmp.mkdir(parents=True, exist_ok=True)
    filled = 0
    for (day, geo_key), items in sorted(pend.items()):
        date = datetime.strptime(day, "%Y-%m-%d")
        try:
            grans = fetch.search_granules(geo_key, vlat, vlon, radius, date)
        except Exception as exc:
            print(f"  {day} {geo_key}: search falló ({type(exc).__name__}) — se salta")
            continue
        if not grans:
            continue
        # Solo los granules cuyo token coincide con algún record pendiente.
        want = {t for t, _ in items}
        sel = [g for g in grans
               if acq_token(str(g).split("/")[-1]) in want
               or any(w in str(g) for w in want)]
        if not sel:
            continue
        try:
            paths = fetch.download_granules(sel, tmp)
        except Exception as exc:
            print(f"  {day} {geo_key}: download falló ({type(exc).__name__}: {exc}) — se salta")
            continue
        if not paths:
            print(f"    DIAG {day} {geo_key}: download devolvió 0 archivos "
                  f"para {len(sel)} granules seleccionados")
            continue

        by_tok = {}
        for p in paths:
            t = acq_token(p.name)
            if t:
                by_tok[t] = p
        if not by_tok:
            # Fallar en silencio acá fue el bug de la 1a corrida (0 rellenados
            # con exit 0). Ruidoso a propósito.
            print(f"    DIAG {day} {geo_key}: {len(sel)} seleccionados → "
                  f"{len(paths)} descargados, 0 con token reconocible. "
                  f"names={[p.name for p in paths][:3]} want={sorted(want)[:3]}")
        for tok, rec in items:
            p = by_tok.get(tok)
            if p is None:
                if by_tok:
                    print(f"    DIAG {day} {geo_key}: token {tok} sin archivo "
                          f"(descargados: {sorted(by_tok)[:3]})")
                continue
            geo = read_geo_angles(p)
            if geo is None:
                continue
            lat_s, lon_s = sample_point(rec, vlat, vlon)
            ang = observation_geometry(geo["lat"], geo["lon"], geo["angles"], lat_s, lon_s)
            if all(v is None for v in ang.values()):
                continue
            for k in OBSERVATION_ANGLE_KEYS:
                rec[k] = ang[k]
            filled += 1
        # Borrar los archivos apenas se usan: son grandes y no se versionan.
        for p in paths:
            try:
                p.unlink()
            except Exception:
                pass
        print(f"  {day} {geo_key}: {len(sel)} granules → {filled} records con geometría (acum.)")

    if filled:
        json.dump(store, open(jpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{args.volcano}: {filled}/{n_pend} records rellenados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
