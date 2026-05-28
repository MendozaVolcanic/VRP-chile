"""
Sanity intra-radio VIIRS — espejo de S82 Fase 1b MODIS.

Pregunta a responder con datos: ¿Las ALERTAs VIIRS MIROVA caen mayoritariamente
dentro de `inner_radius_km` (caso favorable a gate F-S81-B análogo) o están
distribuidas hasta `radius_km` (caso desfavorable — gate mataría TPs reales)?

Universo MIROVA = CONS (latest_consolidado.csv) ∪ OCR (registro_vrp_ocr.csv).

Lección A11: OCR es COMPLEMENTO de CONS, no validación. Juntos = todo lo que
MIROVA publica.

Por (volcán × sensor):
  - N ALERTAs (CONS, OCR, total)
  - p50, p95, max de Distancia_km
  - inner_radius_km del volcán (volcanoes.yaml)
  - N dentro_inner / N fuera_inner / % fuera
  - Veredicto: GATE_OK | GATE_MATA_TPs | INSUFICIENTE_DATA

Output: docs/F_S81_B_SANITY_VIIRS.md + tabla JSON.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "_s84_viirs_sanity"
DOC_OUT = ROOT / "docs" / "F_S81_B_SANITY_VIIRS.md"

# Tier A (orden canónico)
TIER_A = [
    "PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue",
    "NevadosDeChillan", "Llaima", "Chaiten", "PlanchonPeteroa",
    "Lastarria", "Isluga", "Tupungatito",
]

# Mapping nombre canónico (volcanoes.yaml) → variantes en CSV
VOL_VARIANTS = {
    "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle", "PuyehueCordonCaulle"],
    "Villarrica": ["Villarrica"],
    "Lascar": ["Lascar"],
    "Copahue": ["Copahue"],
    "NevadosDeChillan": ["Nevados de Chillan", "NevadosDeChillan"],
    "Llaima": ["Llaima"],
    "Chaiten": ["Chaiten"],
    "PlanchonPeteroa": ["PlanchonPeteroa", "Planchon-Peteroa", "Peteroa"],
    "Lastarria": ["Lastarria"],
    "Isluga": ["Isluga"],
    "Tupungatito": ["Tupungatito"],
}

SENSORS = ["VIIRS375", "VIIRS", "MODIS"]  # incluir MODIS como referencia comparativa
SENSOR_DISPLAY = {"VIIRS375": "VIIRS-I 375m", "VIIRS": "VIIRS-M 750m", "MODIS": "MODIS 1km"}

# Umbrales de veredicto
MIN_N_FOR_VERDICT = 5
PCT_OUTSIDE_GATE_OK = 0.20   # <=20% afuera → gate aplica sin perder TPs significativos
PCT_OUTSIDE_GATE_MATA = 0.40 # >40% afuera → gate mata TPs reales, NO aplicar


def load_inner_radius() -> dict[str, float]:
    y = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
    return {v["name"]: float(v.get("inner_radius_km", 5)) for v in y["volcanoes"]}


def vol_canonical(name_in_csv: str) -> str | None:
    n = (name_in_csv or "").strip()
    for canon, variants in VOL_VARIANTS.items():
        if n in variants:
            return canon
    return None


def load_alertas(csv_path: Path, source_label: str) -> list[dict[str, Any]]:
    """Carga ALERTAs de un CSV. Tipo_Registro debe contener 'ALERTA'."""
    out = []
    if not csv_path.exists():
        print(f"[WARN] CSV no encontrado: {csv_path}")
        return out
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tipo = (row.get("Tipo_Registro") or "").strip().upper()
            if "ALERTA" not in tipo:
                continue
            vol_canon = vol_canonical(row.get("Volcan", ""))
            if vol_canon is None:
                continue
            sensor = (row.get("Sensor") or "").strip()
            if sensor not in SENSORS:
                continue
            try:
                dist = float(row.get("Distancia_km") or 0)
            except ValueError:
                continue
            try:
                vrp = float(row.get("VRP_MW") or 0)
            except ValueError:
                vrp = 0.0
            out.append({
                "vol": vol_canon,
                "sensor": sensor,
                "dist_km": dist,
                "vrp_mw": vrp,
                "fecha": (row.get("Fecha_Satelite_UTC") or "").strip(),
                "source": source_label,
                "tipo": tipo,
                "clasif": (row.get("Clasificacion Mirova") or "").strip(),
            })
    return out


def verdict(n: int, pct_outside: float) -> str:
    if n < MIN_N_FOR_VERDICT:
        return "INSUFICIENTE_DATA"
    if pct_outside <= PCT_OUTSIDE_GATE_OK:
        return "GATE_OK"
    if pct_outside >= PCT_OUTSIDE_GATE_MATA:
        return "GATE_MATA_TPs"
    return "GATE_AMBIGUO"


def main() -> int:
    inner_radius = load_inner_radius()
    print("[sanity VIIRS] cargando CONS + OCR...")

    cons = load_alertas(ROOT / "latest_consolidado.csv", "CONS")
    ocr = load_alertas(
        ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
        "OCR",
    )
    print(f"  CONS: {len(cons)} ALERTAs (cualquier sensor, Tier A)")
    print(f"  OCR : {len(ocr)} ALERTAs")
    all_alertas = cons + ocr
    print(f"  TOTAL universo: {len(all_alertas)}")

    # Agrupar por (vol, sensor)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for a in all_alertas:
        groups[(a["vol"], a["sensor"])].append(a)

    rows = []
    for vol in TIER_A:
        inner = inner_radius.get(vol, 5.0)
        for sensor in SENSORS:
            items = groups.get((vol, sensor), [])
            n = len(items)
            n_cons = sum(1 for x in items if x["source"] == "CONS")
            n_ocr = sum(1 for x in items if x["source"] == "OCR")
            if n == 0:
                rows.append({
                    "vol": vol, "sensor": sensor, "inner_km": inner,
                    "n_total": 0, "n_cons": 0, "n_ocr": 0,
                    "p50": None, "p95": None, "max": None,
                    "n_inside": 0, "n_outside": 0, "pct_outside": None,
                    "verdict": "INSUFICIENTE_DATA",
                })
                continue
            dists = sorted(x["dist_km"] for x in items)
            p50 = median(dists)
            # p95 manual (sin numpy)
            idx_p95 = max(0, min(len(dists) - 1, int(round(0.95 * (len(dists) - 1)))))
            p95 = dists[idx_p95]
            mx = dists[-1]
            n_inside = sum(1 for d in dists if d <= inner)
            n_outside = n - n_inside
            pct_out = n_outside / n
            rows.append({
                "vol": vol, "sensor": sensor, "inner_km": inner,
                "n_total": n, "n_cons": n_cons, "n_ocr": n_ocr,
                "p50": round(p50, 2), "p95": round(p95, 2), "max": round(mx, 2),
                "n_inside": n_inside, "n_outside": n_outside,
                "pct_outside": round(pct_out, 3),
                "verdict": verdict(n, pct_out),
            })

    # Write JSON
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sanity_viirs.json").write_text(
        json.dumps({"rows": rows, "n_cons": len(cons), "n_ocr": len(ocr)}, indent=2),
        encoding="utf-8",
    )

    # Markdown
    md = ["# Sanity F-S81-B intra-radio VIIRS\n\n"]
    md.append("**Pregunta**: ¿Las ALERTAs VIIRS MIROVA caen dentro de `inner_radius_km`")
    md.append(" (gate intra-radio análogo a F-S81-A aplicable) o están dispersas hasta")
    md.append(" `radius_km=25` (gate mataría TPs reales)?\n\n")
    md.append("**Universo MIROVA** = CONS (latest_consolidado.csv) ∪ OCR (registro_vrp_ocr.csv)\n\n")
    md.append(f"**Totales**: {len(cons)} ALERTAs CONS + {len(ocr)} ALERTAs OCR")
    md.append(f" = **{len(all_alertas)} ALERTAs Tier A**\n\n")

    md.append("## Umbrales de veredicto\n\n")
    md.append(f"- `GATE_OK`: ≤{int(PCT_OUTSIDE_GATE_OK*100)}% ALERTAs fuera de inner_radius (gate aplica sin perder TPs).\n")
    md.append(f"- `GATE_MATA_TPs`: ≥{int(PCT_OUTSIDE_GATE_MATA*100)}% afuera (gate destruiría TPs reales — NO aplicar).\n")
    md.append(f"- `GATE_AMBIGUO`: entre {int(PCT_OUTSIDE_GATE_OK*100)}-{int(PCT_OUTSIDE_GATE_MATA*100)}% afuera.\n")
    md.append(f"- `INSUFICIENTE_DATA`: <{MIN_N_FOR_VERDICT} ALERTAs.\n\n")

    # Una tabla por sensor
    for sensor in SENSORS:
        md.append(f"\n## {SENSOR_DISPLAY[sensor]} (`{sensor}`)\n\n")
        md.append("| Volcán | inner_km | N tot | CONS | OCR | p50 | p95 | max | dentro | fuera | %fuera | Veredicto |\n")
        md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
        for r in rows:
            if r["sensor"] != sensor:
                continue
            pct_str = f"{r['pct_outside']*100:.1f}%" if r["pct_outside"] is not None else "—"
            md.append(
                f"| {r['vol']} | {r['inner_km']} | {r['n_total']} | "
                f"{r['n_cons']} | {r['n_ocr']} | {r['p50'] or '—'} | "
                f"{r['p95'] or '—'} | {r['max'] or '—'} | "
                f"{r['n_inside']} | {r['n_outside']} | {pct_str} | "
                f"**{r['verdict']}** |\n"
            )
        # Agregado del sensor
        rows_s = [r for r in rows if r["sensor"] == sensor and r["n_total"] > 0]
        n_total = sum(r["n_total"] for r in rows_s)
        n_in = sum(r["n_inside"] for r in rows_s)
        n_out = sum(r["n_outside"] for r in rows_s)
        pct_agg = n_out / n_total if n_total else 0
        md.append(
            f"| **AGREGADO** | — | **{n_total}** | — | — | — | — | — | "
            f"**{n_in}** | **{n_out}** | **{pct_agg*100:.1f}%** | "
            f"**{verdict(n_total, pct_agg)}** |\n"
        )

    # Síntesis por volcán
    md.append("\n## Síntesis por volcán (VIIRS combinado: 375 + 750)\n\n")
    md.append("| Volcán | inner_km | N VIIRS tot | %fuera VIIRS | Veredicto VIIRS combinado |\n")
    md.append("|---|---:|---:|---:|---|\n")
    for vol in TIER_A:
        viirs_rows = [r for r in rows if r["vol"] == vol and r["sensor"] in {"VIIRS375", "VIIRS"} and r["n_total"] > 0]
        if not viirs_rows:
            md.append(f"| {vol} | {inner_radius.get(vol, '?')} | 0 | — | INSUFICIENTE_DATA |\n")
            continue
        n_total = sum(r["n_total"] for r in viirs_rows)
        n_out = sum(r["n_outside"] for r in viirs_rows)
        pct = n_out / n_total
        md.append(
            f"| {vol} | {inner_radius.get(vol, '?')} | {n_total} | {pct*100:.1f}% | **{verdict(n_total, pct)}** |\n"
        )

    # Conclusión
    md.append("\n## Conclusión y decisión\n\n")
    md.append("(Leer tablas y completar a mano según veredicto agregado.)\n\n")
    md.append("- Si VIIRS agregado = `GATE_OK` → próxima sesión: diseñar F-S81-B gate Path D VIIRS intra-radio análogo.\n")
    md.append("- Si VIIRS agregado = `GATE_MATA_TPs` → descartar gate intra-radio para VIIRS; el problema D9 (Path D dNTI cirrus) requiere otra solución (co-validación BT, cap atm gate, etc.).\n")
    md.append("- Casos per-volcán pueden invertir: e.g. Lascar puede ser `GATE_OK` mientras PCC sea `GATE_MATA_TPs` (lacolito extenso, inner=20).\n")

    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUT.write_text("".join(md), encoding="utf-8")
    print(f"[sanity VIIRS] OK -> {DOC_OUT}")
    print(f"[sanity VIIRS] OK -> {OUT_DIR/'sanity_viirs.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
