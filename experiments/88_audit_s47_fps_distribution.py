"""S47-A2: distribución FPs sobre mirova_equivalent baseline (drift234 adoptado).

Clasifica cada FP en:
  (a) FALSO_POSITIVO MIROVA legitimo: MIROVA marca explicitamente FP en ese
      timestamp -> drift residual real de nuestro algoritmo.
  (b) ALERTA_TERMICA gap-de-scraper: nuestro VRP>0 SIN entrada CSV del MIROVA
      en +-30min pero MIROVA podria haberla reportado (no auditable sin
      mirova-tif-archive cross-check; aqui simplemente "huerfano").
  (c) Huerfano puro: MIROVA reporta RUTINA en ese timestamp (no detecto) y
      nosotros si -> drift propio + posible gap.

NOTA: distinguir (b) vs (c) requiere chequear si MIROVA tiene RUTINA en ese
satelite/timestamp. RUTINA en CSV = scraper VIO el sat pero NO detecto.
  - Si hay RUTINA +-30min mismo sat -> categoria (c) [drift nuestro real]
  - Si NO hay nada del MIROVA en +-30min -> categoria (b) [gap scraper o
    granule no procesado por MIROVA]

Reutiliza lógica de 87_audit_s46_round1.py (sensor_match, vrp_mirovaEq,
inner_radius fallback).

Window: 30d hasta el latest del CSV (CSV termina 2026-05-01, no 05-16).
"""
from __future__ import annotations
import json
import sys
import io
from pathlib import Path
from datetime import timedelta

import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

VOLC_CSV_MAP = {
    "Lascar": "Lascar",
    "Tupungatito": "Tupungatito",
    "Lastarria": "Lastarria",
    "NevadosDeChillan": "Nevados de Chillan",
    "Llaima": "Llaima",
    "Copahue": "Copahue",
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Isluga": "Isluga",
    "Villarrica": "Villarrica",
    "Chaiten": "Chaiten",
}
SENSORS = ["MODIS", "VIIRS", "VIIRS375"]
INNER_RADIUS_FALLBACK = {
    'Lascar': 5, 'Lastarria': 3, 'Tupungatito': 7, 'Villarrica': 5,
    'PuyehueCordonCaulle': 20, 'Copahue': 4, 'NevadosDeChillan': 5,
    'Llaima': 5, 'Chaiten': 5, 'PlanchonPeteroa': 3, 'Isluga': 5,
}


def sensor_match(record_sensor, target):
    if not record_sensor:
        return False
    rs = record_sensor.upper()
    if target == "MODIS":
        return rs.startswith("MODIS")
    if target == "VIIRS":
        return rs.startswith("VIIRS_") and rs.endswith("_750")
    if target == "VIIRS375":
        return rs.startswith("VIIRS_") and not rs.endswith("_750")
    return False


def vrp_mirovaEq(rec, inner):
    if not isinstance(rec, dict):
        return 0.0
    pc = rec.get("primary_cluster")
    if pc is None:
        try:
            return float(rec.get("vrp_mw", 0) or 0)
        except (TypeError, ValueError):
            return 0.0
    cdist = pc.get("centroid_dist_km")
    if cdist is None or cdist > inner:
        return 0.0
    try:
        v = float(pc.get("vrp_mw", 0) or 0)
    except (TypeError, ValueError):
        return 0.0
    if v > 50000:
        return 0.0
    return v


def parse_dt(s):
    if not s:
        return None
    try:
        ts = pd.Timestamp(s)
        return ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")
    except Exception:
        return None


def main():
    repo = Path(__file__).parent.parent
    # S47 update 2026-05-16: usar snapshot fresh (window 30d real)
    csv_path = repo / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
    if not csv_path.exists():
        # Fallback al snapshot histórico embebido
        csv_path = repo / "01_05_2026_registro_vrp_consolidado.csv"
    df = pd.read_csv(csv_path)
    df["ts"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce", utc=True)
    df = df.dropna(subset=["ts"])

    # Window del handoff S47: 2026-04-16 -> 2026-05-16, recortado por CSV (latest 05-01)
    window_start = pd.Timestamp("2026-04-16", tz="UTC")
    window_end = min(df["ts"].max() + pd.Timedelta(days=1),
                     pd.Timestamp("2026-05-17", tz="UTC"))
    print(f"CSV latest: {df['ts'].max()}")
    print(f"Window: {window_start.date()} -> {window_end.date()} (30d)")
    print(f"Profile: mirova_equivalent (drift234 adopted S46)\n")

    tol = timedelta(minutes=30)
    fp_records = []
    per_vol = {}

    for vol_key, vol_csv in VOLC_CSV_MAP.items():
        jpath = repo / "data" / "mirova_equivalent" / f"{vol_key}.json"
        if not jpath.exists():
            continue
        data = json.loads(jpath.read_text(encoding="utf-8"))
        recs = data.get("records", [])
        inner = INNER_RADIUS_FALLBACK.get(vol_key, 5)

        mvol = df[df["Volcan"] == vol_csv].copy()
        mvol = mvol[(mvol["ts"] >= window_start) & (mvol["ts"] < window_end)]

        per_vol[vol_key] = {"TP": 0, "FN": 0, "FP_a": 0, "FP_b": 0, "FP_c": 0,
                            "by_sensor": {s: {"TP": 0, "FP_a": 0, "FP_b": 0,
                                              "FP_c": 0} for s in SENSORS}}

        # iterar nuestros records con VRP>0 en window
        for r in recs:
            t_o = parse_dt(r.get("datetime_utc") or r.get("timestamp_utc"))
            if t_o is None or not (window_start <= t_o < window_end):
                continue
            if vrp_mirovaEq(r, inner) <= 0:
                continue
            sens_r = r.get("sensor", "")
            sens_label = None
            for s in SENSORS:
                if sensor_match(sens_r, s):
                    sens_label = s
                    break
            if sens_label is None:
                continue

            # buscar contraparte MIROVA mismo sensor +-30min
            sens_csv = mvol[mvol["Sensor"] == sens_label]
            candidates = sens_csv[abs(sens_csv["ts"] - t_o) <= tol]

            if (candidates["Tipo_Registro"] == "ALERTA_TERMICA").any():
                per_vol[vol_key]["TP"] += 1
                per_vol[vol_key]["by_sensor"][sens_label]["TP"] += 1
                continue

            # No es TP -> es FP de algun tipo
            pc = r.get("primary_cluster") or {}
            fp_info = {
                "vol": vol_key,
                "ts": t_o.isoformat(),
                "sensor": sens_label,
                "sensor_raw": sens_r,
                "vrp_mw": pc.get("vrp_mw"),
                "centroid_dist_km": pc.get("centroid_dist_km"),
                "lat": pc.get("centroid_lat"),
                "lon": pc.get("centroid_lon"),
                "n_pixels": pc.get("n_pixels"),
            }

            # S48 fix: el matching temporal+sensor crudo confunde clusters
            # distintos del mismo granule. Lascar caso paradigmático: MIROVA
            # reporta FP de cluster a 16-29 km del vent, nuestro pc está a
            # <1.6 km del vent (summit cráter real). Eran eventos distintos.
            # Fix: para clasificar FP_a/FP_c, exigir además que la distancia
            # nuestra y la de MIROVA al vent estén dentro de 5 km
            # (= mismo cluster espacial del granule).
            our_dist = pc.get("centroid_dist_km")
            SPATIAL_TOL_KM = 5.0

            def _same_cluster(mirova_dist_km):
                if our_dist is None or mirova_dist_km is None:
                    return True  # ante duda, comportamiento legacy (no agrava)
                try:
                    return abs(float(mirova_dist_km) - float(our_dist)) <= SPATIAL_TOL_KM
                except (TypeError, ValueError):
                    return True

            # Spatial-aware FP classification
            fp_match = candidates[candidates["Tipo_Registro"] == "FALSO_POSITIVO"]
            rt_match = candidates[candidates["Tipo_Registro"] == "RUTINA"]

            same_cluster_fp = any(_same_cluster(d) for d in fp_match["Distancia_km"]) if len(fp_match) > 0 else False
            same_cluster_rt = any(_same_cluster(d) for d in rt_match["Distancia_km"]) if len(rt_match) > 0 else False

            if same_cluster_fp:
                fp_info["category"] = "a_mirova_fp"
                per_vol[vol_key]["FP_a"] += 1
                per_vol[vol_key]["by_sensor"][sens_label]["FP_a"] += 1
            elif same_cluster_rt:
                fp_info["category"] = "c_mirova_rutina"
                per_vol[vol_key]["FP_c"] += 1
                per_vol[vol_key]["by_sensor"][sens_label]["FP_c"] += 1
            elif len(fp_match) > 0 or len(rt_match) > 0:
                # MIROVA tuvo entry temporal pero cluster distinto del nuestro
                # → ambos vieron el granule pero detectaron en zonas distintas.
                # Lo más honesto: huérfano de nuestra detección (no contó
                # MIROVA como FP del SAME cluster).
                fp_info["category"] = "b_no_mirova_entry"
                fp_info["mirova_diff_cluster"] = True
                per_vol[vol_key]["FP_b"] += 1
                per_vol[vol_key]["by_sensor"][sens_label]["FP_b"] += 1
            else:
                fp_info["category"] = "b_no_mirova_entry"
                per_vol[vol_key]["FP_b"] += 1
                per_vol[vol_key]["by_sensor"][sens_label]["FP_b"] += 1

            fp_records.append(fp_info)

        # FN: ALERTAS MIROVA sin match
        for _, m in mvol[mvol["Tipo_Registro"] == "ALERTA_TERMICA"].iterrows():
            sens_label = m["Sensor"]
            if sens_label not in SENSORS:
                continue
            t_m = m["ts"]
            matched = False
            for r in recs:
                t_o = parse_dt(r.get("datetime_utc") or r.get("timestamp_utc"))
                if t_o is None or abs(t_o - t_m) > tol:
                    continue
                if not sensor_match(r.get("sensor", ""), sens_label):
                    continue
                if vrp_mirovaEq(r, inner) > 0:
                    matched = True
                    break
            if not matched:
                per_vol[vol_key]["FN"] += 1

    # Reporte
    print("=" * 70)
    print("PER-VOLCAN (mirova_equivalent, drift234)")
    print("=" * 70)
    print(f"{'Vol':<22} {'TP':>4} {'FN':>4} {'FP_a':>5} {'FP_b':>5} {'FP_c':>5} {'FP_tot':>7}")
    tot = {"TP": 0, "FN": 0, "FP_a": 0, "FP_b": 0, "FP_c": 0}
    for v, m in sorted(per_vol.items()):
        fp_tot = m["FP_a"] + m["FP_b"] + m["FP_c"]
        print(f"{v:<22} {m['TP']:>4} {m['FN']:>4} {m['FP_a']:>5} "
              f"{m['FP_b']:>5} {m['FP_c']:>5} {fp_tot:>7}")
        for k in tot:
            tot[k] += m[k]
    fp_tot = tot["FP_a"] + tot["FP_b"] + tot["FP_c"]
    print(f"{'TOTAL':<22} {tot['TP']:>4} {tot['FN']:>4} {tot['FP_a']:>5} "
          f"{tot['FP_b']:>5} {tot['FP_c']:>5} {fp_tot:>7}")

    print("\n" + "=" * 70)
    print("PER-SENSOR aggregate")
    print("=" * 70)
    print(f"{'Sensor':<10} {'TP':>4} {'FP_a':>5} {'FP_b':>5} {'FP_c':>5}")
    for s in SENSORS:
        st = {"TP": 0, "FP_a": 0, "FP_b": 0, "FP_c": 0}
        for v in per_vol.values():
            for k in st:
                st[k] += v["by_sensor"][s][k]
        print(f"{s:<10} {st['TP']:>4} {st['FP_a']:>5} {st['FP_b']:>5} {st['FP_c']:>5}")

    print("\n" + "=" * 70)
    print("EJEMPLOS FP categoria (a) — drift real vs MIROVA")
    print("=" * 70)
    cat_a = [f for f in fp_records if f["category"] == "a_mirova_fp"]
    for ex in cat_a[:5]:
        print(f"  {ex['vol']:<20} {ex['ts']}  {ex['sensor']:<8} "
              f"vrp={ex['vrp_mw']}  d={ex['centroid_dist_km']}km  "
              f"npx={ex['n_pixels']}  ({ex['lat']:.4f},{ex['lon']:.4f})")
    if not cat_a:
        print("  (ninguno)")

    out = repo / "experiments" / "88_fps_distribution.json"
    out.write_text(json.dumps(
        {"window_start": str(window_start), "window_end": str(window_end),
         "per_vol": per_vol, "totals": tot,
         "fp_records": fp_records}, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON: {out}")


if __name__ == "__main__":
    main()
