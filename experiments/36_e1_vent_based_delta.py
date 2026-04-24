"""36_e1_vent_based_delta.py — Delta E1 vs S15 usando VRP_VENT (no distance_class).

Contexto S17: el delta 35_summit_only usa final_hotspot_dist_km <= inner_radius
para filtrar summit. Pero la logica de final_hotspot en process_viirs.py
prioriza eruption-path sobre vent-path, entonces cuando Path A detecta un FP
regional (nube/nieve/sombra) mas fuerte que el vent, el record queda
clasificado "far" incluso si vrp_vent_mw > 0 capto el crater real.

Fisicamente: el vent-path solo dispara si hay un pixel dentro de
inner_radius con BT > t_bg + 1K. Si vrp_vent_mw > 0, por construccion la
deteccion esta en summit. Esto es mas robusto que depender de
final_hotspot_dist_km que puede quedar capturado por FPs lejanos mas
grandes.

Criterio TP en este script:
  - Hay ref MIROVA summit (dist <= inner) en la ventana.
  - Hay record nuestro matchee en sensor+tiempo (<=15 min).
  - El record tiene vrp_vent_mw > 0 (= vent-path detecto crater).

El VRP comparado es vrp_vent_mw (la senal sub-pixel del crater), no vrp_mw
(que puede incluir el FP regional).
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
        "VIIRS": {"VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"},
        "VIIRS375": {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"}}


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


def load_profile_vent_records(profile_dir, vols, start, end):
    """Carga records con campo vrp_vent_mw para evaluar vent-path en summit."""
    out = {}
    for vol in vols:
        p = ROOT / "data" / profile_dir / f"{vol}.json"
        if not p.exists():
            out[vol] = []
            continue
        d = json.load(open(p, "r", encoding="utf-8"))
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
            vrp_vent = r.get("vrp_vent_mw") or 0
            vrp_total = r.get("vrp_mir_mw") or r.get("vrp_mw") or 0
            vent_dist = r.get("vent_hotspot_dist_km")
            recs.append({"dt": dt, "sensor": r.get("sensor"),
                         "vrp_vent": vrp_vent, "vrp_total": vrp_total,
                         "vent_dist": vent_dist})
        out[vol] = recs
    return out


def find_days_processed(profile_dir, vols, start, end):
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
    """TP = match existe Y vrp_vent > 0. Ratio = vrp_vent/vrp_mirova."""
    tp, fn = [], []
    for m in refs:
        om = match(m, ours)
        if om is None or om["vrp_vent"] <= 0:
            fn.append(m)
        else:
            tp.append({"ratio": om["vrp_vent"] / m["vrp"] if m["vrp"] > 0 else 0,
                       "m_vrp": m["vrp"], "o_vrp_vent": om["vrp_vent"],
                       "o_vrp_total": om["vrp_total"]})
    rec = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) else 0
    rm = median([t["ratio"] for t in tp]) if tp else 0
    return {"tp": len(tp), "fn": len(fn), "recall": rec, "ratio_med": rm,
            "ratios": [t["ratio"] for t in tp]}


def main():
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    vols = ["Tupungatito", "Chaiten", "Lascar"]

    start = datetime(2026, 4, 8)
    end = datetime(2026, 4, 22, 23, 59)
    e1_days = find_days_processed("s9_vent_permissive", vols, start, end)
    if not e1_days:
        print("No hay dias procesados en s9_vent_permissive. Abortar.")
        return

    days_sorted = sorted(e1_days)
    start_eff = datetime.strptime(days_sorted[0], "%Y-%m-%d")
    end_eff = datetime.strptime(days_sorted[-1], "%Y-%m-%d") + timedelta(hours=23, minutes=59)

    print(f"S17 E1 Delta Report — VENT-BASED (vrp_vent_mw > 0)")
    print(f"Ventana efectiva: {days_sorted[0]} -> {days_sorted[-1]} ({len(e1_days)} dias)")
    print(f"Criterio TP: match sensor+tiempo + vrp_vent_mw > 0")
    print(f"Ratio: vrp_vent_mw / vrp_mirova (vent-path vs MIROVA)")
    print("=" * 78)

    refs = load_csv_refs(CSV_PATH, start_eff, end_eff)
    s15 = load_profile_vent_records("mirova_equivalent", vols, start_eff, end_eff)
    e1 = load_profile_vent_records("s9_vent_permissive", vols, start_eff, end_eff)

    refs_summit = {}
    for vol, rs in refs.items():
        inner = INNER_KM[vol]
        refs_summit[vol] = [r for r in rs if r["dist"] <= inner]

    print(f"\n{'Volcan':<14} {'N_summit':>8} | "
          f"{'TP_s15':>6} {'TP_e1':>6} | {'Rec_s15':>7} {'Rec_e1':>7} | "
          f"{'RatMed_s15':>10} {'RatMed_e1':>10}")
    print("-" * 100)

    for vol in vols:
        m_s15 = metrics(refs_summit.get(vol, []), s15.get(vol, []))
        m_e1 = metrics(refs_summit.get(vol, []), e1.get(vol, []))
        print(f"{vol:<14} {len(refs_summit.get(vol, [])):>8} | "
              f"{m_s15['tp']:>6} {m_e1['tp']:>6} | "
              f"{m_s15['recall']:>7.2f} {m_e1['recall']:>7.2f} | "
              f"{m_s15['ratio_med']:>10.2f} {m_e1['ratio_med']:>10.2f}")

    print()
    print("INTERPRETACION vent-based:")
    print("  - Cuenta TP si vent-path dispara (vrp_vent_mw > 0) Y match MIROVA.")
    print("  - Inmune al bug 'eruption regional enmascara vent local'.")
    print("  - Criterios handoff S17:")
    print("      Tupungatito recall >= 0.85 (vs S9 0.977)")
    print("      Chaiten recall    >= 0.90 (vs S9 0.929)")
    print("      Ratio_med en [0.5, 2.0] tolerable, [0.7, 1.4] ideal")


if __name__ == "__main__":
    main()
