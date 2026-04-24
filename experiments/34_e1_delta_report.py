"""34_e1_delta_report.py — delta S15 vs S16 E1 (s9_vent_permissive).

Compara crossmatch MIROVA CSV contra:
  - data/mirova_equivalent/ (S15 fixes, vent-path sigma-gated S12+)
  - data/s9_vent_permissive/ (E1 test, vent-path S9 fijo 1K)

Filtra a ventana común procesada por ambos (2026-04-08 -> 2026-04-22).
Volcanes: Tupungatito, Chaiten, Lascar.

Veredicto H1 confirmada si:
  - Tupungatito recall E1 >= 0.85 (vs S15 0.45).
  - Chaiten recall E1 >= 0.90 (vs S15 0.80).
  - Lascar recall no baja (canary: ratio mantenido [0.7, 1.4]).
  - Precision no cae bajo 0.30.

Si H1 confirmada -> proponer incorporar n_sigma_vent=0 a mirova_equivalent.
Si no -> probar E2 (MODIS vent threshold S9) o re-examinar arquitectura.
"""

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / "21_04_2026 registro_vrp_consolidado.csv"

# Ventana común E1 (días reprocesados ambos perfiles)
START = datetime(2026, 4, 8)
END = datetime(2026, 4, 22, 23, 59)

VOLMAP = {"Lascar": "Lascar", "Chaiten": "Chaiten",
          "Tupungatito": "Tupungatito"}
SMAP = {"MODIS": {"MODIS_TERRA", "MODIS_AQUA"},
        "VIIRS": {"VIIRS_SNPP_750", "VIIRS_NOAA20_750"},
        "VIIRS375": {"VIIRS_SNPP", "VIIRS_NOAA20"}}


def load_csv_refs(path):
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
            if vrp <= 0 or not (START <= dt <= END):
                continue
            if r["Sensor"] not in SMAP:
                continue
            out.setdefault(vol, []).append(
                {"dt": dt, "sensor": r["Sensor"], "vrp": vrp})
    return out


def load_profile_records(profile_dir, vols):
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
            if not (START <= dt <= END):
                continue
            v = r.get("vrp_mir_mw") or r.get("vrp_mw") or 0
            recs.append({
                "dt": dt, "sensor": r.get("sensor"),
                "vrp": v,
                "dist_km": r.get("final_hotspot_dist_km")
                         or r.get("hotspot_dist_km") or 0,
            })
        out[vol] = recs
    return out


def match(mirova_det, our_recs):
    compat = SMAP.get(mirova_det["sensor"], set())
    best, best_dt = None, timedelta.max
    for r in our_recs:
        if r["sensor"] not in compat:
            continue
        delta = abs(r["dt"] - mirova_det["dt"])
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
            ratio = om["vrp"] / m["vrp"]
            tp.append({"ratio": ratio, "m_vrp": m["vrp"], "o_vrp": om["vrp"]})
    # FPs: our detections without MIROVA match
    fp = []
    for r in ours:
        if r["vrp"] <= 0:
            continue
        hit = False
        for m in refs:
            if r["sensor"] in SMAP.get(m["sensor"], set()) and \
               abs(r["dt"] - m["dt"]) <= timedelta(minutes=15):
                hit = True
                break
        if not hit:
            fp.append(r)
    rec = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) else 0
    prec = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) else 0
    rm = median([t["ratio"] for t in tp]) if tp else 0
    return {
        "tp": len(tp), "fn": len(fn), "fp": len(fp),
        "recall": rec, "precision": prec, "ratio_med": rm,
    }


def main():
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    vols = ["Tupungatito", "Chaiten", "Lascar"]
    refs = load_csv_refs(CSV_PATH)
    s15 = load_profile_records("mirova_equivalent", vols)
    e1 = load_profile_records("s9_vent_permissive", vols)

    print("S16 E1 Delta Report — s9_vent_permissive vs mirova_equivalent")
    print("Ventana: 2026-04-08 -> 2026-04-22")
    print("=" * 78)

    print(f"\n{'Volcan':<14} {'N_CSV':>5} | {'TP_s15':>6} {'TP_e1':>6} | "
          f"{'Rec_s15':>7} {'Rec_e1':>7} | {'Prec_s15':>8} {'Prec_e1':>8} | "
          f"{'RatMed_s15':>10} {'RatMed_e1':>10}")
    print("-" * 100)

    verdict_table = []
    for vol in vols:
        v_refs = refs.get(vol, [])
        m_s15 = metrics(v_refs, s15.get(vol, []))
        m_e1 = metrics(v_refs, e1.get(vol, []))
        print(f"{vol:<14} {len(v_refs):>5} | "
              f"{m_s15['tp']:>6} {m_e1['tp']:>6} | "
              f"{m_s15['recall']:>7.2f} {m_e1['recall']:>7.2f} | "
              f"{m_s15['precision']:>8.2f} {m_e1['precision']:>8.2f} | "
              f"{m_s15['ratio_med']:>10.2f} {m_e1['ratio_med']:>10.2f}")
        verdict_table.append((vol, m_s15, m_e1))

    # Veredicto H1
    print()
    print("=" * 78)
    print("Criterios H1:")
    tup_s15 = next((m_e1 for v, m_s15, m_e1 in verdict_table if v == "Tupungatito"), None)
    cha_e1 = next((m_e1 for v, m_s15, m_e1 in verdict_table if v == "Chaiten"), None)
    las_e1 = next((m_e1 for v, m_s15, m_e1 in verdict_table if v == "Lascar"), None)
    las_s15 = next((m_s15 for v, m_s15, m_e1 in verdict_table if v == "Lascar"), None)

    if tup_s15:
        ok = tup_s15["recall"] >= 0.85
        print(f"  [{'OK' if ok else 'FAIL'}] Tupungatito recall >= 0.85: {tup_s15['recall']:.2f}")
    if cha_e1:
        ok = cha_e1["recall"] >= 0.90
        print(f"  [{'OK' if ok else 'FAIL'}] Chaiten recall >= 0.90: {cha_e1['recall']:.2f}")
    if las_e1 and las_s15:
        ratio_stable = 0.70 <= las_e1["ratio_med"] <= 1.40
        recall_stable = las_e1["recall"] >= las_s15["recall"] - 0.05
        print(f"  [{'OK' if ratio_stable else 'FAIL'}] Lascar ratio estable [0.70-1.40]: {las_e1['ratio_med']:.2f}")
        print(f"  [{'OK' if recall_stable else 'FAIL'}] Lascar recall no regresa: {las_e1['recall']:.2f} vs S15 {las_s15['recall']:.2f}")

    print()
    print("Interpretación:")
    print("  - Si Tupungatito y Chaiten suben a umbrales: H1 CONFIRMADA.")
    print("    -> integrar n_sigma_vent=0 en mirova_equivalent por defecto.")
    print("  - Si no suben: H1 descartada o parcial. Proceder a E2 (MODIS vent S9).")


if __name__ == "__main__":
    main()
