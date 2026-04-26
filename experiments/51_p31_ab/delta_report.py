"""51_p31_ab/delta_report.py — A/B P3.1 dual-ROI delta report (S24).

Compara forenses generados por `forense_h17_replicable.py` para los profiles
`_p3_1_enabled` (treatment, dual-ROI on) vs `_p3_1_disabled` (control, single-ROI)
sobre la ventana 14d 2026-04-12 a 2026-04-25 × 4 Tier A.

Asume que existen los 8 forense JSONs en este directorio:
  forense_<profile>_<volcano>.json

Genera un reporte markdown con:
  - Tabla por volcán: TP/FN/FP, recall, precision, F1, ratio mediano (enabled vs disabled).
  - Tabla agregada (suma de los 4 volcanes).
  - Veredicto basado en criterios del plan_s15_p3_1_dual_roi.md:
    * Chaiten precision >= 0.40 (enabled).
    * FP totales bajan >= 30% (enabled vs disabled).
    * Recall global no cae más de 5 pp (enabled vs disabled).
    * Lascar ratio mediano permanece en [1.10, 1.30].
"""
import json
import sys
from pathlib import Path
from statistics import median

ROOT = Path(__file__).parent
PROFILES = ["_p3_1_enabled", "_p3_1_disabled"]
VOLCANOES = ["Lascar", "Lastarria", "Tupungatito", "Chaiten"]
OUT = ROOT / "DELTA_REPORT.md"


def load(profile, volcano):
    p = ROOT / f"forense_{profile}_{volcano}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def metrics(d):
    """Extrae TP/FN/FP/recall/precision/F1/ratio_mediano del forense."""
    if d is None:
        return None
    counts = d.get("counts", {})
    tp = counts.get("tp", 0)
    fn = counts.get("fn", 0)
    fp = counts.get("fp", 0)
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0.0
    # Ratio mediano sobre TPs si forense lo expone
    tp_records = d.get("tp_records", []) or d.get("tp", [])
    ratios = [m.get("ratio") for m in tp_records if isinstance(m, dict) and m.get("ratio")]
    rm = median(ratios) if ratios else None
    return {"tp": tp, "fn": fn, "fp": fp, "recall": rec,
            "precision": prec, "f1": f1, "ratio_med": rm}


def main():
    lines = ["# A/B P3.1 dual-ROI — Delta Report (S24)",
             "",
             "Generado por `experiments/51_p31_ab/delta_report.py`.",
             "",
             "Compara `_p3_1_enabled` (dual-ROI on) vs `_p3_1_disabled` (control)",
             "sobre 14d 2026-04-12 a 2026-04-25, 4 Tier A.",
             "",
             "## Por volcán",
             "",
             "| Volcán | TP en/dis | FN en/dis | FP en/dis | Recall en/dis | Precision en/dis | Ratio med en/dis |",
             "|---|---|---|---|---|---|---|"]

    agg_en = {"tp": 0, "fn": 0, "fp": 0}
    agg_dis = {"tp": 0, "fn": 0, "fp": 0}

    for vol in VOLCANOES:
        en = metrics(load("_p3_1_enabled", vol))
        dis = metrics(load("_p3_1_disabled", vol))

        def fmt(en_v, dis_v, fmt_str="{:.2f}"):
            if en is None and dis is None:
                return "-/-"
            e = fmt_str.format(en_v) if en is not None and en_v is not None else "-"
            d = fmt_str.format(dis_v) if dis is not None and dis_v is not None else "-"
            return f"{e}/{d}"

        row = [
            vol,
            fmt(en["tp"] if en else None, dis["tp"] if dis else None, "{:d}"),
            fmt(en["fn"] if en else None, dis["fn"] if dis else None, "{:d}"),
            fmt(en["fp"] if en else None, dis["fp"] if dis else None, "{:d}"),
            fmt(en["recall"] if en else None, dis["recall"] if dis else None),
            fmt(en["precision"] if en else None, dis["precision"] if dis else None),
            fmt(en["ratio_med"] if en else None, dis["ratio_med"] if dis else None),
        ]
        lines.append("| " + " | ".join(row) + " |")

        if en:
            for k in agg_en: agg_en[k] += en[k]
        if dis:
            for k in agg_dis: agg_dis[k] += dis[k]

    lines.append("")
    lines.append("## Agregado (4 volcanes)")
    lines.append("")

    def agg_metrics(a):
        rec = a["tp"] / (a["tp"] + a["fn"]) if (a["tp"] + a["fn"]) else 0
        prec = a["tp"] / (a["tp"] + a["fp"]) if (a["tp"] + a["fp"]) else 0
        f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
        return rec, prec, f1

    rec_e, pr_e, f1_e = agg_metrics(agg_en)
    rec_d, pr_d, f1_d = agg_metrics(agg_dis)

    lines += [
        f"| Métrica | Enabled (dual-ROI on) | Disabled (control) | Δ |",
        f"|---|---:|---:|---:|",
        f"| TP | {agg_en['tp']} | {agg_dis['tp']} | {agg_en['tp']-agg_dis['tp']:+d} |",
        f"| FN | {agg_en['fn']} | {agg_dis['fn']} | {agg_en['fn']-agg_dis['fn']:+d} |",
        f"| FP | {agg_en['fp']} | {agg_dis['fp']} | {agg_en['fp']-agg_dis['fp']:+d} |",
        f"| Recall | {rec_e:.3f} | {rec_d:.3f} | {rec_e-rec_d:+.3f} |",
        f"| Precision | {pr_e:.3f} | {pr_d:.3f} | {pr_e-pr_d:+.3f} |",
        f"| F1 | {f1_e:.3f} | {f1_d:.3f} | {f1_e-f1_d:+.3f} |",
        "",
    ]

    # Veredicto
    lines.append("## Veredicto criterios P3.1 (plan_s15_p3_1_dual_roi.md)")
    lines.append("")

    chaiten_en = metrics(load("_p3_1_enabled", "Chaiten"))
    lascar_en = metrics(load("_p3_1_enabled", "Lascar"))

    crit = []
    if chaiten_en:
        c1 = chaiten_en["precision"] >= 0.40
        crit.append((f"Chaitén precision (enabled) ≥ 0.40 → {chaiten_en['precision']:.2f}", c1))
    if agg_dis["fp"] > 0:
        fp_drop = (agg_dis["fp"] - agg_en["fp"]) / agg_dis["fp"]
        c2 = fp_drop >= 0.30
        crit.append((f"FP totales caen ≥ 30% (enabled vs disabled) → {fp_drop*100:.1f}%", c2))
    c3 = (rec_d - rec_e) <= 0.05
    crit.append((f"Recall no cae más de 5 pp → Δ {(rec_e-rec_d)*100:+.1f} pp", c3))
    if lascar_en and lascar_en["ratio_med"] is not None:
        c4 = 1.10 <= lascar_en["ratio_med"] <= 1.30
        crit.append((f"Lascar ratio mediano (enabled) en [1.10, 1.30] → {lascar_en['ratio_med']:.2f}", c4))

    if crit:
        passed = all(c[1] for c in crit)
        lines.append(f"**P3.1 {'APROBADO' if passed else 'NO APROBADO'}**")
        lines.append("")
        for msg, ok in crit:
            mark = "[OK]" if ok else "[FAIL]"
            lines.append(f"- {mark} {msg}")
    else:
        lines.append("**Sin datos para evaluar criterios** (forense JSONs faltantes).")

    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Delta report escrito en {OUT}")
    print()
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
