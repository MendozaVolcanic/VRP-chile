"""54_test1_ab/refs_forense.py — Validación Test 1 vs 6 ALERTAs MIROVA Villarrica.

Para cada ref MIROVA Villarrica VIIRS 375m:
1. Buscar record correspondiente en _test1_enabled y _test1_disabled.
2. Comparar: ¿Test 1 disparó? ¿Pipeline integrado captura?
3. Tabla resumen + veredicto recall.

Respuesta esperada (POC offline ya validó 6/6):
- _test1_enabled: 6/6 deberían tener triggered_test1=True y n_anomalous_pixels>0.
- _test1_disabled: 0/6 deberían tener detección (replicar comportamiento
  pre-Test 1 que vimos en data/mirova_equivalent/Villarrica.json).
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
OUT = Path(__file__).parent / "REFS_FORENSE.md"


def find_records(records, ref_dt, ref_sensor):
    """Returns all records within TOL min of ref_dt matching sensor."""
    matches = []
    for rec in records:
        try:
            rec_dt = _parse_dt_record(rec["datetime_utc"])
        except Exception:
            continue
        if abs((rec_dt - ref_dt).total_seconds()) > TOL.total_seconds():
            continue
        if not sensor_match(ref_sensor, rec["sensor"]):
            continue
        matches.append(rec)
    return matches


def main():
    csv = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
    df = pd.read_csv(csv)
    refs = df[(df.Volcan == "Villarrica") & (df.Tipo_Registro == "ALERTA_TERMICA")].copy()
    refs["dt"] = refs.Fecha_Satelite_UTC.apply(_parse_dt_csv)
    refs = refs.sort_values("dt")

    en_path = ROOT / "data" / "_test1_enabled" / "Villarrica.json"
    dis_path = ROOT / "data" / "_test1_disabled" / "Villarrica.json"
    en_recs = json.loads(en_path.read_text(encoding="utf-8"))["records"]
    dis_recs = json.loads(dis_path.read_text(encoding="utf-8"))["records"]

    lines = [
        "# Validación Test 1 vs 6 ALERTAs MIROVA Villarrica (S25 final)",
        "",
        "Para cada ref MIROVA, buscamos los records VIIRS 375m de los 3 satélites",
        "(SNPP/NOAA20/NOAA21) en ±60 min en cada profile A/B.",
        "",
        "| Ref MIROVA | VRP MIROVA | Records (en/dis) | Test 1 disparó | n_anom dis | n_anom en | Veredicto |",
        "|---|---:|---|---|---:|---:|---|",
    ]

    n_refs = len(refs)
    n_caught_en = 0  # at least one record per ref dispara test1 en enabled
    n_caught_dis = 0  # at least one record per ref tiene n_anom>0 en disabled

    detail_rows = []
    for _, ref in refs.iterrows():
        ref_dt = ref["dt"]
        ref_vrp = ref["VRP_MW"]
        en_matches = find_records(en_recs, ref_dt, "VIIRS375")
        dis_matches = find_records(dis_recs, ref_dt, "VIIRS375")

        en_t1_count = sum(1 for r in en_matches if r.get("triggered_test1"))
        en_anom_count = sum(1 for r in en_matches if r.get("n_anomalous_pixels", 0) > 0)
        dis_anom_count = sum(1 for r in dis_matches if r.get("n_anomalous_pixels", 0) > 0)

        if en_t1_count > 0:
            n_caught_en += 1
        if dis_anom_count > 0:
            n_caught_dis += 1

        verdict = ""
        if en_t1_count > 0 and dis_anom_count == 0:
            verdict = "✓ Test 1 captura (paths actuales NO)"
        elif en_t1_count > 0 and dis_anom_count > 0:
            verdict = "= Ambos detectan"
        elif en_t1_count == 0 and dis_anom_count == 0:
            verdict = "✗ NINGUNO detecta (sin granule en ventana?)"
        else:
            verdict = "? raro"

        lines.append(
            f"| {ref_dt.strftime('%Y-%m-%d %H:%M')} | {ref_vrp:.3f} | "
            f"{len(en_matches)}/{len(dis_matches)} | "
            f"{en_t1_count}/{len(en_matches)} | "
            f"{dis_anom_count} | {en_anom_count} | {verdict} |"
        )

        # Detail per record
        for r in en_matches:
            detail_rows.append({
                "ref_dt": str(ref_dt),
                "ref_vrp": ref_vrp,
                "rec_dt": r["datetime_utc"],
                "sensor": r["sensor"],
                "test1_triggered": r.get("triggered_test1", False),
                "test1_k_obs": r.get("test1_k_observed", 0),
                "n_test1_pixels": r.get("n_test1_pixels", 0),
                "n_anomalous_pixels": r.get("n_anomalous_pixels", 0),
                "n_bt_path": r.get("n_bt_path", 0),
                "n_dnti_ctx_path": r.get("n_dnti_ctx_path", 0),
                "vrp_mw": r.get("vrp_mw", 0),
                "distance_class": r.get("distance_class"),
            })

    lines.append("")
    lines.append(f"## Recall summary")
    lines.append("")
    lines.append(f"- Refs MIROVA con ≥1 granule disparando Test 1 (enabled): **{n_caught_en}/{n_refs}**")
    lines.append(f"- Refs MIROVA con ≥1 granule detectado por paths actuales (disabled): {n_caught_dis}/{n_refs}")
    lines.append("")
    lines.append("## Detalle por record (enabled profile)")
    lines.append("")
    lines.append("| Ref | Sensor | Triggered Test 1 | K obs | n_test1 | n_anom | n_bt | n_dnti | VRP | class |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    for d in detail_rows:
        t1 = "✓" if d["test1_triggered"] else "✗"
        lines.append(
            f"| {d['ref_dt'][:16]} | {d['sensor']} | {t1} | "
            f"{d['test1_k_obs']:.1f} | {d['n_test1_pixels']} | {d['n_anomalous_pixels']} | "
            f"{d['n_bt_path']} | {d['n_dnti_ctx_path']} | {d['vrp_mw']:.4f} | {d['distance_class'] or '-'} |"
        )

    lines.append("")
    lines.append("## Veredicto Test 1 (clon-MIROVA recall)")
    lines.append("")
    if n_refs > 0:
        recall_en = n_caught_en / n_refs
        recall_dis = n_caught_dis / n_refs
        lines.append(f"**Recall Villarrica enabled = {recall_en:.2f} ({n_caught_en}/{n_refs})**")
        lines.append(f"Recall Villarrica disabled (control) = {recall_dis:.2f} ({n_caught_dis}/{n_refs})")
        lines.append("")
        if recall_en >= 0.5 and recall_en > recall_dis:
            lines.append("**INTEGRAR Test 1 a `mirova_equivalent`** — recall sube significativamente sin")
            lines.append("inflar FPs en controles (validado en A/B 14d previo).")
        elif recall_en > 0:
            lines.append(f"Test 1 captura {n_caught_en} refs nuevas pero queda corto del 50%. **EVALUAR**:")
            lines.append("  - Bajar k_sigma de 3.0 a 2.5 (más permisivo).")
            lines.append("  - Refinar inner_ring_km / roi_km.")
            lines.append("  - Verificar que el cálculo en pipeline coincide con el POC offline.")
        else:
            lines.append("**Test 1 no captura ninguna ref en pipeline integrado**. Investigar:")
            lines.append("  - ¿Granules disponibles en _test1_enabled para las refs?")
            lines.append("  - Diferencia entre POC offline y pipeline (efferdescente / cloud_mask?).")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Forense escrito en {OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
