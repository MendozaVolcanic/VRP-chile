"""33_p31_delta_report.py — Delta pre-P3 vs post-P3.2 vs post-P3.1.

Compara 3 estados:
  - pre-P3   : experiments/27_crossmatch_results.json
  - post-P3.2: experiments/27_crossmatch_post_p32.json  (del overnight)
  - post-P3.1: experiments/27_crossmatch_post_p31.json  (generado por
               stage 4 del daytime_p31 wrapper)

Veredicto criterios P3.1:
  - Chaiten precision >= 0.40 desde 0.0 (scene filter cortaria FPs)
  - FPs globales caen >=30%
  - Lascar ratio mediano en [1.10, 1.30] (canary sin regresion)
  - Lastarria ratio mediano < 3.0 (cumplir el objetivo P3.2 original
    con P3.1 complementario)
"""

import json
import sys
from pathlib import Path
from statistics import median


ROOT = Path(__file__).parent.parent
PRE = ROOT / "experiments" / "27_crossmatch_results.json"
P32 = ROOT / "experiments" / "27_crossmatch_post_p32.json"
P31 = ROOT / "experiments" / "27_crossmatch_post_p31.json"
OUT = ROOT / "experiments" / "33_p31_delta_report.md"


def _med(lst):
    xs = [m["ratio"] for m in lst if m.get("ratio")]
    return median(xs) if xs else None


def vol_metrics(d):
    tp, fn, fp = len(d["tp"]), len(d["fn"]), len(d["fp"])
    rec = tp / (tp + fn) if (tp + fn) else 0
    prec = tp / (tp + fp) if (tp + fp) else 0
    f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
    rm = _med(d["tp"]) or 0
    return tp, fn, fp, rec, prec, f1, rm


def global_metrics(state):
    if state is None:
        return None
    TP = sum(len(v["tp"]) for v in state.values())
    FN = sum(len(v["fn"]) for v in state.values())
    FP = sum(len(v["fp"]) for v in state.values())
    ratios = [m["ratio"] for v in state.values()
              for m in v["tp"] if m.get("ratio")]
    rec = TP / (TP + FN) if (TP + FN) else 0
    prec = TP / (TP + FP) if (TP + FP) else 0
    f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
    rm = median(ratios) if ratios else 0
    return {"TP": TP, "FN": FN, "FP": FP, "rec": rec, "prec": prec,
            "f1": f1, "rm": rm}


def main():
    pre = json.load(open(PRE, "r", encoding="utf-8"))
    p32 = json.load(open(P32, "r", encoding="utf-8")) if P32.exists() else None
    p31 = json.load(open(P31, "r", encoding="utf-8")) if P31.exists() else None

    lines = []
    lines.append("# P3.1 — Delta Report (pre / P3.2 / P3.1)")
    lines.append("")

    states = [("pre-P3", pre), ("post-P3.2", p32), ("post-P3.1", p31)]
    globs = [(n, global_metrics(s)) for n, s in states]

    lines.append("## Global")
    lines.append("")
    lines.append("| Estado | TP | FN | FP | Recall | Precision | F1 | R_med |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name, g in globs:
        if g:
            lines.append(f"| {name} | {g['TP']} | {g['FN']} | {g['FP']} | "
                         f"{g['rec']:.2f} | {g['prec']:.2f} | {g['f1']:.2f} | "
                         f"{g['rm']:.2f} |")
        else:
            lines.append(f"| {name} | (no existe) | - | - | - | - | - | - |")
    lines.append("")

    # Por volcan en 3 estados
    lines.append("## Por volcan (TP / Ratio / Recall / Precision)")
    lines.append("")
    lines.append("| Volcan | Metric | pre | P3.2 | P3.1 |")
    lines.append("|---|---|---|---|---|")
    all_vols = set(pre.keys())
    if p32: all_vols |= set(p32.keys())
    if p31: all_vols |= set(p31.keys())
    for v in sorted(all_vols):
        a = pre.get(v)
        b = p32.get(v) if p32 else None
        c = p31.get(v) if p31 else None

        def met(d, i):
            if d is None: return "-"
            m = vol_metrics(d)
            return ["tp","fn","fp","rec","prec","f1","rm"][i], m[i]

        ma = vol_metrics(a) if a else [0]*7
        mb = vol_metrics(b) if b else None
        mc = vol_metrics(c) if c else None

        def fmt(x, spec=".2f"):
            return f"{x:{spec}}" if x is not None else "-"

        lines.append(f"| {v} | TP    | {ma[0]} | "
                     f"{mb[0] if mb else '-'} | {mc[0] if mc else '-'} |")
        lines.append(f"| {v} | Ratio | {ma[6]:.2f} | "
                     f"{fmt(mb[6] if mb else None)} | "
                     f"{fmt(mc[6] if mc else None)} |")
        lines.append(f"| {v} | Rec   | {ma[3]:.2f} | "
                     f"{fmt(mb[3] if mb else None)} | "
                     f"{fmt(mc[3] if mc else None)} |")
        lines.append(f"| {v} | Prec  | {ma[4]:.2f} | "
                     f"{fmt(mb[4] if mb else None)} | "
                     f"{fmt(mc[4] if mc else None)} |")

    lines.append("")

    # Veredicto
    lines.append("## Veredicto criterios P3.1")
    lines.append("")
    if p31:
        g_pre = global_metrics(pre)
        g_p31 = global_metrics(p31)
        chaiten_prec = vol_metrics(p31.get("Chaiten", {"tp":[],"fn":[],"fp":[]}))[4]
        lascar_rm = vol_metrics(p31.get("Lascar", {"tp":[],"fn":[],"fp":[]}))[6]
        lastarria_rm = vol_metrics(p31.get("Lastarria", {"tp":[],"fn":[],"fp":[]}))[6]
        fp_drop = (g_pre["FP"] - g_p31["FP"]) / max(g_pre["FP"], 1)

        criteria = [
            (f"Chaiten precision >= 0.40 (post {chaiten_prec:.2f})",
             chaiten_prec >= 0.40),
            (f"FPs globales caen >=30% (drop {100*fp_drop:.0f}%)",
             fp_drop >= 0.30),
            (f"Lascar ratio en [1.10, 1.30] (post {lascar_rm:.2f})",
             1.10 <= lascar_rm <= 1.30),
            (f"Lastarria ratio < 3.0 (post {lastarria_rm:.2f})",
             lastarria_rm < 3.0),
        ]
        passed = all(c[1] for c in criteria)
        lines.append(f"**P3.1 {'APROBADO' if passed else 'NO APROBADO'}**")
        lines.append("")
        for msg, ok in criteria:
            lines.append(f"- {'[OK]' if ok else '[FAIL]'} {msg}")
    else:
        lines.append("**Pendiente** (post-P3.1 json no existe aun).")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Delta report escrito en {OUT}")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
