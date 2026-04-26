"""S21 experiment #40 — Análisis de `diag_sigma_bg_k` por clase forense.

Hipótesis D6: en T4 (records con n_anomalous>0 todos far, MIROVA detecta cráter
y nosotros no), el `std_bg` sobre el anillo bbox global está inflado por
terreno heterogéneo (glaciar Tupungatito) → el threshold vent capeado a 3K no
dispara la fumarola real (ΔT ~1.5-2K).

Approach: usar `diag_sigma_bg_k` ya persistido en cada record JSON (es el std_bg
sobre anillo bbox 50×50 km). Agrupar por clase forense (TP/T1/T2b/T3/T4) y
comparar distribuciones. Si T4 tiene mediana ≫ TP → confirma D6 sin necesidad
de descargar granules raw.

Nota: este experimento mide el std_bg GLOBAL ya guardado. NO mide std_bg local
(ROI1 5×5 km centrado en cráter) — eso requiere granules raw y queda para
Task 8b si es necesario tras este análisis.

Uso CLI:
    python experiments/analyze_diag_sigma_by_class.py \\
        --forense-json experiments/38_forense_Tupungatito.json \\
        --output-json experiments/40_sigma_by_class_Tupungatito.json \\
        --output-md experiments/40_sigma_by_class_Tupungatito.md
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np


def extract_sigma_by_class(classifications: list[dict],
                           sensor_filter: str | None = None) -> dict[str, list[float]]:
    """Agrupa diag_sigma_bg_k por clase. Excluye records None (T1) y missing sigma.

    sensor_filter: si se pasa, solo incluye records cuyo sensor START WITH eso.
    Ej: 'MODIS' → MODIS_AQUA + MODIS_TERRA. Útil para apples-to-apples cuando
    VIIRS no guarda sigma (H_S21_8).
    """
    by_class: dict[str, list[float]] = {}
    for c in classifications:
        rec = c.get("rec")
        if rec is None:
            continue
        if sensor_filter and not rec.get("sensor", "").startswith(sensor_filter):
            continue
        sigma = rec.get("diag_sigma_bg_k")
        if sigma is None:
            continue
        by_class.setdefault(c["class"], []).append(float(sigma))
    return by_class


def summarize_distributions(sigmas_by_class: dict[str, list[float]]) -> dict:
    """Devuelve stats {n, mean, median, p25, p75, p95, std} por clase."""
    out = {}
    for cls, vals in sigmas_by_class.items():
        n = len(vals)
        if n == 0:
            out[cls] = {"n": 0, "median": float("nan"),
                        "mean": float("nan"), "p25": float("nan"),
                        "p75": float("nan"), "p95": float("nan"),
                        "std": float("nan")}
            continue
        arr = np.array(vals, dtype=float)
        out[cls] = {
            "n": n,
            "median": float(np.median(arr)),
            "mean": float(np.mean(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p75": float(np.percentile(arr, 75)),
            "p95": float(np.percentile(arr, 95)),
            "std": float(np.std(arr)),
        }
    return out


def extract_extra_diag(classifications: list[dict],
                       fields: tuple[str, ...] = ("diag_eff_threshold_k", "t_bg_k")) -> dict:
    """Idem extract_sigma_by_class pero para múltiples campos de diagnóstico."""
    out: dict[str, dict[str, list[float]]] = {f: {} for f in fields}
    for c in classifications:
        rec = c.get("rec")
        if rec is None:
            continue
        cls = c["class"]
        for f in fields:
            v = rec.get(f)
            if v is not None:
                out[f].setdefault(cls, []).append(float(v))
    return out


def render_md(out: dict, volcano: str) -> str:
    lines = [
        f"# Análisis std_bg por clase forense — {volcano}",
        "",
        "Hipótesis D6: T4 tiene `diag_sigma_bg_k` (std_bg global) significativamente",
        "más alto que TP, lo que infla el threshold vent y no dispara la fumarola.",
        "",
        "## Distribución `diag_sigma_bg_k` (K) por clase",
        "",
        "| Clase | n | median | mean | p25 | p75 | p95 | std |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    sigma_summary = out["sigma_summary"]
    for cls in ("TP", "T4", "T3", "T2b"):
        if cls not in sigma_summary:
            continue
        s = sigma_summary[cls]
        lines.append(
            f"| {cls} | {s['n']} | {s['median']:.3f} | {s['mean']:.3f} | "
            f"{s['p25']:.3f} | {s['p75']:.3f} | {s['p95']:.3f} | {s['std']:.3f} |"
        )
    lines.append("")

    # Diagnóstico H_S21_1 corregido: si TP y T4 tienen sigma similar →
    # std_bg global NO explica el problema. Si T4 ≫ TP → confirma D6.
    if "TP" in sigma_summary and "T4" in sigma_summary:
        ratio = (sigma_summary["T4"]["median"] /
                 sigma_summary["TP"]["median"]) if sigma_summary["TP"]["median"] > 0 else float("nan")
        lines.append("## Diagnóstico D6")
        lines.append("")
        lines.append(f"- Ratio mediano T4/TP de `diag_sigma_bg_k`: **{ratio:.2f}**")
        if ratio > 1.5:
            lines.append("- ⚠️ **CONFIRMA D6**: std_bg global en T4 es marcadamente "
                         "mayor que en TP. El threshold vent capeado en 3K no dispara "
                         "ΔT real ~1.5-2K en escenas T4.")
        elif ratio < 1.2:
            lines.append("- ⚠️ **REFUTA D6**: std_bg global en T4 es similar a TP. "
                         "El problema NO es background inflado — buscar otra causa "
                         "(ej: posición fumarola del experiment 39, o granule MODIS "
                         "vacío H_S21_2).")
        else:
            lines.append(f"- 🤔 Ratio intermedio ({ratio:.2f}). std_bg global "
                         "podría contribuir pero no es el factor dominante.")
    lines.append("")

    # Threshold efectivo
    if "diag_eff_threshold_k" in out["extra_summary"]:
        thr_summary = out["extra_summary"]["diag_eff_threshold_k"]
        lines.append("## `diag_eff_threshold_k` (threshold efectivo aplicado, K)")
        lines.append("")
        lines.append("| Clase | n | median | mean | p95 |")
        lines.append("|---|---:|---:|---:|---:|")
        for cls in ("TP", "T4", "T3", "T2b"):
            if cls in thr_summary:
                s = thr_summary[cls]
                lines.append(
                    f"| {cls} | {s['n']} | {s['median']:.3f} | "
                    f"{s['mean']:.3f} | {s['p95']:.3f} |"
                )
        lines.append("")

    return "\n".join(lines)


def run(forense_json: Path, sensor_filter: str | None = None) -> dict:
    forense = json.loads(forense_json.read_text(encoding="utf-8"))
    classifications = forense["classifications"]

    sigmas = extract_sigma_by_class(classifications, sensor_filter=sensor_filter)
    sigma_summary = summarize_distributions(sigmas)

    extra = extract_extra_diag(classifications)
    extra_summary = {f: summarize_distributions(d) for f, d in extra.items()}

    return {
        "volcano": forense["volcano"],
        "n_refs": forense["n_refs"],
        "sensor_filter": sensor_filter,
        "sigma_summary": sigma_summary,
        "extra_summary": extra_summary,
    }


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forense-json", required=True,
                    help="Output de experiments/forense_h17_replicable.py")
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    ap.add_argument("--sensor-filter", default=None,
                    help="Si se pasa (ej 'MODIS' o 'VIIRS'), filtra records al sensor. "
                         "Importante porque process_viirs.py no guarda diag_sigma_bg_k (H_S21_8)")
    args = ap.parse_args()

    out = run(Path(args.forense_json), sensor_filter=args.sensor_filter)
    Path(args.output_json).write_text(json.dumps(out, indent=2, default=str),
                                       encoding="utf-8")
    Path(args.output_md).write_text(render_md(out, out["volcano"]),
                                     encoding="utf-8")

    sigma = out["sigma_summary"]
    if "TP" in sigma and "T4" in sigma:
        ratio = (sigma["T4"]["median"] / sigma["TP"]["median"]
                 if sigma["TP"]["median"] > 0 else float("nan"))
        print(f"OK · {out['volcano']}: median sigma TP={sigma['TP']['median']:.2f}K "
              f"T4={sigma['T4']['median']:.2f}K  ratio T4/TP={ratio:.2f}")
    else:
        print(f"OK · {out['volcano']}: insuficientes datos para ratio T4/TP")


if __name__ == "__main__":
    _main()
