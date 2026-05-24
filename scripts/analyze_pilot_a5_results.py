"""F31 A5 piloto — analizador post-corrida.

Cruza los resultados del reproc piloto VRPTIR Aveni 2025 GRL
(`data/experimental_lowT/<Volcano>.json`) contra el ground truth físico
disponible para los 3 volcanes candidatos:

- **Planchón-Peteroa**: Aguilera et al. 2021 (Frontiers in Earth Sci,
  doi:10.3389/feart.2021.722056). Qvolc lago cratérico: **7-59 MW**.
  Ground truth ESTRICTO (medición de campo + Landsat TIR). Es el anchor
  más fuerte del piloto.

- **Lastarria**: sin ground truth físico publicado. Fumarólica crónica
  histórica ~0.1-2 MW (Coppola 2024 cap Springer §estimado). Banda
  ancha pero centrada en sub-MW.

- **Copahue**: sin ground truth físico publicado durante ventana piloto.
  Lago cratérico Caviahue puede estar activo o quieto según fase.
  Banda esperada 1-30 MW si está activo, ~0 si pasivo.

**Decisión post-piloto (per docs/F31_AVENI_VRPTIR_PLAN_S74.md)**:

- Si mediana `vrptir_aveni_mw` PP cae en 7-59 MW → **candidato a flip
  operacional S78** (con A45 obligatorio + brainstorming gate).
- Si cae factor ≥5× fuera (>295 MW o <1.4 MW) → **queda en experimental**
  y se documenta el desfasaje.
- Si cae entre los dos rangos → más análisis (depende de la varianza,
  cobertura noches, etc.).

Uso:
    python scripts/analyze_pilot_a5_results.py
        [--data-dir data/experimental_lowT]
        [--volcanoes PlanchonPeteroa Lastarria Copahue]
        [--output experiments/145_pilot_a5_analysis/]

Output:
- `<output>/summary.json` — métricas por volcán.
- `<output>/report.md` — resumen humano-legible (compara vs Aguilera 7-59 MW).
- stdout: tabla resumen.

Refs:
- PR #158 (integración A2, campos vrptir_aveni_*)
- PR #165 (script piloto reproc)
- pipeline/profiles/experimental_lowT.yaml
- docs/F31_AGUILERA_2021_PETEROA.md (ground truth PP)
- docs/F31_AVENI_VRPTIR_PLAN_S74.md
- docs/F31_AVENI_GRL_2025_EXTRACT.md
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Ground truth bandas (refs en docstring del módulo).
GROUND_TRUTH = {
    "PlanchonPeteroa": {
        "source": "Aguilera 2021 Frontiers, doi:10.3389/feart.2021.722056",
        "qvolc_min_mw": 7.0,
        "qvolc_max_mw": 59.0,
        "confidence": "alta — medición campo + Landsat TIR, multi-año",
    },
    "Lastarria": {
        "source": "Coppola 2024 cap Springer (estimado fumarólica crónica)",
        "qvolc_min_mw": 0.1,
        "qvolc_max_mw": 2.0,
        "confidence": "media — banda derivada de literatura volcanológica, sin medición campo",
    },
    "Copahue": {
        "source": "no hay ground truth físico publicado para ventana piloto",
        "qvolc_min_mw": 1.0,
        "qvolc_max_mw": 30.0,
        "confidence": "baja — banda especulativa según fase de actividad",
    },
}


def _load_volcano_records(data_dir: Path, volcano: str) -> list[dict]:
    """Lee data/experimental_lowT/<Volcano>.json y devuelve los records."""
    path = data_dir / f"{volcano}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARN: no pude parsear {path}: {e}", file=sys.stderr)
        return []
    return data.get("records", [])


def _summarize_records(records: list[dict], volcano: str) -> dict[str, Any]:
    """Computa estadísticos sobre vrptir_aveni_mw para un volcán."""
    valid = [
        r for r in records
        if r.get("vrptir_aveni_mw") is not None
        and r.get("vrptir_aveni_n_pixels", 0) > 0
    ]
    n_records = len(records)
    n_valid = len(valid)

    summary = {
        "volcano": volcano,
        "n_records_total": n_records,
        "n_records_vrptir_valid": n_valid,
    }

    if n_valid == 0:
        summary["status"] = "sin_data"
        summary["caveat"] = (
            "Ningún record en la ventana tiene vrptir_aveni_mw > 0 + "
            "n_pixels > 0. Posibles causas: (a) ENABLE_VRPTIR_AVENI no estaba "
            "activo, (b) no hubo pixels en rango 300-600K, (c) reproc no se "
            "ejecutó. Verificar pipeline/profiles/experimental_lowT.yaml."
        )
        return summary

    values = [r["vrptir_aveni_mw"] for r in valid]
    values.sort()

    summary.update({
        "vrptir_aveni_mw_min": values[0],
        "vrptir_aveni_mw_p25": values[len(values) // 4] if len(values) >= 4 else values[0],
        "vrptir_aveni_mw_median": statistics.median(values),
        "vrptir_aveni_mw_p75": values[3 * len(values) // 4] if len(values) >= 4 else values[-1],
        "vrptir_aveni_mw_max": values[-1],
        "vrptir_aveni_mw_mean": statistics.mean(values),
        "vrptir_aveni_mw_stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    })

    # Verdict contra ground truth.
    gt = GROUND_TRUTH.get(volcano)
    if gt is None:
        summary["verdict"] = "sin_ground_truth"
        return summary

    median = summary["vrptir_aveni_mw_median"]
    gt_min, gt_max = gt["qvolc_min_mw"], gt["qvolc_max_mw"]
    gt_mid = (gt_min + gt_max) / 2

    if gt_min <= median <= gt_max:
        verdict = "DENTRO_BANDA"
        comment = (
            f"Mediana {median:.2f} MW cae dentro de la banda {gt['source']} "
            f"({gt_min}-{gt_max} MW). Candidato a flip operacional S78."
        )
    elif median > 5 * gt_max:
        verdict = "FUERA_ALTO"
        comment = (
            f"Mediana {median:.2f} MW supera 5× el techo de banda "
            f"({gt_max} MW). Queda en experimental. Posible artefacto "
            f"Stefan-Boltzmann sobre 4σ-mask (similar a F46 bug)."
        )
    elif median < 0.2 * gt_min:
        verdict = "FUERA_BAJO"
        comment = (
            f"Mediana {median:.2f} MW está 5× por debajo del piso de banda "
            f"({gt_min} MW). Queda en experimental. Posible sub-sensibilidad "
            f"VIIRS I5 o emisividad inadecuada."
        )
    else:
        verdict = "FRONTERIZO"
        comment = (
            f"Mediana {median:.2f} MW está cerca pero fuera de la banda "
            f"({gt_min}-{gt_max} MW). Análisis adicional necesario "
            f"(varianza, cobertura, sensor)."
        )

    summary["verdict"] = verdict
    summary["verdict_comment"] = comment
    summary["ground_truth_band_mw"] = [gt_min, gt_max]
    summary["ground_truth_source"] = gt["source"]
    summary["ground_truth_confidence"] = gt["confidence"]
    return summary


def _build_report(summaries: list[dict]) -> str:
    """Construye el markdown del reporte humano-legible."""
    lines = []
    lines.append("# F31 A5 piloto — análisis post-corrida\n")
    lines.append(f"Generado: {datetime.now(timezone.utc).isoformat()}\n")
    lines.append(
        "Cruza `vrptir_aveni_mw` por volcán contra ground truth físico publicado.\n"
        "Ground truth ESTRICTO: Aguilera 2021 (PP), bandas literatura para los demás.\n"
    )

    lines.append("## Resumen por volcán\n")
    lines.append("| Volcán | N records | N válidos | Mediana MW | Banda GT | Verdict |")
    lines.append("|---|---|---|---|---|---|")
    for s in summaries:
        gt_band = ""
        if "ground_truth_band_mw" in s:
            gt_band = f"{s['ground_truth_band_mw'][0]}-{s['ground_truth_band_mw'][1]} MW"
        median = s.get("vrptir_aveni_mw_median", "—")
        if isinstance(median, float):
            median = f"{median:.2f}"
        lines.append(
            f"| {s['volcano']} | {s['n_records_total']} | "
            f"{s['n_records_vrptir_valid']} | {median} | {gt_band} | "
            f"{s.get('verdict', s.get('status', '?'))} |"
        )

    lines.append("\n## Detalle por volcán\n")
    for s in summaries:
        lines.append(f"### {s['volcano']}\n")
        if s.get("status") == "sin_data":
            lines.append(f"**Estado**: sin data válida.\n\n{s.get('caveat', '')}\n")
            continue
        lines.append(f"- Records totales: {s['n_records_total']}")
        lines.append(f"- Records VRPTIR válidos (n_pixels > 0): {s['n_records_vrptir_valid']}")
        lines.append(f"- Distribución vrptir_aveni_mw:")
        lines.append(f"  - min: {s['vrptir_aveni_mw_min']:.3f}")
        lines.append(f"  - p25: {s['vrptir_aveni_mw_p25']:.3f}")
        lines.append(f"  - **mediana: {s['vrptir_aveni_mw_median']:.3f}**")
        lines.append(f"  - p75: {s['vrptir_aveni_mw_p75']:.3f}")
        lines.append(f"  - max: {s['vrptir_aveni_mw_max']:.3f}")
        lines.append(f"  - mean ± stdev: {s['vrptir_aveni_mw_mean']:.3f} ± {s['vrptir_aveni_mw_stdev']:.3f}")
        if "ground_truth_source" in s:
            lines.append(f"\n**Ground truth**:")
            lines.append(f"- Fuente: {s['ground_truth_source']}")
            lines.append(f"- Banda: {s['ground_truth_band_mw'][0]}-{s['ground_truth_band_mw'][1]} MW")
            lines.append(f"- Confianza: {s['ground_truth_confidence']}")
            lines.append(f"\n**Verdict**: `{s['verdict']}`")
            lines.append(f"\n{s['verdict_comment']}\n")

    lines.append("\n## Recomendación final\n")
    pp = next((s for s in summaries if s["volcano"] == "PlanchonPeteroa"), None)
    if pp is None or pp.get("status") == "sin_data":
        lines.append(
            "PP no tiene data válida — no se puede tomar decisión sobre flip operacional. "
            "Verificar que el piloto haya corrido con `enable_vrptir_aveni: true`.\n"
        )
    elif pp.get("verdict") == "DENTRO_BANDA":
        lines.append(
            "PP DENTRO de la banda Aguilera 2021 (7-59 MW). **Candidato a flip operacional S78**.\n"
            "- Pre-requisitos antes del flip: A45 (tag defensivo) + superpowers-brainstorming gate + R2 pixel-level validation contra MIROVA web.\n"
            "- Si los 3 candidatos pasan, considerar mover `enable_vrptir_aveni: true` de experimental_lowT.yaml a mirova_equivalent.yaml.\n"
        )
    elif pp.get("verdict") == "FUERA_ALTO":
        lines.append(
            "PP FUERA banda Aguilera por arriba. Queda en experimental.\n"
            "- Investigar si comparte patrón con bug F46 (Stefan-Boltzmann sobre 4σ-mask sin gate consistencia).\n"
            "- Verificar emisividad asumida (Aveni 2025 ε=1; revisar si lago cratérico requiere ajuste).\n"
        )
    elif pp.get("verdict") == "FUERA_BAJO":
        lines.append(
            "PP FUERA banda Aguilera por debajo. Queda en experimental.\n"
            "- Posible sub-sensibilidad VIIRS I5 al ground truth Landsat de Aguilera.\n"
            "- Considerar piloto con M-band 750m o MODIS B31 como complementarios.\n"
        )
    else:
        lines.append(
            "PP FRONTERIZO. Análisis adicional necesario antes de decisión.\n"
            "- Revisar varianza (¿median engaña? Usar p25-p75).\n"
            "- Revisar cobertura noches (¿pocas pasadas inflan ruido?).\n"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--data-dir", type=Path,
                   default=Path("data/experimental_lowT"),
                   help="Directorio con JSONs del piloto (default data/experimental_lowT/).")
    p.add_argument("--volcanoes", nargs="+",
                   default=list(GROUND_TRUTH.keys()),
                   help="Volcanes a analizar.")
    p.add_argument("--output", type=Path,
                   default=Path("experiments/145_pilot_a5_analysis"),
                   help="Directorio output.")
    args = p.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    summaries = []
    for vol in args.volcanoes:
        records = _load_volcano_records(args.data_dir, vol)
        s = _summarize_records(records, vol)
        summaries.append(s)

    # JSON
    (args.output / "summary.json").write_text(
        json.dumps(summaries, indent=2, default=str),
        encoding="utf-8",
    )
    # Markdown
    (args.output / "report.md").write_text(
        _build_report(summaries),
        encoding="utf-8",
    )

    # Stdout
    print()
    print("=== F31 A5 análisis post-piloto ===")
    print(f"Data dir : {args.data_dir}")
    print(f"Output   : {args.output}")
    print()
    print(f"{'Volcán':<22} {'N rec':>7} {'N valid':>9} {'Mediana MW':>12}  Verdict")
    for s in summaries:
        median = s.get("vrptir_aveni_mw_median", "—")
        if isinstance(median, float):
            median = f"{median:.3f}"
        verdict = s.get("verdict", s.get("status", "?"))
        print(f"{s['volcano']:<22} {s['n_records_total']:>7} "
              f"{s['n_records_vrptir_valid']:>9} {median:>12}  {verdict}")
    print()
    print(f"Reporte completo: {args.output / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
