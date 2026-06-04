"""S100 — Auditoria A/B ampliada del fix de magnitud Test 1 (baseline vs ctxpeak)
sobre LOS 11 Tier A (no solo los 3 del A/B S99).

Generaliza experiments/_s99_audit/ab_test1_audit.py: pregunta de Nicolas S100 — el
flag enable_test1_contextual_* se aplica a todos los Tier A, asi que la adopcion
debe validarse contra toda la base. Match ALERTA MIROVA (CONS+OCR latest) → nuestro
record por Fecha_Satelite_UTC (+-15 min) + familia de sensor. Ratio = pc.vrp_mw /
MIROVA_VRP (A10).

CRITERIO ADOPCION (por-volcan):
  ctxpeak NO baja recall vs baseline, NO suma FN (z) vs baseline, ratio same-or-better.

Uso:
  gh run download <RUN_ID> -D experiments/_s99_audit/_ab_full_art
  python experiments/_s99_audit/ab_test1_audit_full.py
Artifacts esperados: _ab_full_art/s100-<profile>-<vol>/<vol>.json
Ground truth fresco: latest_consolidado.csv (root) + registro_vrp_ocr.csv (A17).
"""
import csv
import json
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
WIN_START = datetime(2026, 4, 1)
WIN_END = datetime(2026, 5, 31, 23, 59, 59)

CSV_CONS = _REPO / "latest_consolidado.csv"
CSV_OCR = _REPO / "data/mirova_reference/registro_vrp_ocr.csv"
ART = _REPO / "experiments/_s99_audit/_ab_full_art"

VOLS = ["Tupungatito", "Villarrica", "Lascar", "Lastarria", "Isluga", "Llaima",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle", "Chaiten",
        "Copahue"]
PROFILES = ["_s99_test1_baseline", "_s99_test1_ctxpeak"]
# A14: TODAS las variantes de nombre CSV por volcan (verificadas S100 contra CSV).
CSV_NAMES = {
    "Tupungatito": ["Tupungatito"],
    "Villarrica": ["Villarrica"],
    "Lascar": ["Lascar"],
    "Lastarria": ["Lastarria"],
    "Isluga": ["Isluga"],
    "Llaima": ["Llaima"],
    "NevadosDeChillan": ["Nevados de Chillan"],
    "PlanchonPeteroa": ["PlanchonPeteroa", "Peteroa"],  # A14: dos variantes
    "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle"],
    "Chaiten": ["Chaiten"],
    "Copahue": ["Copahue"],
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


def _parse_dt(s):
    s = str(s).replace("Z", "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s[:len("2026-01-01 00:00:00") if ":" in s[14:] else 16], fmt)
        except (ValueError, IndexError):
            continue
    return None


def load_refs(path, vol_csv_names, types):
    refs = []
    if not Path(path).exists():
        return refs
    with open(path, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row.get("Volcan") not in vol_csv_names:
                continue
            if row.get("Tipo_Registro") not in types:
                continue
            dt = _parse_dt(row.get("Fecha_Satelite_UTC", ""))
            if dt is None or not (WIN_START <= dt <= WIN_END):
                continue
            try:
                vrp = float(str(row["VRP_MW"]).replace(",", "."))
            except (ValueError, KeyError):
                continue
            refs.append({"dt": dt, "sensor": row.get("Sensor", ""), "vrp": vrp})
    return refs


def load_our(profile, vol):
    p = ART / f"s100-{profile}-{vol}" / f"{vol}.json"
    if not p.exists():
        return None
    d = json.load(open(p, encoding="utf-8"))
    return d if isinstance(d, list) else d.get("records", [])


def match(refs, recs):
    """(recall_detectado, ratios[], n_zeroed). z = FN magnitud (record existe, pc.vrp=0)."""
    detected, zeroed = 0, 0
    ratios = []
    for r in refs:
        cands = []
        for rec in recs:
            rdt = _parse_dt(rec.get("datetime_utc", ""))
            if rdt is None:
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
        if pc_vrp > 0:
            detected += 1
            if r["vrp"] > 0:
                ratios.append(pc_vrp / r["vrp"])
        elif r["vrp"] > 0:
            zeroed += 1
    return detected, ratios, zeroed


def summ(detected, n, ratios, zeroed):
    o = {"n_alertas": n, "recall_detected": detected, "n_zeroed": zeroed,
         "recall_pct": round(100 * detected / n, 1) if n else None}
    if ratios:
        o["ratio_median"] = round(st.median(ratios), 3)
        o["ratio_max"] = round(max(ratios), 3)
        o["pct_in_0p5_2p0"] = round(100 * sum(1 for x in ratios if 0.5 <= x <= 2.0) / len(ratios), 1)
        o["n_ratios"] = len(ratios)
    return o


def main():
    results = []
    for vol in VOLS:
        names = CSV_NAMES[vol]
        refs = (load_refs(CSV_CONS, names, ["ALERTA_TERMICA"]) +
                load_refs(CSV_OCR, names, ["ALERTA_TERMICA_OCR"]))
        n = len(refs)
        row = {"volcano": vol, "n_alertas": n, "by_profile": {}}
        for prof in PROFILES:
            recs = load_our(prof, vol)
            if recs is None:
                row["by_profile"][prof] = {"present": False}
                continue
            d, rt, z = match(refs, recs)
            s = summ(d, n, rt, z)
            s["present"] = True
            row["by_profile"][prof] = s
        results.append(row)

    outp = _REPO / "experiments/_s99_audit/ab_test1_full_result.json"
    json.dump(results, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    def g(d, k):
        return d.get(k, "-") if d and d.get("present") else "NA"

    short = {"_s99_test1_baseline": "baseline", "_s99_test1_ctxpeak": "ctx+peak"}
    L = [f"=== S100 A/B Test1 magnitude FULL (11 Tier A) vs MIROVA CONS+OCR — {WIN_START.date()}..{WIN_END.date()} ==="]
    L.append("rec=ALERTAS detectadas pc.vrp>0 | rat=mediana pc.vrp/MIROVA | in%=ratios en [0.5,2] | z=FN magnitud")
    L.append(f"{'volcano':<22} {'profile':<10} {'alert':>5} {'rec':>4} {'ratio':>8} {'in%':>5} {'z(FN)':>5}")
    # Veredicto por-volcan (criterio adopcion).
    verdicts = []
    for r in results:
        for prof in PROFILES:
            d = r["by_profile"].get(prof, {})
            L.append(f"{r['volcano']:<22} {short[prof]:<10} {r['n_alertas']:>5} "
                     f"{str(g(d,'recall_detected')):>4} {str(g(d,'ratio_median')):>8} "
                     f"{str(g(d,'pct_in_0p5_2p0')):>5} {str(g(d,'n_zeroed')):>5}")
        # comparar ctxpeak vs baseline
        bl = r["by_profile"].get("_s99_test1_baseline", {})
        cp = r["by_profile"].get("_s99_test1_ctxpeak", {})
        if bl.get("present") and cp.get("present"):
            d_rec = (cp.get("recall_detected", 0) or 0) - (bl.get("recall_detected", 0) or 0)
            d_z = (cp.get("n_zeroed", 0) or 0) - (bl.get("n_zeroed", 0) or 0)
            ok = (d_rec >= 0 and d_z <= 0)
            verdicts.append((r["volcano"], ok, d_rec, d_z,
                             bl.get("ratio_median"), cp.get("ratio_median")))
        L.append("")
    L.append("--- VEREDICTO ctxpeak vs baseline (criterio: d_recall>=0 AND d_FN<=0) ---")
    for vol, ok, d_rec, d_z, bl_r, cp_r in verdicts:
        flag = "OK " if ok else "!! "
        L.append(f"{flag}{vol:<22} d_recall={d_rec:+d}  d_FN={d_z:+d}  ratio {bl_r}->{cp_r}")
    n_bad = sum(1 for _, ok, *_ in verdicts if not ok)
    L.append("")
    L.append(f"ADOPCION GLOBAL: {'TODOS OK — adoptar ctxpeak' if n_bad == 0 else f'{n_bad} vol(es) con regresion — revisar antes de adoptar'}")
    txt = "\n".join(L)
    print(txt)
    (_REPO / "experiments/_s99_audit/ab_test1_full_summary.txt").write_text(txt, encoding="utf-8")
    if not ART.exists():
        print(f"\n[!] {ART} no existe aun — corre: gh run download <RUN_ID> -D {ART}", file=sys.stderr)


if __name__ == "__main__":
    main()
