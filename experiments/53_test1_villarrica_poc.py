"""53_test1_villarrica_poc.py — POC Coppola 2015 Eq.1 Test 1 integrated-ROI.

Plan original: tasks/plan_s13_test1_integrated_roi.md (S13, dormido 12 sesiones).

Hipótesis revisada S25 (basada en S24 P2 NEGATIVO):
- Las 6 ALERTAs MIROVA Villarrica (VIIRS 375m, VRP 0.05-0.21 MW) son
  detecciones operacionales del paper Coppola 2015 que MIROVA usa.
- Nuestro pipeline rechaza esos 12 records (SNPP+NOAA20 cada pasada) porque
  ningún path actual (eruption BT-5K, vent BT-1K+vent_radius, NTI K1=-0.8,
  dNTI c1=0.003) captura ΔBT=2.6-6.8K en el pixel summit naive.
- MIROVA SÍ los publica → opera con criterio integrated-ROI (Coppola 2015 §2.2).

Test 1 fórmula:
    L_MIR(i,j) = radiancia desde BT I04 vía Planck inversa.
    L_bg = mediana ROI ring (excluye centro).
    σ_bg = MAD * 1.4826 sobre ROI ring.
    ΔL_ROI = Σ max(0, L_MIR(i,j) − L_bg) sobre ROI completa.
    σ_ΔL = σ_bg · √N_ROI.
    Trigger si: ΔL_ROI > 3·σ_ΔL  AND  ΔL_ROI > 0.02·L_bg·N_ROI.

POC: descarga 12 granules (6 refs × {SNPP, NOAA20}), aplica Test 1, reporta
qué fracción dispara y compara VRP_ROI vs MIROVA NRT.

Criterio aceptación POC: ≥4/6 refs disparan → green light Fase 2 integración.
"""
from __future__ import annotations
import json
import math
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Forzar VRP_PROFILE antes de importar pipeline (evita error si default falla)
import os
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline import fetch
from pipeline.process_viirs import read_viirs_l1b, read_viirs_geo, bt_to_spectral_radiance

# Constants Coppola 2015 Test 1
LAMBDA_I4_UM = 3.74          # VIIRS I-band MIR
ROI_KM = 3.0                 # ROI radius around vent
INNER_KM_RING = 1.0          # exclude center for bg estimation
K_SIGMA = 3.0                # absolute criterion multiplier
MIR_RELATIVE = 0.02          # relative criterion (2% of bg per pixel)
WOOSTER_K_VIIRS_I = 18.0     # VRP_MIR coefficient (VIIRS I-band, S14 calibration)
A_PIX_VIIRS_I = 140625       # m² nadir

# Villarrica config
VENT_LAT = -39.420227        # from volcanoes.yaml
VENT_LON = -71.93            # approx; volcanoes.yaml lon -71.93
TOLERANCE_MIN = 60


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def compute_test1(bt_i4: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                  vent_lat: float, vent_lon: float) -> dict:
    """Coppola 2015 Eq.1 Test 1 integrated-ROI. Returns dict with trigger + VRP."""
    dist = haversine_km(vent_lat, vent_lon, lat, lon)
    roi_mask = (dist <= ROI_KM) & ~np.isnan(bt_i4)
    bg_mask = (dist > INNER_KM_RING) & (dist <= ROI_KM) & ~np.isnan(bt_i4)

    n_roi = int(np.sum(roi_mask))
    n_bg = int(np.sum(bg_mask))
    if n_bg < 20:
        return {"triggered": False, "reason": f"n_bg={n_bg}<20", "n_roi": n_roi}

    # BT → radiancia espectral I4 (W/m²/sr/μm)
    L = bt_to_spectral_radiance(bt_i4, LAMBDA_I4_UM)

    # Background stats (MAD para robustez)
    L_bg_vals = L[bg_mask]
    L_bg = float(np.median(L_bg_vals))
    mad = float(np.median(np.abs(L_bg_vals - L_bg)))
    sigma_bg = 1.4826 * mad

    # Exceso integrado
    roi_vals = L[roi_mask]
    excess = np.maximum(0.0, roi_vals - L_bg)
    delta_L = float(np.sum(excess))
    n_contributing = int(np.sum(excess > 0))

    # σ integrado (propagación √N)
    sigma_delta_L = sigma_bg * math.sqrt(n_roi)

    # Criterios dual
    abs_crit = delta_L > K_SIGMA * sigma_delta_L
    rel_crit = delta_L > MIR_RELATIVE * L_bg * n_roi
    triggered = abs_crit and rel_crit

    # VRP Wooster sobre pixels contributivos
    # delta_L tiene unidades W/m²/sr/μm. Para VRP necesitamos sumar A_pix·ΔL.
    # Aproximamos area=A_PIX_VIIRS_I para todos los pixels de la ROI.
    vrp_w = WOOSTER_K_VIIRS_I * A_PIX_VIIRS_I * delta_L
    vrp_mw = vrp_w * 1e-6

    # Pixel más caliente (para reporte)
    bt_roi = bt_i4[roi_mask]
    t_max = float(np.nanmax(bt_roi)) if bt_roi.size else 0.0
    bt_bg = bt_i4[bg_mask]
    t_bg = float(np.nanmedian(bt_bg)) if bt_bg.size else 0.0

    return {
        "triggered": triggered,
        "abs_criterion": abs_crit,
        "rel_criterion": rel_crit,
        "n_roi": n_roi,
        "n_bg": n_bg,
        "n_contributing": n_contributing,
        "L_bg": L_bg,
        "sigma_bg": sigma_bg,
        "delta_L_integrated": delta_L,
        "sigma_delta_L_integrated": sigma_delta_L,
        "k_sigma_observed": delta_L / sigma_delta_L if sigma_delta_L > 0 else 0,
        "rel_observed": delta_L / (L_bg * n_roi) if L_bg > 0 else 0,
        "vrp_test1_mw": vrp_mw,
        "t_max_k": t_max,
        "t_bg_k": t_bg,
        "delta_bt": t_max - t_bg,
    }


def fetch_granules_for_ref(ref_dt: datetime, dest_dir: Path) -> list:
    """Search & download VIIRS 375m granules around ref_dt for Villarrica."""
    fetch.auth()
    radius_deg = 25 / 111.0
    # Keys de PRODUCTS dict en pipeline.fetch (no short_names directos)
    products_375 = [
        ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
        ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
        ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
    ]
    granule_pairs = []
    date = ref_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    for l1b_key, geo_key in products_375:
        try:
            l1b_list = fetch.search_granules(l1b_key, VENT_LAT, VENT_LON, radius_deg, date)
        except Exception as e:
            print(f"  search {l1b_key} fail: {e}")
            continue
        if not l1b_list:
            continue
        try:
            geo_list = fetch.search_granules(geo_key, VENT_LAT, VENT_LON, radius_deg, date)
        except Exception:
            geo_list = []
        # Match by datetime
        for g in l1b_list:
            try:
                g_time_str = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
                g_dt = datetime.fromisoformat(g_time_str.replace("Z", "+00:00"))
            except Exception:
                continue
            if abs((g_dt - ref_dt).total_seconds()) > TOLERANCE_MIN * 60:
                continue
            # Find matching GEO
            geo_match = None
            for gh in geo_list:
                try:
                    gh_str = gh["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
                    gh_dt = datetime.fromisoformat(gh_str.replace("Z", "+00:00"))
                except Exception:
                    continue
                if abs((gh_dt - g_dt).total_seconds()) < 30:
                    geo_match = gh
                    break
            if geo_match is not None:
                granule_pairs.append((g, geo_match, l1b_key))
    if not granule_pairs:
        return []
    # Download
    paths = []
    for l1b_g, geo_g, key in granule_pairs:
        try:
            l1b_paths = fetch.download_granules([l1b_g], dest_dir)
            geo_paths = fetch.download_granules([geo_g], dest_dir)
            if l1b_paths and geo_paths:
                paths.append((l1b_paths[0], geo_paths[0], key))
        except Exception as e:
            print(f"  download fail {key}: {e}")
    return paths


def main():
    import pandas as pd
    csv = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
    df = pd.read_csv(csv)
    refs = df[(df.Volcan == "Villarrica") & (df.Tipo_Registro == "ALERTA_TERMICA")].copy()

    def parse_dt(s):
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    refs["dt"] = refs.Fecha_Satelite_UTC.apply(parse_dt)

    print(f"# POC Test 1 integrated-ROI sobre {len(refs)} refs MIROVA Villarrica")
    print()

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for _, ref in refs.iterrows():
            print(f"=== Ref {ref['dt']} VRP MIROVA={ref['VRP_MW']:.3f} ===")
            granules = fetch_granules_for_ref(ref["dt"], tmp_path)
            print(f"  granules descargados: {len(granules)}")
            for l1b_path, geo_path, key in granules:
                try:
                    bt = read_viirs_l1b(Path(l1b_path))
                    geo = read_viirs_geo(Path(geo_path))
                    if "I04" not in bt:
                        print(f"  {Path(l1b_path).name}: sin I04, skip")
                        continue
                    res = compute_test1(bt["I04"], geo["lat"], geo["lon"],
                                        VENT_LAT, VENT_LON)
                    res["ref_dt"] = str(ref["dt"])
                    res["ref_vrp_mw"] = float(ref["VRP_MW"])
                    res["product_key"] = key
                    res["granule"] = Path(l1b_path).name
                    results.append(res)
                    fired = "✓ DISPARA" if res["triggered"] else "✗ no dispara"
                    print(f"  {Path(l1b_path).name}: {fired}  "
                          f"VRP_test1={res['vrp_test1_mw']:.3f}  "
                          f"ΔBT={res['delta_bt']:.1f}K  "
                          f"K={res['k_sigma_observed']:.1f}  "
                          f"rel={res['rel_observed']*100:.2f}%  "
                          f"n_contrib={res['n_contributing']}/{res['n_roi']}")
                except Exception as e:
                    print(f"  {Path(l1b_path).name}: ERROR {e}")
            print()

    # Summary
    out = ROOT / "experiments" / "53_test1_villarrica_results.json"
    out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"# Detalle escrito en {out}")
    print()
    by_ref = {}
    for r in results:
        by_ref.setdefault(r["ref_dt"], []).append(r)
    n_refs_fired = sum(1 for refs_results in by_ref.values()
                       if any(rr["triggered"] for rr in refs_results))
    print(f"# Refs MIROVA con ≥1 granule disparando Test 1: {n_refs_fired}/{len(by_ref)}")
    if n_refs_fired:
        # VRP ratio Test1/MIROVA en granules disparados
        ratios = []
        for r in results:
            if r["triggered"] and r["ref_vrp_mw"] > 0:
                ratios.append(r["vrp_test1_mw"] / r["ref_vrp_mw"])
        if ratios:
            ratios.sort()
            print(f"# Ratio VRP_Test1 / VRP_MIROVA (n={len(ratios)}): "
                  f"min={ratios[0]:.2f} median={ratios[len(ratios)//2]:.2f} max={ratios[-1]:.2f}")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
