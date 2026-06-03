"""S99 — Auditoría A/B del fix de magnitud Test 1 (baseline / pixfilter / core).

Reusa el método validado de experiments/_s98_anchor/audit_ratio.py. Match ALERTA
MIROVA (CONS+OCR, latest) → nuestro record por Fecha_Satelite_UTC (±15 min) +
familia de sensor. Ratio = pc.vrp_mw / MIROVA_VRP (A10).

Compara 3 datasets (artifacts del run A/B):
  baseline  = _s99_test1_baseline  (sin fix)
  pixfilter = _s99_test1_pixfilter (Candidato A: filtro por-píxel dual-ROI)
  core      = _s99_test1_core      (Candidato B: recorte compacidad espacial)

Volcanes: Tupungatito (cura), Villarrica (CANARIO FN), Lascar (control).

CRITERIOS (diseño 2026-06-03):
  1. Tupungatito ratio mediano → [0.5, 2.0] (de ~19×).
  2. Villarrica recall NO baja vs baseline; ningún record MIROVA-confirmado → VRP=0.
  3. Lascar sin cambio.

Uso:
  gh run download <RUN_ID> -D experiments/_s99_audit/_ab_art
  python experiments/_s99_audit/ab_test1_audit.py
Artifacts esperados: _ab_art/s99-<profile>-<vol>/<vol>.json
Ground truth fresco: latest_consolidado.csv (root) + data/mirova_reference/registro_vrp_ocr.csv (A17).
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
ART = _REPO / "experiments/_s99_audit/_ab_art"

VOLS = ["Tupungatito", "Villarrica", "Lascar"]
PROFILES = ["_s99_test1_baseline", "_s99_test1_core", "_s99_test1_ctxpeak"]
# A14: variantes de nombre CSV (estos 3 son simples).
CSV_NAME = {"Tupungatito": "Tupungatito", "Villarrica": "Villarrica", "Lascar": "Lascar"}


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
    # fromisoformat (Py3.11+) acepta espacio o 'T', con o sin segundos.
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    # nuestros records vienen SIN segundos ('2026-04-01 04:48'); refs MIROVA CON.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s[:len("2026-01-01 00:00:00") if ":" in s[14:] else 16], fmt)
        except (ValueError, IndexError):
            continue
    return None


def load_refs(path, vol_csv, types):
    refs = []
    if not Path(path).exists():
        return refs
    with open(path, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row.get("Volcan") != vol_csv:
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
    p = ART / f"s99-{profile}-{vol}" / f"{vol}.json"
    if not p.exists():
        return None
    d = json.load(open(p, encoding="utf-8"))
    return d if isinstance(d, list) else d.get("records", [])


def match(refs, recs):
    """Devuelve (recall_detectado, ratios[], n_zeroed) contra un dataset nuestro.

    n_zeroed = ALERTAS MIROVA con VRP>0 para las que existe un record nuestro
    coincidente (mismo tiempo+sensor) pero con pc.vrp_mw == 0 → falso negativo
    de magnitud (canario FN). Cuenta solo alertas reales (MIROVA vrp>0).
    """
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
            zeroed += 1  # MIROVA detectó (vrp>0), nosotros tenemos record pero pc.vrp=0
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
        csvn = CSV_NAME[vol]
        refs = (load_refs(CSV_CONS, csvn, ["ALERTA_TERMICA"]) +
                load_refs(CSV_OCR, csvn, ["ALERTA_TERMICA_OCR"]))
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

    outp = _REPO / "experiments/_s99_audit/ab_test1_result.json"
    json.dump(results, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    def g(d, k, default="-"):
        return d.get(k, default) if d and d.get("present") else "NA"

    short = {"_s99_test1_baseline": "baseline", "_s99_test1_pixfilter": "pixfilter",
             "_s99_test1_core": "core(esp)", "_s99_test1_eq16": "eq16(LL)",
             "_s99_test1_ctx": "ctx(MIR)", "_s99_test1_ctxpeak": "ctx+peak"}
    L = [f"=== S99 A/B Test1 magnitude vs MIROVA (CONS+OCR latest) — {WIN_START.date()}..{WIN_END.date()} ==="]
    L.append("rec=ALERTAS detectadas pc.vrp>0 | rat=mediana pc.vrp/MIROVA | in%=ratios en [0.5,2] | z=FN magnitud (record existe, pc.vrp=0)")
    L.append(f"{'volcano':<13} {'profile':<11} {'alert':>5} {'rec':>4} {'ratio':>8} {'in%':>5} {'z(FN)':>5}")
    for r in results:
        for prof in PROFILES:
            d = r["by_profile"].get(prof, {})
            L.append(f"{r['volcano']:<13} {short[prof]:<11} {r['n_alertas']:>5} "
                     f"{str(g(d,'recall_detected')):>4} {str(g(d,'ratio_median')):>8} "
                     f"{str(g(d,'pct_in_0p5_2p0')):>5} {str(g(d,'n_zeroed')):>5}")
        L.append("")
    L.append("CRITERIOS: core baja ratio Tupungatito a [0.5,2.0]; eq16 baja ratio Villarrica;")
    L.append("NINGUN candidato sube z(FN) de Villarrica vs baseline (canario veto).")
    txt = "\n".join(L)
    print(txt)
    (_REPO / "experiments/_s99_audit/ab_test1_summary.txt").write_text(txt, encoding="utf-8")
    if not ART.exists():
        print(f"\n[!] {ART} no existe aún — corré primero: gh run download <RUN_ID> -D {ART}", file=sys.stderr)


if __name__ == "__main__":
    main()
