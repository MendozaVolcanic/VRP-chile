"""55_dual_roi_bt_ab/delta_report.py — A/B dual-ROI BT delta report (S26 T7).

Mide la contribución del fix arquitectural dual-ROI N·σ en eruption-path BT
(Coppola 2016a Tabla 1: 5σ summit, 10σ scene). Compara:
  - _dual_roi_bt_enabled (treatment, dual-ROI BT on)
  - _dual_roi_bt_disabled (control, mirror operacional 3σ uniforme)

Criterio de aceptación (plan 2026-04-27):
  ✓ Recall agregado vs MIROVA NRT cae < 5 pp.
  ✓ FPs lejanos vrp>1MW caen ≥40%.
  ✓ Ratio mediano VRP global ≤30× (hoy 57×).

Si las 3 PASS → integrar a mirova_equivalent. Si NO → no mergear.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from experiments.forense_h17_replicable import _parse_dt_csv, _parse_dt_record, sensor_match

PROFILES = ["_dual_roi_bt_enabled", "_dual_roi_bt_disabled"]
VOLCANOES = ["Villarrica", "Lascar", "Lastarria", "Tupungatito"]
START = datetime(2026, 4, 12, tzinfo=timezone.utc)
END = datetime(2026, 4, 25, 23, 59, 59, tzinfo=timezone.utc)
TOL = timedelta(minutes=60)
CSV_PATH = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OUT = Path(__file__).parent / "DELTA_REPORT.md"


def _vol_csv_name(v):
    return {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
            "PlanchonPeteroa": "Planchon-Peteroa",
            "NevadosDeChillan": "Nevados de Chillan"}.get(v, v)


def metrics_for(profile, volcano):
    """Compute TP/FN/FP_far/recall/ratio_mediano vs MIROVA NRT en ventana."""
    p = ROOT / "data" / profile / f"{volcano}.json"
    if not p.exists():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    records = raw["records"] if isinstance(raw, dict) else raw

    df = pd.read_csv(CSV_PATH)
    df = df[(df.Volcan == _vol_csv_name(volcano)) & (df.Tipo_Registro == "ALERTA_TERMICA")].copy()
    df["dt"] = df.Fecha_Satelite_UTC.apply(_parse_dt_csv)
    refs = df[(df.dt >= START) & (df.dt <= END)]

    tp = 0; fn = 0
    matched_ids = set()
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
                matched_ids.add(id(rec))
                if ref_vrp > 0:
                    ratios.append(rec["vrp_mw"] / ref_vrp)
                found = True
                break
        if not found:
            fn += 1

    fp_far_high = sum(1 for r in records
                      if (START <= _parse_dt_record(r.get("datetime_utc", "")) <= END if r.get("datetime_utc") else False)
                      and r.get("vrp_mw", 0) > 1
                      and r.get("distance_class") == "far"
                      and id(r) not in matched_ids)

    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    rmed = sorted(ratios)[len(ratios) // 2] if ratios else float("nan")
    return {"tp": tp, "fn": fn, "fp_far_high": fp_far_high, "recall": recall,
            "ratio_med": rmed, "n_refs": len(refs), "ratios": ratios}


def main():
    rows = {p: {v: metrics_for(p, v) for v in VOLCANOES} for p in PROFILES}

    lines = ["# A/B dual-ROI BT — Delta Report (S26)", ""]
    lines.append(f"Ventana: {START.date()} → {END.date()} (14d). Tolerancia ±60 min.")
    lines.append("")
    lines.append("## Por volcán")
    lines.append("")
    lines.append("| Volcán | Refs | TP en/dis | FN en/dis | FP_far en/dis | Recall en/dis | Ratio med en/dis |")
    lines.append("|---|---:|---|---|---|---|---|")

    agg_en = {"tp": 0, "fn": 0, "fp_far_high": 0, "ratios": []}
    agg_dis = {"tp": 0, "fn": 0, "fp_far_high": 0, "ratios": []}

    for v in VOLCANOES:
        en = rows[PROFILES[0]][v]
        dis = rows[PROFILES[1]][v]
        if en is None or dis is None:
            lines.append(f"| {v} | — | — | — | — | — | — |")
            continue
        n_refs = en["n_refs"]
        lines.append(
            f"| {v} | {n_refs} | "
            f"{en['tp']}/{dis['tp']} | "
            f"{en['fn']}/{dis['fn']} | "
            f"{en['fp_far_high']}/{dis['fp_far_high']} | "
            f"{en['recall']:.2f}/{dis['recall']:.2f} | "
            f"{en['ratio_med']:.2f}/{dis['ratio_med']:.2f} |"
        )
        for k in ["tp", "fn", "fp_far_high"]:
            agg_en[k] += en[k]
            agg_dis[k] += dis[k]
        agg_en["ratios"].extend(en["ratios"])
        agg_dis["ratios"].extend(dis["ratios"])

    rec_en = agg_en["tp"] / (agg_en["tp"] + agg_en["fn"]) if (agg_en["tp"] + agg_en["fn"]) else 0
    rec_dis = agg_dis["tp"] / (agg_dis["tp"] + agg_dis["fn"]) if (agg_dis["tp"] + agg_dis["fn"]) else 0
    rmed_en = sorted(agg_en["ratios"])[len(agg_en["ratios"]) // 2] if agg_en["ratios"] else 0
    rmed_dis = sorted(agg_dis["ratios"])[len(agg_dis["ratios"]) // 2] if agg_dis["ratios"] else 0

    lines.append("")
    lines.append("## Agregado")
    lines.append("")
    lines.append("| Métrica | Enabled (dual-ROI BT) | Disabled (control 3σ) | Δ |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| TP | {agg_en['tp']} | {agg_dis['tp']} | {agg_en['tp']-agg_dis['tp']:+d} |")
    lines.append(f"| FN | {agg_en['fn']} | {agg_dis['fn']} | {agg_en['fn']-agg_dis['fn']:+d} |")
    lines.append(f"| FP_far (vrp>1MW sin match) | {agg_en['fp_far_high']} | {agg_dis['fp_far_high']} | {agg_en['fp_far_high']-agg_dis['fp_far_high']:+d} |")
    lines.append(f"| Recall | {rec_en:.3f} | {rec_dis:.3f} | {rec_en-rec_dis:+.3f} |")
    lines.append(f"| Ratio mediano VRP | {rmed_en:.2f} | {rmed_dis:.2f} | {rmed_en-rmed_dis:+.2f} |")

    # Veredicto vs criterios de aceptación
    delta_recall_pp = (rec_en - rec_dis) * 100
    fp_drop = (agg_dis["fp_far_high"] - agg_en["fp_far_high"]) / agg_dis["fp_far_high"] if agg_dis["fp_far_high"] else 0

    crit1 = delta_recall_pp >= -5  # cae < 5 pp
    crit2 = fp_drop >= 0.40
    crit3 = rmed_en <= 30

    lines.append("")
    lines.append("## Veredicto criterios plan 2026-04-27")
    lines.append("")
    lines.append(f"- {'✓' if crit1 else '✗'} **Recall agregado cae < 5 pp** → Δ = {delta_recall_pp:+.1f} pp.")
    lines.append(f"- {'✓' if crit2 else '✗'} **FP_far cae ≥ 40%** → caída = {fp_drop*100:+.1f}%.")
    lines.append(f"- {'✓' if crit3 else '✗'} **Ratio mediano ≤ 30×** → ratio enabled = {rmed_en:.1f}×.")
    lines.append("")
    if crit1 and crit2 and crit3:
        lines.append("**RESULTADO: APROBADO** → integrar `enable_dual_roi_bt: true` a `mirova_equivalent.yaml`.")
    else:
        lines.append("**RESULTADO: NO APROBADO** → no mergear. Persistir hallazgo y revisar plan.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Delta report escrito en {OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
