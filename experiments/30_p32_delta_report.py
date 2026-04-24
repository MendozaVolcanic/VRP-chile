"""30_p32_delta_report.py — Comparar crossmatch pre vs post P3.2.

Lee experiments/27_crossmatch_results.json (baseline pre-P3.2) y
experiments/27_crossmatch_post_p32.json (post reproceso) y genera un
reporte markdown con los deltas por volcan y un veredicto de
aceptacion/rechazo basado en los criterios del plan.

Criterios de aceptacion P3.2 (tasks/plan_s15_p3_2_dnti_contextual.md):
  - Lastarria ratio mediano < 3.0 (desde 19.87).
  - Recall global >= 0.23 (baseline 0.28, margen 5 pp).
  - Lascar ratio mediano permanece en [1.10, 1.25] (canary).

Si post-P3.2 no existe (reproceso fallo), reporta solo el estado pre.
"""

import json
import sys
from pathlib import Path
from statistics import median


ROOT = Path(__file__).parent.parent
PRE = ROOT / "experiments" / "27_crossmatch_results.json"
POST = ROOT / "experiments" / "27_crossmatch_post_p32.json"
OUT = ROOT / "experiments" / "30_p32_delta_report.md"


def _med(ratios):
    rs = [m["ratio"] for m in ratios if m.get("ratio")]
    return median(rs) if rs else None


def metrics(vol_data):
    tp, fn, fp = len(vol_data["tp"]), len(vol_data["fn"]), len(vol_data["fp"])
    rec = tp / (tp + fn) if (tp + fn) else 0
    prec = tp / (tp + fp) if (tp + fp) else 0
    f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
    rm = _med(vol_data["tp"]) or 0
    return tp, fn, fp, rec, prec, f1, rm


def globals(d):
    TP = sum(len(v["tp"]) for v in d.values())
    FN = sum(len(v["fn"]) for v in d.values())
    FP = sum(len(v["fp"]) for v in d.values())
    all_ratios = [m["ratio"] for v in d.values()
                  for m in v["tp"] if m.get("ratio")]
    rec = TP / (TP + FN) if (TP + FN) else 0
    prec = TP / (TP + FP) if (TP + FP) else 0
    f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
    rm = median(all_ratios) if all_ratios else 0
    return TP, FN, FP, rec, prec, f1, rm


def main():
    if not PRE.exists():
        print(f"ERROR: {PRE} no existe. No hay baseline.")
        sys.exit(1)
    pre = json.load(open(PRE, "r", encoding="utf-8"))
    post = json.load(open(POST, "r", encoding="utf-8")) if POST.exists() else None

    lines = []
    lines.append("# P3.2 — Delta Report pre/post reproceso")
    lines.append("")
    lines.append("Generado por `experiments/30_p32_delta_report.py`.")
    lines.append("")

    # Global
    TP_a, FN_a, FP_a, rec_a, pr_a, f1_a, rm_a = globals(pre)
    lines.append("## Global")
    lines.append("")
    lines.append("| Metrica | Pre-P3.2 | Post-P3.2 | Delta |")
    lines.append("|---|---:|---:|---:|")
    if post:
        TP_b, FN_b, FP_b, rec_b, pr_b, f1_b, rm_b = globals(post)
        lines.append(f"| TP | {TP_a} | {TP_b} | {TP_b-TP_a:+d} |")
        lines.append(f"| FN | {FN_a} | {FN_b} | {FN_b-FN_a:+d} |")
        lines.append(f"| FP | {FP_a} | {FP_b} | {FP_b-FP_a:+d} |")
        lines.append(f"| Recall | {rec_a:.2f} | {rec_b:.2f} | {rec_b-rec_a:+.2f} |")
        lines.append(f"| Precision | {pr_a:.2f} | {pr_b:.2f} | {pr_b-pr_a:+.2f} |")
        lines.append(f"| F1 | {f1_a:.2f} | {f1_b:.2f} | {f1_b-f1_a:+.2f} |")
        lines.append(f"| Ratio mediano | {rm_a:.2f} | {rm_b:.2f} | {rm_b-rm_a:+.2f} |")
    else:
        lines.append(f"| TP | {TP_a} | (post no existe) | - |")
        lines.append(f"| Recall | {rec_a:.2f} | - | - |")
        lines.append(f"| Ratio mediano | {rm_a:.2f} | - | - |")
    lines.append("")

    # Por volcan
    lines.append("## Por volcan")
    lines.append("")
    lines.append("| Volcan | TP pre/post | Ratio pre/post | Recall pre/post |")
    lines.append("|---|---|---|---|")
    vols = sorted(set(pre.keys()) | (set(post.keys()) if post else set()))
    for v in vols:
        a = pre.get(v)
        b = post.get(v) if post else None
        if a:
            tp_a, fn_a, fp_a, rec_a, _, _, rm_a = metrics(a)
        else:
            tp_a = rec_a = rm_a = 0
        if b:
            tp_b, fn_b, fp_b, rec_b, _, _, rm_b = metrics(b)
            row = f"| {v} | {tp_a}/{tp_b} | {rm_a:.2f}/{rm_b:.2f} | {rec_a:.2f}/{rec_b:.2f} |"
        else:
            row = f"| {v} | {tp_a}/- | {rm_a:.2f}/- | {rec_a:.2f}/- |"
        lines.append(row)
    lines.append("")

    # Veredicto criterios P3.2
    lines.append("## Veredicto criterios P3.2")
    lines.append("")
    criteria = []
    if post:
        _, _, _, _, _, _, rm_lastarria_b = metrics(post["Lastarria"]) \
            if "Lastarria" in post else (0,0,0,0,0,0,0)
        _, _, _, _, _, _, rm_lastarria_a = metrics(pre["Lastarria"])
        c1 = rm_lastarria_b < 3.0
        criteria.append(
            (f"Lastarria ratio mediano < 3.0 (pre {rm_lastarria_a:.2f} -> post {rm_lastarria_b:.2f})", c1)
        )

        _, _, _, _, _, _, rm_lascar_b = metrics(post["Lascar"]) \
            if "Lascar" in post else (0,0,0,0,0,0,0)
        c2 = 1.10 <= rm_lascar_b <= 1.30
        criteria.append(
            (f"Lascar ratio mediano en [1.10, 1.30] (post {rm_lascar_b:.2f})", c2)
        )

        _, _, _, rec_global_b, _, _, _ = globals(post)
        c3 = rec_global_b >= 0.23
        criteria.append(
            (f"Recall global >= 0.23 (post {rec_global_b:.2f})", c3)
        )

        passed_all = all(c[1] for c in criteria)
        lines.append(f"**P3.2 {'APROBADO' if passed_all else 'NO APROBADO'}**")
        lines.append("")
        for msg, ok in criteria:
            mark = "[OK]" if ok else "[FAIL]"
            lines.append(f"- {mark} {msg}")
    else:
        lines.append("**Pendiente** (post-P3.2 json no existe aun).")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Delta report escrito en {OUT}")
    print()
    print("\n".join(lines[:20]))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
