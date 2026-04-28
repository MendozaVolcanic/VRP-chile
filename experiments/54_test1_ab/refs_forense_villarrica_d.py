"""S26 D — validación final Test 1 Villarrica vs 6 ALERTAs MIROVA.

Lee data/mirova_equivalent/Villarrica.json (refrescada por workflow
reproc-villarrica-test1-refs.yml con Test 1 activo + fix VRP-clip).
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

TOL = timedelta(minutes=60)
OUT = Path(__file__).parent / "VILLARRICA_TEST1_D_FORENSE.md"


def main():
    csv = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
    df = pd.read_csv(csv)
    refs = df[(df.Volcan == "Villarrica") & (df.Tipo_Registro == "ALERTA_TERMICA")].copy()
    refs["dt"] = refs.Fecha_Satelite_UTC.apply(_parse_dt_csv)
    refs = refs.sort_values("dt")

    p = ROOT / "data" / "mirova_equivalent" / "Villarrica.json"
    recs = json.loads(p.read_text(encoding="utf-8"))["records"]

    lines = [
        "# S26 D final — Test 1 Villarrica vs 6 ALERTAs MIROVA",
        "",
        "Profile: `mirova_equivalent_villarrica_test1` (Test 1 activo + fix VRP-clip).",
        "Workflow: `reproc-villarrica-test1-refs.yml` 5 ventanas refs MIROVA.",
        "",
        "| Ref MIROVA | VRP MIROVA | Records VIIRS375 | Test1 disparó | Hit summit | VRP nuestro |",
        "|---|---:|---:|---:|---|---:|",
    ]

    n_caught = 0
    n_test1_fired = 0

    for _, ref in refs.iterrows():
        ref_dt = ref["dt"]
        ref_vrp = ref["VRP_MW"]
        v375 = []
        for r in recs:
            try:
                rec_dt = _parse_dt_record(r["datetime_utc"])
            except Exception:
                continue
            if abs((rec_dt - ref_dt).total_seconds()) > TOL.total_seconds():
                continue
            if not sensor_match("VIIRS375", r["sensor"]):
                continue
            v375.append(r)
        n_records = len(v375)
        n_t1 = sum(1 for r in v375 if r.get("triggered_test1"))
        summit_hit = any(r.get("distance_class") == "summit"
                         and r.get("vrp_mw", 0) > 0 for r in v375)
        if summit_hit:
            n_caught += 1
        if n_t1 > 0:
            n_test1_fired += 1
        best = max(v375, key=lambda r: r.get("vrp_mw", 0) or 0) if v375 else {}
        our_vrp = best.get("vrp_mw", 0)
        check = "✓" if summit_hit else "✗"
        lines.append(
            f"| {ref_dt.strftime('%Y-%m-%d %H:%M')} | {ref_vrp:.3f} | "
            f"{n_records} | {n_t1}/{n_records} | {check} | {our_vrp:.3f} |"
        )

    lines.append("")
    n_refs = len(refs)
    recall = n_caught / n_refs if n_refs else 0
    lines.append(f"## Resumen")
    lines.append("")
    lines.append(f"- Refs MIROVA: {n_refs}")
    lines.append(f"- Refs con summit-class hit (vrp_mw>0): **{n_caught}/{n_refs}** (recall {recall:.2f})")
    lines.append(f"- Refs con Test 1 disparando: **{n_test1_fired}/{n_refs}**")
    lines.append("")
    lines.append("Pre-D (sin Test 1): recall summit Villarrica era 0/6.")
    lines.append("")
    if recall >= 0.67:
        lines.append("**RESULTADO: ✓ APROBADO** → mantener profile dedicado Villarrica + Test 1.")
    elif recall > 0:
        lines.append(f"**RESULTADO: parcial** ({recall:.0%}) → algún beneficio pero <67%.")
    else:
        lines.append("**RESULTADO: ✗ NO APROBADO** → Test 1 en pipeline no captura.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Forense escrito en {OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
