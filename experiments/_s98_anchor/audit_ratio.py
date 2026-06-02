"""S98 — Auditoría de RATIO de magnitud vs MIROVA (baseline vs fix del ancla).

Reutiliza el método validado en experiments/115_s65_audit_tupungatito_post_fix.py
(mismo fix, S65 dio 0.67×). Match ALERTA MIROVA (CONS+OCR) → nuestro record por
Fecha_Satelite_UTC (±15 min) + familia de sensor. Ratio = pc.vrp_mw / MIROVA_VRP
(A10: pc.vrp_mw, NO record.vrp_mw scene-wide).

Compara baseline (data/mirova_equivalent/, ancla mirova_center) vs fix
(data/_s98_anchor/, ancla cráter). Criterio (diseño): ratio mediano hacia
0.5–2.0; recall NO cae.

Ground truth: snapshot MIROVA CONS+OCR (cubre hasta 2026-05-18) → ventana de
ratio acotada a 05-01..05-18. A14: nombres CSV con variantes.
A17: para cobertura fresca, actualizar el CSV; aquí usamos el snapshot
versionado (reproducible).
"""
import csv
import json
import statistics as st
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
WIN_START = datetime(2026, 5, 1)
WIN_END = datetime(2026, 5, 18, 23, 59, 59)  # snapshot CONS llega a 05-18

CSV_BASE = _REPO / "data/mirova_reference/mirova_v1_snapshot"
CSV_CONS = CSV_BASE / "registro_vrp_consolidado.csv"
CSV_OCR = CSV_BASE / "registro_vrp_ocr.csv"

# A14: variantes de nombre en el CSV del scraper Mirova-v1
CSV_NAME = {
    "Tupungatito": "Tupungatito",
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Lascar": "Lascar",
    "Villarrica": "Villarrica",
}


def sensor_family(s):
    s = s or ""
    if "MODIS" in s:
        return "MODIS"
    if "750" in s:
        return "VIIRS750"
    if "VIIRS" in s:
        return "VIIRS375"
    return s


def load_refs(path, vol_csv, types):
    refs = []
    if not Path(path).exists():
        return refs
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Volcan") != vol_csv:
                continue
            if row.get("Tipo_Registro") not in types:
                continue
            try:
                dt = datetime.strptime(row["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                continue
            if not (WIN_START <= dt <= WIN_END):
                continue
            try:
                vrp = float(row["VRP_MW"])
            except (ValueError, KeyError):
                continue
            refs.append({"dt": dt, "sensor": row.get("Sensor", ""), "vrp": vrp})
    return refs


def _load_our(subdir, name):
    p = _REPO / "data" / subdir / f"{name}.json"
    if not p.exists():
        return None
    d = json.load(open(p, encoding="utf-8"))
    return d if isinstance(d, list) else d.get("records", [])


def _match_ratio(refs, recs):
    """Devuelve (n_alertas, recall_detected, ratios[]) contra un dataset nuestro."""
    ratios, detected = [], 0
    for r in refs:
        cands = []
        for rec in recs:
            try:
                rdt = datetime.fromisoformat(str(rec["datetime_utc"]).replace("Z", ""))
            except (ValueError, KeyError):
                continue
            if abs((rdt - r["dt"]).total_seconds()) > 900:
                continue
            if sensor_family(rec.get("sensor", "")) != sensor_family(r["sensor"]):
                continue
            cands.append(rec)
        if not cands:
            continue
        best = min(cands, key=lambda x: (x.get("primary_cluster") or {}).get("centroid_dist_km", 99))
        pc_vrp = (best.get("primary_cluster") or {}).get("vrp_mw", 0) or 0
        if pc_vrp <= 0:
            continue
        detected += 1
        if r["vrp"] > 0:
            ratios.append(pc_vrp / r["vrp"])
    return detected, ratios


def _summ(detected, n_alertas, ratios):
    o = {"n_alertas": n_alertas, "recall_detected": detected,
         "recall_pct": round(100 * detected / n_alertas, 1) if n_alertas else None}
    if ratios:
        o["ratio_median"] = round(st.median(ratios), 3)
        o["ratio_min"] = round(min(ratios), 3)
        o["ratio_max"] = round(max(ratios), 3)
        o["pct_in_0p5_2p0"] = round(100 * sum(1 for x in ratios if 0.5 <= x <= 2.0) / len(ratios), 1)
        o["n_ratios"] = len(ratios)
    return o


def main():
    results = []
    for our, csvn in CSV_NAME.items():
        refs = (load_refs(CSV_CONS, csvn, ["ALERTA_TERMICA"]) +
                load_refs(CSV_OCR, csvn, ["ALERTA_TERMICA_OCR"]))
        n = len(refs)
        base = _load_our("mirova_equivalent", our) or []
        fix = _load_our("_s98_anchor", our)
        row = {"volcano": our, "n_alertas": n, "fix_data_present": fix is not None}
        d_b, rt_b = _match_ratio(refs, base)
        row["baseline"] = _summ(d_b, n, rt_b)
        if fix is not None:
            d_f, rt_f = _match_ratio(refs, fix)
            row["fix"] = _summ(d_f, n, rt_f)
        results.append(row)

    outp = _REPO / "experiments/_s98_anchor/audit_ratio_result.json"
    json.dump(results, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    L = [f"=== S98 ratio vs MIROVA (CONS+OCR) — ventana {WIN_START.date()}..{WIN_END.date()} ==="]
    L.append(f"{'volcano':<20} {'alertas':>7} {'b_rec':>6} {'f_rec':>6} "
             f"{'b_ratio':>8} {'f_ratio':>8} {'b_in%':>6} {'f_in%':>6}")
    for r in results:
        b = r["baseline"]
        f = r.get("fix")
        f_rec = f["recall_detected"] if f else "-"
        f_ratio = f.get("ratio_median", "-") if f else "-"
        f_in = f.get("pct_in_0p5_2p0", "-") if f else "-"
        L.append(f"{r['volcano']:<20} {r['n_alertas']:>7} {b['recall_detected']:>6} {str(f_rec):>6} "
                 f"{str(b.get('ratio_median','-')):>8} {str(f_ratio):>8} "
                 f"{str(b.get('pct_in_0p5_2p0','-')):>6} {str(f_in):>6}")
    L.append("")
    L.append("rec = ALERTAS detectadas con pc.vrp>0 (recall). ratio = mediana pc.vrp/MIROVA.")
    L.append("in% = % de ratios en [0.5, 2.0]. CRITERIO: f_ratio hacia 0.5-2.0; recall no cae.")
    txt = "\n".join(L)
    print(txt)
    (_REPO / "experiments/_s98_anchor/audit_ratio_summary.txt").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
