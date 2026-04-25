"""37_nsigma_ab_test.py — S18 test A/B drift D2 (N·σ multiplier).

Contexto (docs/DRIFTS_S17.md D2): ningún paper MIROVA soporta n_sigma_mir=3.0
uniforme. Coppola 2016a Tabla 1 dice 5σ ROI1 / 10σ ROI2 / 15σ día para MODIS.
Di Bella 2024 §3.3 dice VIIRS 12σ noche / 8σ día. Los papers discrepan entre sí.

Test A/B: correr los 3 volcanes Tier A con 3 profiles distintos y comparar
F1/recall/precision contra MIROVA NRT CSV consolidado.

    profile            n_sigma_mir  fuente
    --------------     -----------  -----------------------------------------
    mirova_equivalent  3.0          baseline actual (sin respaldo documental)
    nsigma_mir_5       5.0          Coppola 2016a MODIS ROI1 noche
    nsigma_mir_12      12.0         Di Bella 2024 VIIRS noche

Criterio decisión (handoff S18): adoptar la config que maximice F1 sin
degradar recall < 0.60 en ningún Tier A. Si ninguna supera mirova_equivalent,
mantener baseline y documentar que 3σ uniforme, aunque sin paper, funciona
empíricamente mejor que las alternativas teóricas para nuestra geometría σ
(ROI bbox 50×50 km, no la "mitad-imagen VA" de Di Bella).

Prerequisito: los 3 profiles deben estar reprocesados en la ventana 2026-04-08
a 2026-04-22 para los 3 volcanes. Ver run_pipeline.py --profile <nombre>.
"""

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


ROOT = Path(__file__).parent.parent
# S19 2026-04-25: actualizado al CSV reciente con +5 días de cobertura.
CSV_PATH = ROOT / "registro_vrp_consolidado_25_04_2026.csv"

INNER_KM = {"Tupungatito": 7.0, "Chaiten": 5.0, "Lascar": 5.0}
VOLMAP = {"Lascar": "Lascar", "Chaiten": "Chaiten", "Tupungatito": "Tupungatito"}
SMAP = {
    "MODIS":    {"MODIS_TERRA", "MODIS_AQUA"},
    "VIIRS":    {"VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"},
    "VIIRS375": {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"},
}

PROFILES = ["mirova_equivalent", "nsigma_mir_5", "nsigma_mir_12"]
VOLS = ["Tupungatito", "Chaiten", "Lascar"]


def load_csv_refs(path, start, end):
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            vol = VOLMAP.get(r["Volcan"])
            if not vol:
                continue
            try:
                vrp = float(r["VRP_MW"])
                dt = datetime.strptime(r["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if vrp <= 0 or not (start <= dt <= end):
                continue
            if r["Sensor"] not in SMAP:
                continue
            out.setdefault(vol, []).append({
                "dt": dt, "sensor": r["Sensor"], "vrp": vrp,
                "dist": float(r.get("Distancia_km") or 0),
            })
    return out


def load_records(profile_dir, vol, start, end):
    p = ROOT / "data" / profile_dir / f"{vol}.json"
    if not p.exists():
        return []
    d = json.load(open(p, "r", encoding="utf-8"))
    out = []
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
        out.append({
            "dt": dt, "sensor": r.get("sensor"),
            "vrp": r.get("vrp_mw") or 0,
            "vrp_vent": r.get("vrp_vent_mw") or 0,
        })
    return out


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
    """TP: ref MIROVA existe y tenemos detección (vrp_vent>0 o vrp>0).
    FP: tenemos detección pero no hay ref MIROVA en la misma pasada.
    FN: hay ref MIROVA y no tenemos detección.
    """
    tp, fn = [], []
    matched_our_dts = set()
    for m in refs:
        om = match(m, ours)
        if om is None or (om["vrp_vent"] <= 0 and om["vrp"] <= 0):
            fn.append(m)
        else:
            tp.append({
                "ratio": (om["vrp_vent"] or om["vrp"]) / m["vrp"] if m["vrp"] > 0 else 0,
                "m_vrp": m["vrp"], "o_vrp": om["vrp_vent"] or om["vrp"],
            })
            matched_our_dts.add((om["dt"], om["sensor"]))

    # FP = detecciones nuestras no matched con ningún ref MIROVA
    fp = 0
    for r in ours:
        if r["vrp_vent"] <= 0 and r["vrp"] <= 0:
            continue
        if (r["dt"], r["sensor"]) not in matched_our_dts:
            fp += 1

    rec = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) else 0
    prec = len(tp) / (len(tp) + fp) if (len(tp) + fp) else 0
    f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
    rm = median([t["ratio"] for t in tp]) if tp else 0
    return {
        "tp": len(tp), "fp": fp, "fn": len(fn),
        "recall": rec, "precision": prec, "f1": f1,
        "ratio_med": rm,
    }


def main():
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # S19 2026-04-25: ventana extendida a 30 días (vs 15 de S18) para más
    # poder estadístico, especialmente Tupungatito (35 refs vs 17) y Lascar
    # (~85 refs vs 42).
    start = datetime(2026, 3, 25)
    end = datetime(2026, 4, 24, 23, 59)

    print("S19 Test A/B drift D2 — N·σ multiplier")
    print(f"Ventana: 2026-03-25 → 2026-04-24 (30 días) | Volcanes: {', '.join(VOLS)}")
    print(f"Criterio TP: match MIROVA sensor+tiempo (<=15 min) con vrp>0 nuestro")
    print("=" * 108)

    refs = load_csv_refs(CSV_PATH, start, end)
    refs_summit = {}
    for vol, rs in refs.items():
        inner = INNER_KM[vol]
        refs_summit[vol] = [r for r in rs if r["dist"] <= inner]

    # Tabla principal: profile × volcan × métricas
    print()
    print(f"{'Profile':<20} {'Volcan':<14} {'N_ref':>5} | "
          f"{'TP':>3} {'FP':>3} {'FN':>3} | "
          f"{'Rec':>5} {'Prec':>5} {'F1':>5} | {'RatMed':>7}")
    print("-" * 108)

    agg = {}  # profile -> aggregated metrics across volcanes
    for profile_dir in PROFILES:
        totals = {"tp": 0, "fp": 0, "fn": 0, "ratios": []}
        for vol in VOLS:
            ours = load_records(profile_dir, vol, start, end)
            if not ours:
                print(f"{profile_dir:<20} {vol:<14} {'--':>5} | "
                      f"{'-':>3} {'-':>3} {'-':>3} | "
                      f"{'-':>5} {'-':>5} {'-':>5} | {'-':>7}  NO DATA")
                continue
            m = metrics(refs_summit.get(vol, []), ours)
            print(f"{profile_dir:<20} {vol:<14} {len(refs_summit.get(vol, [])):>5} | "
                  f"{m['tp']:>3} {m['fp']:>3} {m['fn']:>3} | "
                  f"{m['recall']:>5.2f} {m['precision']:>5.2f} {m['f1']:>5.2f} | "
                  f"{m['ratio_med']:>7.2f}")
            totals["tp"] += m["tp"]
            totals["fp"] += m["fp"]
            totals["fn"] += m["fn"]
        agg[profile_dir] = totals
        print()

    # Tabla agregada
    print("=" * 108)
    print(f"{'Profile agregado':<20} {'TP_all':>6} {'FP_all':>6} {'FN_all':>6} | "
          f"{'Rec':>5} {'Prec':>5} {'F1':>5}")
    print("-" * 108)
    for profile_dir, t in agg.items():
        tp, fp, fn = t["tp"], t["fp"], t["fn"]
        rec = tp / (tp + fn) if (tp + fn) else 0
        prec = tp / (tp + fp) if (tp + fp) else 0
        f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
        print(f"{profile_dir:<20} {tp:>6} {fp:>6} {fn:>6} | "
              f"{rec:>5.2f} {prec:>5.2f} {f1:>5.2f}")

    print()
    print("Decisión (handoff S18):")
    print("  Adoptar el profile con mayor F1 agregado, siempre que ningún volcán")
    print("  individual tenga recall < 0.60.")
    print("  Si mirova_equivalent (baseline 3σ) gana: documentar drift D2 como")
    print("  empíricamente correcto aunque sin respaldo en papers.")


if __name__ == "__main__":
    main()
