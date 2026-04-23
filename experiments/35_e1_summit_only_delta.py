"""35_e1_summit_only_delta.py — Delta E1 vs S15 FILTRADO A SUMMIT-ONLY.

Contexto: el delta general (experiments/34_e1_delta_report.py) esta
contaminado por FPs bbox-edge (Lascar capta Salar de Atacama a 22-23 km,
Tupungatito capta Embalse El Yeso a 25-27 km). Esos FPs vienen de bbox
S15 + Path A sin water filter (P3.6 pendiente), NO del cambio E1
(que solo afecta vent-path).

Para aislar el efecto real de H1, este script filtra a registros donde el
hotspot principal esta dentro del inner_radius_km (summit). Es equivalente
a aplicar el filtro distance_class == "summit" pero computado manualmente
dado que los records ya reprocesados pueden no tener ese campo consistente.

Filtro per-volcano inner_radius:
  Tupungatito: 7 km
  Chaiten: 5 km
  Lascar: 5 km

Aplica tanto a mirova_equivalent (S15) como a s9_vent_permissive (E1).
"""

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / "21_04_2026 registro_vrp_consolidado.csv"

INNER_KM = {"Tupungatito": 7.0, "Chaiten": 5.0, "Lascar": 5.0}
VOLMAP = {"Lascar": "Lascar", "Chaiten": "Chaiten", "Tupungatito": "Tupungatito"}
SMAP = {"MODIS": {"MODIS_TERRA", "MODIS_AQUA"},
        "VIIRS": {"VIIRS_SNPP_750", "VIIRS_NOAA20_750"},
        "VIIRS375": {"VIIRS_SNPP", "VIIRS_NOAA20"}}


def load_csv_refs(path, start, end):
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            vol = VOLMAP.get(r["Volcan"])
            if not vol:
                continue
            try:
                vrp = float(r["VRP_MW"])
                dt = datetime.strptime(r["Fecha_Satelite_UTC"],
                                        "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if vrp <= 0 or not (start <= dt <= end):
                continue
            if r["Sensor"] not in SMAP:
                continue
            out.setdefault(vol, []).append(
                {"dt": dt, "sensor": r["Sensor"], "vrp": vrp,
                 "dist": float(r.get("Distancia_km") or 0)})
    return out


def load_profile_summit_records(profile_dir, vols, start, end):
    """Carga records per-volcano FILTRADOS a summit-only."""
    out = {}
    for vol in vols:
        p = ROOT / "data" / profile_dir / f"{vol}.json"
        if not p.exists():
            out[vol] = []
            continue
        d = json.load(open(p, "r", encoding="utf-8"))
        inner = INNER_KM[vol]
        recs = []
        for r in d.get("records", []):
            dt_str = r.get("datetime_utc", "")
            if not dt_str:
                continue
            try:
                dt = datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if not (start <= dt <= end):
                continue
            # Filter summit-only: final_hotspot dist OR distance_class="summit"
            dist = r.get("final_hotspot_dist_km") or r.get("hotspot_dist_km") or 0
            dclass = r.get("distance_class")
            is_summit = (dclass == "summit") or (dist <= inner and dist > 0)
            if not is_summit:
                continue
            v = r.get("vrp_mir_mw") or r.get("vrp_mw") or 0
            recs.append({"dt": dt, "sensor": r.get("sensor"), "vrp": v, "dist": dist})
        out[vol] = recs
    return out


def find_days_processed(profile_dir, vols, start, end):
    """Devuelve el set de dias (YYYY-MM-DD) efectivamente procesados por perfil."""
    days = set()
    for vol in vols:
        p = ROOT / "data" / profile_dir / f"{vol}.json"
        if not p.exists():
            continue
        d = json.load(open(p, "r", encoding="utf-8"))
        for r in d.get("records", []):
            dt_str = r.get("datetime_utc", "")[:10]
            if not dt_str:
                continue
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
            except ValueError:
                continue
            if start <= dt <= end:
                days.add(dt_str)
    return days


def match(m, ours):
    compat = SMAP.get(m["sensor"], set())
    best, best_dt = None, timedelta.max
    for r in ours:
        if r["sensor"] not in compat:
            continue
        delta = abs(r["dt"] - m["dt"])
        if delta < best_dt and delta <= timedelta(minutes=15):
            best, best_dt = r, delta
    return best


def metrics(refs, ours):
    tp, fn = [], []
    for m in refs:
        om = match(m, ours)
        if om is None or om["vrp"] <= 0:
            fn.append(m)
        else:
            tp.append({"ratio": om["vrp"] / m["vrp"] if m["vrp"] > 0 else 0,
                       "m_vrp": m["vrp"], "o_vrp": om["vrp"]})
    rec = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) else 0
    rm = median([t["ratio"] for t in tp]) if tp else 0
    return {"tp": len(tp), "fn": len(fn), "recall": rec, "ratio_med": rm}


def main():
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    vols = ["Tupungatito", "Chaiten", "Lascar"]

    # Filtrar ventana a dias efectivamente procesados por E1
    start = datetime(2026, 4, 8)
    end = datetime(2026, 4, 22, 23, 59)
    e1_days = find_days_processed("s9_vent_permissive", vols, start, end)
    if not e1_days:
        print("No hay dias procesados en s9_vent_permissive. Abortar.")
        return

    days_sorted = sorted(e1_days)
    start_eff = datetime.strptime(days_sorted[0], "%Y-%m-%d")
    end_eff = datetime.strptime(days_sorted[-1], "%Y-%m-%d") + timedelta(hours=23, minutes=59)

    print(f"S16 E1 Delta Report — SUMMIT ONLY (filtra FPs bbox-edge)")
    print(f"Ventana efectiva: {days_sorted[0]} -> {days_sorted[-1]} ({len(e1_days)} dias)")
    print(f"Filter: pixel dentro inner_radius (Tupungatito 7, Chaiten 5, Lascar 5 km)")
    print("=" * 78)

    refs = load_csv_refs(CSV_PATH, start_eff, end_eff)
    s15 = load_profile_summit_records("mirova_equivalent", vols, start_eff, end_eff)
    e1 = load_profile_summit_records("s9_vent_permissive", vols, start_eff, end_eff)

    # Tambien filtrar refs CSV a summit (dist <= inner)
    refs_summit = {}
    for vol, rs in refs.items():
        inner = INNER_KM[vol]
        refs_summit[vol] = [r for r in rs if r["dist"] <= inner]

    print(f"\n{'Volcan':<14} {'N_CSV_summit':>12} | "
          f"{'TP_s15':>6} {'TP_e1':>6} | {'Rec_s15':>7} {'Rec_e1':>7} | "
          f"{'RatMed_s15':>10} {'RatMed_e1':>10}")
    print("-" * 100)

    for vol in vols:
        m_s15 = metrics(refs_summit.get(vol, []), s15.get(vol, []))
        m_e1 = metrics(refs_summit.get(vol, []), e1.get(vol, []))
        print(f"{vol:<14} {len(refs_summit.get(vol, [])):>12} | "
              f"{m_s15['tp']:>6} {m_e1['tp']:>6} | "
              f"{m_s15['recall']:>7.2f} {m_e1['recall']:>7.2f} | "
              f"{m_s15['ratio_med']:>10.2f} {m_e1['ratio_med']:>10.2f}")

    print()
    print("INTERPRETACION summit-only:")
    print("  - Este delta muestra SOLO pixels dentro del edificio volcanico.")
    print("  - Aisla el efecto H1 (vent-path) de los FPs bbox-edge S15.")
    print("  - Si E1 recall > S15 recall en summit: H1 confirmada parcial.")
    print("  - Los FPs bbox-edge quedan documentados como problema SEPARADO")
    print("    que requiere water filter (P3.6) antes de push bbox a main.")


if __name__ == "__main__":
    main()
