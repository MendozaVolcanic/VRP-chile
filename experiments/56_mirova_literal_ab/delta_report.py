"""56_mirova_literal_ab/delta_report.py — A/B MIROVA literal vs legacy (S27).

Criterio de aceptación (docs/superpowers/plans/2026-04-28-mirova-literal-puro.md):
  - Recall agregado vs MIROVA NRT cae < 10 pp (de ~0.81 a >=0.71).
  - FPs lejanos vrp>1MW caen >=40% global.
  - Ratio mediano VRP global <=30x (hoy 57x).

Si las 3 PASS -> mergear flags a `mirova_equivalent.yaml`.
Si NO PASS -> persistir hallazgo, NO mergear.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from experiments.forense_h17_replicable import (  # noqa: E402
    _parse_dt_csv, _parse_dt_record, sensor_match,
)

PROFILES = ["_mirova_literal", "_mirova_legacy"]
VOLCANOES = ["Lascar", "Lastarria", "Tupungatito", "Villarrica"]
START = datetime(2026, 4, 12, tzinfo=timezone.utc)
END = datetime(2026, 4, 25, 23, 59, 59, tzinfo=timezone.utc)
TOL = timedelta(minutes=60)
CSV_PATH = (
    ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot"
    / "registro_vrp_consolidado.csv"
)
OUT = Path(__file__).parent / "DELTA_REPORT.md"


def _vol_csv_name(v: str) -> str:
    return {
        "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
        "PlanchonPeteroa": "Planchon-Peteroa",
        "NevadosDeChillan": "Nevados de Chillan",
    }.get(v, v)


def metrics_for(profile: str, volcano: str) -> dict | None:
    """Recall/FP/ratio para 1 volcán bajo 1 profile en la ventana 14d."""
    p = ROOT / "data" / profile / f"{volcano}.json"
    if not p.exists():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    records = raw["records"] if isinstance(raw, dict) else raw

    df = pd.read_csv(CSV_PATH)
    df = df[
        (df.Volcan == _vol_csv_name(volcano))
        & (df.Tipo_Registro == "ALERTA_TERMICA")
    ].copy()
    df["dt"] = df.Fecha_Satelite_UTC.apply(_parse_dt_csv)
    refs = df[(df.dt >= START) & (df.dt <= END)]

    tp, fn = 0, 0
    matched = set()
    ratios = []
    for _, ref in refs.iterrows():
        ref_dt = ref["dt"]
        ref_sensor = ref["Sensor"]
        ref_vrp = ref["VRP_MW"]
        found = False
        for rec in records:
            try:
                rec_dt = _parse_dt_record(rec["datetime_utc"])
            except Exception:
                continue
            if rec_dt < START or rec_dt > END:
                continue
            if abs((rec_dt - ref_dt).total_seconds()) > TOL.total_seconds():
                continue
            if not sensor_match(ref_sensor, rec["sensor"]):
                continue
            if rec.get("vrp_mw", 0) > 0 and rec.get("distance_class") == "summit":
                tp += 1
                matched.add(id(rec))
                if ref_vrp > 0:
                    ratios.append(rec["vrp_mw"] / ref_vrp)
                found = True
                break
        if not found:
            fn += 1

    fp_far_high = sum(
        1
        for r in records
        if r.get("vrp_mw", 0) > 1
        and r.get("distance_class") == "far"
        and id(r) not in matched
        and r.get("datetime_utc")
    )

    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    rmed = sorted(ratios)[len(ratios) // 2] if ratios else float("nan")
    return {
        "tp": tp,
        "fn": fn,
        "fp_far_high": fp_far_high,
        "recall": recall,
        "ratio_med": rmed,
        "n_refs": len(refs),
        "ratios": ratios,
    }


def _safe(v, fmt):
    """Render NaN/None gracefully."""
    if v is None:
        return "—"
    try:
        if isinstance(v, float) and (v != v):  # NaN
            return "—"
    except Exception:
        return str(v)
    return fmt.format(v)


def main() -> None:
    rows = {p: {v: metrics_for(p, v) for v in VOLCANOES} for p in PROFILES}

    lines = ["# A/B MIROVA literal puro — Delta Report (S27)", ""]
    lines.append(f"Ventana: {START.date()} → {END.date()} (14d).")
    lines.append("")
    lines.append(
        "| Volcán | Refs | TP lit/leg | FN lit/leg | FP_far lit/leg "
        "| Recall lit/leg | Ratio med lit/leg |"
    )
    lines.append("|---|---:|---|---|---|---|---|")

    agg = {p: {"tp": 0, "fn": 0, "fp_far_high": 0, "ratios": []} for p in PROFILES}
    for v in VOLCANOES:
        lit = rows[PROFILES[0]][v]
        leg = rows[PROFILES[1]][v]
        if lit is None or leg is None:
            lines.append(f"| {v} | — | — | — | — | — | — |")
            continue
        n_refs = lit["n_refs"]
        lines.append(
            f"| {v} | {n_refs} | "
            f"{lit['tp']}/{leg['tp']} | "
            f"{lit['fn']}/{leg['fn']} | "
            f"{lit['fp_far_high']}/{leg['fp_far_high']} | "
            f"{_safe(lit['recall'], '{:.2f}')}/{_safe(leg['recall'], '{:.2f}')} | "
            f"{_safe(lit['ratio_med'], '{:.2f}')}/{_safe(leg['ratio_med'], '{:.2f}')} |"
        )
        for k in ["tp", "fn", "fp_far_high"]:
            agg[PROFILES[0]][k] += lit[k]
            agg[PROFILES[1]][k] += leg[k]
        agg[PROFILES[0]]["ratios"].extend(lit["ratios"])
        agg[PROFILES[1]]["ratios"].extend(leg["ratios"])

    def _agg_recall(a):
        d = a["tp"] + a["fn"]
        return a["tp"] / d if d else 0.0

    rec_lit = _agg_recall(agg[PROFILES[0]])
    rec_leg = _agg_recall(agg[PROFILES[1]])
    rats_lit = sorted(agg[PROFILES[0]]["ratios"])
    rats_leg = sorted(agg[PROFILES[1]]["ratios"])
    rmed_lit = rats_lit[len(rats_lit) // 2] if rats_lit else 0.0
    rmed_leg = rats_leg[len(rats_leg) // 2] if rats_leg else 0.0

    lines.append("")
    lines.append("## Agregado")
    lines.append("")
    lines.append("| Métrica | MIROVA Literal | Legacy (parches) | Δ |")
    lines.append("|---|---:|---:|---:|")
    lines.append(
        f"| TP | {agg[PROFILES[0]]['tp']} | {agg[PROFILES[1]]['tp']} | "
        f"{agg[PROFILES[0]]['tp']-agg[PROFILES[1]]['tp']:+d} |"
    )
    lines.append(
        f"| FN | {agg[PROFILES[0]]['fn']} | {agg[PROFILES[1]]['fn']} | "
        f"{agg[PROFILES[0]]['fn']-agg[PROFILES[1]]['fn']:+d} |"
    )
    lines.append(
        f"| FP_far(>1MW) | {agg[PROFILES[0]]['fp_far_high']} | "
        f"{agg[PROFILES[1]]['fp_far_high']} | "
        f"{agg[PROFILES[0]]['fp_far_high']-agg[PROFILES[1]]['fp_far_high']:+d} |"
    )
    lines.append(f"| Recall | {rec_lit:.3f} | {rec_leg:.3f} | {rec_lit-rec_leg:+.3f} |")
    lines.append(
        f"| Ratio mediano | {rmed_lit:.2f} | {rmed_leg:.2f} | {rmed_lit-rmed_leg:+.2f} |"
    )
    lines.append("")

    delta_recall_pp = (rec_lit - rec_leg) * 100
    fp_drop = (
        (agg[PROFILES[1]]["fp_far_high"] - agg[PROFILES[0]]["fp_far_high"])
        / agg[PROFILES[1]]["fp_far_high"]
        if agg[PROFILES[1]]["fp_far_high"]
        else 0.0
    )

    crit1 = delta_recall_pp >= -10
    crit2 = fp_drop >= 0.40
    crit3 = rmed_lit <= 30

    lines.append("## Veredicto")
    lines.append("")
    lines.append(
        f"- {'PASS' if crit1 else 'FAIL'} Recall cae < 10 pp -> Δ = {delta_recall_pp:+.1f} pp."
    )
    lines.append(
        f"- {'PASS' if crit2 else 'FAIL'} FP_far cae ≥ 40% -> caída = {fp_drop*100:+.1f}%."
    )
    lines.append(
        f"- {'PASS' if crit3 else 'FAIL'} Ratio mediano ≤ 30× -> ratio literal = {rmed_lit:.1f}×."
    )
    lines.append("")
    if crit1 and crit2 and crit3:
        lines.append("**APROBADO** -> mergear flags a `mirova_equivalent.yaml`.")
    else:
        lines.append("**NO APROBADO** -> persistir hallazgo, NO mergear.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Delta report en {OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
