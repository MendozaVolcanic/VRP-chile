#!/usr/bin/env python3
"""S90/S91 — Análisis A/B detección diurna MODIS (enabled vs disabled).

Gate de adopción (design doc 2026-05-30 §7). NO setea nada en operacional;
solo mide. Foco: las detecciones que SOLO aparecen con el path diurno ON.

Qué computa, por volcán:
  1. Recall vs MIROVA (ALERTA_TERMICA) por (vol, noche), enabled vs disabled.
  2. Precisión: de nuestras detecciones, cuántas matchean una ALERTA MIROVA.
  3. Nuevas detecciones diurnas = records en enabled ausentes en disabled
     (key por datetime_utc al minuto). Para cada una: elevación solar (mismo
     `_solar_elevation` del pipeline), VRP, mirova_eq_vrp, distancia, y si
     matchea una ALERTA MIROVA real esa noche (R3: TP diurno vs FP solar).

Uso:
  python experiments/_s90_daytime_modis/analyze_ab.py \
      --volcano NevadosDeChillan --start 2026-03-01 --end 2026-04-30
  python experiments/_s90_daytime_modis/analyze_ab.py \
      --volcano Villarrica --start 2026-05-01 --end 2026-05-30

El CSV ground truth por defecto es latest_consolidado.csv (más reciente).
"""
import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Constraint Windows: stdout cp1252 rompe con Δ/°/símbolos (CLAUDE.md).
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipeline.audit_metrics import mirova_eq_vrp  # noqa: E402
from pipeline.store import _solar_elevation       # noqa: E402

# JSON stem -> nombre MIROVA en el CSV (A14: variantes de nombre)
NAME_MAP = {
    "NevadosDeChillan": "Nevados de Chillan",
    "Planchon-Peteroa": "Planchon-Peteroa",
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
    "Villarrica": "Villarrica",
    "Lascar": "Lascar",
    "Lastarria": "Lastarria",
    "Tupungatito": "Tupungatito",
    "Llaima": "Llaima",
    "Isluga": "Isluga",
    "Copahue": "Copahue",
    "Chaiten": "Chaiten",
}

# inner_radius_km oficial MIROVA (para mirova_eq_vrp)
INNER_KM = {
    "NevadosDeChillan": 5, "Villarrica": 5, "Lascar": 5, "Isluga": 5,
    "Llaima": 5, "Chaiten": 5, "Lastarria": 3, "Planchon-Peteroa": 3,
    "Copahue": 4, "Tupungatito": 7, "PuyehueCordonCaulle": 20,
}


def parse_dt(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


def load_alertas(csv_path, vol_csv_name, start, end):
    """ALERTA_TERMICA MIROVA del volcán en ventana. key=(noche). Incluye sensor."""
    alertas = defaultdict(list)
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Tipo_Registro") != "ALERTA_TERMICA":
                continue
            if row.get("Volcan", "").strip() != vol_csv_name:
                continue
            dt = parse_dt(row.get("Fecha_Satelite_UTC", "").strip())
            if dt is None or not (start <= dt <= end):
                continue
            alertas[dt.date()].append({
                "vrp": float(row["VRP_MW"]) if row.get("VRP_MW") else 0.0,
                "dist": float(row["Distancia_km"]) if row.get("Distancia_km") else None,
                "dt": dt,
                "sensor": row.get("Sensor", "").strip(),
            })
    return alertas


def load_recs(json_path, start, end):
    """Records de un dataset en ventana. Devuelve lista de (dt, record)."""
    if not json_path.exists():
        return []
    data = json.load(open(json_path, encoding="utf-8"))
    records = data.get("records", data) if isinstance(data, dict) else data
    out = []
    for r in records:
        dt = parse_dt(r.get("datetime_utc", ""))
        if dt is None or not (start <= dt <= end):
            continue
        out.append((dt, r))
    return out


def rec_solar_elev(r):
    """Elevación solar de un record (mismo algoritmo del pipeline)."""
    dt = parse_dt(r.get("datetime_utc", ""))
    lat = r.get("final_hotspot_lat") or r.get("hotspot_lat")
    lon = r.get("final_hotspot_lon") or r.get("hotspot_lon")
    if dt is None or lat is None or lon is None:
        return None
    return _solar_elevation(lat, lon, dt)


def recall_precision(recs, alertas, vol_stem):
    """Recall y precisión por noche vs MIROVA. recs: lista (dt, record)."""
    inner = INNER_KM.get(vol_stem)
    by_night = defaultdict(list)
    for dt, r in recs:
        by_night[dt.date()].append(r)

    our_nights = set(by_night)
    mir_nights = set(alertas)
    tp = len(our_nights & mir_nights)
    fn = len(mir_nights - our_nights)
    # FP a nivel noche: noche con detección nuestra (mirova_eq_vrp>0) sin alerta MIROVA
    fp = 0
    for night, rs in by_night.items():
        meq = max((mirova_eq_vrp(r, vol_stem, inner) for r in rs), default=0)
        if meq > 0 and night not in mir_nights:
            fp += 1
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    return {"tp": tp, "fn": fn, "fp": fp, "recall": recall, "precision": precision}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True, help="stem JSON, ej. NevadosDeChillan")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--csv", default=str(ROOT / "latest_consolidado.csv"))
    args = ap.parse_args()

    vol = args.volcano
    vol_csv = NAME_MAP.get(vol, vol)
    inner = INNER_KM.get(vol)
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end).replace(hour=23, minute=59, second=59)

    en_path = ROOT / "data" / "_daytime_modis_enabled" / f"{vol}.json"
    di_path = ROOT / "data" / "_daytime_modis_disabled" / f"{vol}.json"
    en = load_recs(en_path, start, end)
    di = load_recs(di_path, start, end)
    alertas = load_alertas(Path(args.csv), vol_csv, start, end)

    print(f"\n{'='*64}\n  A/B DIURNO MODIS — {vol} ({vol_csv})  {args.start}->{args.end}")
    print(f"  CSV: {Path(args.csv).name}  |  inner_radius_km={inner}")
    print(f"  records enabled={len(en)}  disabled={len(di)}  |  noches ALERTA MIROVA={len(alertas)}")
    print('='*64)

    # --- Métricas globales A/B ---
    m_en = recall_precision(en, alertas, vol)
    m_di = recall_precision(di, alertas, vol)
    print("\n[1] Métricas vs MIROVA (por noche). OJO: la precisión ABSOLUTA es baja")
    print("    por A54 (≈95% de los 'FP' son realidad física, no ruido solar). El")
    print("    criterio de adopción mira el Δ enabled−disabled y la sección [3], no")
    print("    el valor absoluto.")
    print(f"  {'':10} {'recall':>8} {'prec':>8} {'TP':>4} {'FN':>4} {'FP':>4}")
    for lbl, m in [("disabled", m_di), ("enabled", m_en)]:
        print(f"  {lbl:10} {m['recall']:>7.1%} {m['precision']:>7.1%} "
              f"{m['tp']:>4} {m['fn']:>4} {m['fp']:>4}")
    d_rec = m_en["recall"] - m_di["recall"]
    d_prec = m_en["precision"] - m_di["precision"]
    print(f"  Δ recall = {d_rec:+.1%}   Δ precisión = {d_prec:+.1%}")

    # --- Nuevas detecciones diurnas (enabled \ disabled) ---
    di_keys = {dt.strftime("%Y-%m-%dT%H:%M") for dt, _ in di
               if (mirova_eq_vrp(_, vol, inner) > 0)}
    en_pos = [(dt, r) for dt, r in en if mirova_eq_vrp(r, vol, inner) > 0]
    nuevas = [(dt, r) for dt, r in en_pos
              if dt.strftime("%Y-%m-%dT%H:%M") not in di_keys]

    print(f"\n[2] Nuevas detecciones con flag ON (mirova_eq_vrp>0, ausentes en disabled): {len(nuevas)}")
    print(f"  {'datetime_utc':17} {'sol°':>6} {'D/N':>3} {'sensor':>14} "
          f"{'meq_MW':>8} {'dist':>6} {'class':>9} {'MIROVA?':>8}")
    n_diurnas = n_diurnas_tp = n_diurnas_fp = 0
    for dt, r in sorted(nuevas, key=lambda x: x[0]):
        elev = rec_solar_elev(r)
        dn = "DÍA" if (elev is not None and elev > 0) else "noc"
        meq = mirova_eq_vrp(r, vol, inner)
        dist = r.get("final_hotspot_dist_km")
        mir = alertas.get(dt.date(), [])
        mir_modis = [a for a in mir if a["sensor"].upper().startswith("MODIS")]
        match = "TP" if mir_modis else ("TP*" if mir else "FP?")
        if dn == "DÍA":
            n_diurnas += 1
            if mir:
                n_diurnas_tp += 1
            else:
                n_diurnas_fp += 1
        print(f"  {dt.strftime('%Y-%m-%dT%H:%M'):17} "
              f"{(elev if elev is not None else float('nan')):>6.1f} {dn:>3} "
              f"{r.get('sensor','?'):>14} {meq:>8.2f} "
              f"{(dist if dist is not None else float('nan')):>6.2f} "
              f"{r.get('distance_class','?'):>9} {match:>8}")

    print(f"\n[3] R3 — de las nuevas DIURNAS: {n_diurnas} total | "
          f"{n_diurnas_tp} matchean ALERTA MIROVA (TP) | {n_diurnas_fp} sin alerta (FP solar?)")
    print("  (TP* = MIROVA reporta esa noche pero con sensor no-MODIS; revisar)")
    print("\nNota: R2 pixel-level (TIF) es aparte: scripts/compare_tif_mirova_vs_ours.py")


if __name__ == "__main__":
    main()
