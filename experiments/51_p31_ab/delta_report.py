"""51_p31_ab/delta_report.py — A/B P3.1 dual-ROI delta report (S24).

Mide la contribución aislada de P3.1 dual-ROI thresholds (Coppola 2016a Tabla 2)
comparando los profiles _p3_1_enabled (dual-ROI on) vs _p3_1_disabled (control).

P3.1 NO afecta detecciones summit (ROI inner). Filtra detecciones SCENE (ROI
fuera de inner_radius) con threshold más estricto. La métrica relevante es
**número de records con detecciones SCENE**, que son típicamente FPs (clusters
lejanos que MIROVA descarta — Lazufre Lastarria, lago Conguillío Llaima, etc.).

Cada record se clasifica por su `distance_class`:
  - summit: detección en ROI inner. Estable entre profiles (no afectado por P3.1).
  - far:    detección en ROI scene. P3.1 dual-ROI debería reducirla.
  - sin detección (vrp_mw=0, n_anomalous=0): no informativo.

Cruzamos opcionalmente contra el CSV MIROVA para dividir los `far` en:
  - far + match MIROVA = TP_far (rare but possible)
  - far + sin match  = FP_far (lo que P3.1 debería matar)

Lectura: data/_p3_1_<state>/<volcano>.json sobre ventana 2026-04-12..04-25.
Consolidado MIROVA: data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv

Salida: experiments/51_p31_ab/DELTA_REPORT.md
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

# Reusa parsers + sensor_match del forense
sys.path.insert(0, str(Path(__file__).parent.parent))
from forense_h17_replicable import _parse_dt_csv, _parse_dt_record, sensor_match  # noqa


ROOT = Path(__file__).parent.parent.parent
PROFILES = ["_p3_1_enabled", "_p3_1_disabled"]
VOLCANOES = ["Lascar", "Lastarria", "Tupungatito", "Chaiten"]
START = datetime(2026, 4, 12, tzinfo=timezone.utc)
END = datetime(2026, 4, 25, 23, 59, 59, tzinfo=timezone.utc)
TOLERANCE = timedelta(minutes=60)
CSV_PATH = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OUT = Path(__file__).parent / "DELTA_REPORT.md"


def load_refs(volcano):
    df = pd.read_csv(CSV_PATH)
    df = df[df["Volcan"] == volcano]
    df = df[df["Tipo_Registro"] == "ALERTA_TERMICA"]
    refs = []
    for _, r in df.iterrows():
        try:
            dt = _parse_dt_csv(r["Fecha_Satelite_UTC"])
        except Exception:
            continue
        if not (START <= dt <= END):
            continue
        refs.append({"dt": dt, "sensor": r["Sensor"], "vrp": r.get("VRP_MW", None)})
    return refs


def has_match(rec_dt, rec_sensor, refs):
    for ref in refs:
        if abs((rec_dt - ref["dt"]).total_seconds()) > TOLERANCE.total_seconds():
            continue
        if sensor_match(ref["sensor"], rec_sensor):
            return True
    return False


def classify(profile, volcano, refs):
    p = ROOT / "data" / profile / f"{volcano}.json"
    if not p.exists():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    records = raw["records"] if isinstance(raw, dict) and "records" in raw else raw
    summit_total = 0
    summit_match = 0
    far_total = 0
    far_match = 0  # TP_far
    far_no_match = 0  # FP_far
    for r in records:
        try:
            dt = _parse_dt_record(r["datetime_utc"])
        except Exception:
            continue
        if not (START <= dt <= END):
            continue
        # Solo records con detección física
        if r.get("vrp_mw", 0) <= 0 and r.get("n_anomalous_pixels", 0) == 0:
            continue
        dist_class = r.get("distance_class", "")
        sensor = r.get("sensor", "")
        m = has_match(dt, sensor, refs)
        if dist_class == "summit":
            summit_total += 1
            if m:
                summit_match += 1
        elif dist_class == "far":
            far_total += 1
            if m:
                far_match += 1
            else:
                far_no_match += 1
    return {
        "summit_total": summit_total,
        "summit_match": summit_match,
        "far_total": far_total,
        "far_match": far_match,
        "far_no_match": far_no_match,
        "n_refs": len(refs),
    }


def main():
    rows_by_vol = {}
    for vol in VOLCANOES:
        refs = load_refs(vol)
        rows_by_vol[vol] = {p: classify(p, vol, refs) for p in PROFILES}

    lines = [
        "# A/B P3.1 dual-ROI — Delta Report (S24)",
        "",
        f"Ventana: {START.date()} → {END.date()} (14d). Tolerancia match ±60 min.",
        "",
        "Cada record con detección física se clasifica por `distance_class`:",
        "- **summit**: ROI inner — P3.1 NO lo afecta (filtra solo SCENE).",
        "- **far**: ROI scene — P3.1 lo reduce con threshold 3.3× más estricto.",
        "  - **far+match**: detectado por nosotros y por MIROVA (señal real lejana, raro).",
        "  - **far−match**: solo nosotros (FP lejano — lo que P3.1 debería matar).",
        "",
        "## Por volcán",
        "",
        "| Volcán | n_refs | summit en/dis | far en/dis | far−match (FP_far) en/dis | Δ FP_far |",
        "|---|---:|---|---|---|---:|",
    ]

    agg = {p: {"summit_total": 0, "far_total": 0, "far_no_match": 0, "far_match": 0} for p in PROFILES}

    for vol in VOLCANOES:
        en = rows_by_vol[vol][PROFILES[0]]
        dis = rows_by_vol[vol][PROFILES[1]]

        def fmt(en_v, dis_v):
            e = "?" if en is None else str(en_v)
            d = "?" if dis is None else str(dis_v)
            return f"{e}/{d}"

        n_refs = (en or dis or {}).get("n_refs", 0)
        delta_fp = "?"
        if en and dis:
            delta_fp = f"{en['far_no_match'] - dis['far_no_match']:+d}"

        row = [
            vol,
            str(n_refs),
            fmt(en["summit_total"] if en else None, dis["summit_total"] if dis else None),
            fmt(en["far_total"] if en else None, dis["far_total"] if dis else None),
            fmt(en["far_no_match"] if en else None, dis["far_no_match"] if dis else None),
            delta_fp,
        ]
        lines.append("| " + " | ".join(row) + " |")

        for p in PROFILES:
            d = rows_by_vol[vol][p]
            if d:
                for k in agg[p]:
                    agg[p][k] += d[k]

    lines.append("")
    lines.append("## Agregado (4 volcanes)")
    lines.append("")
    lines.append(f"| Métrica | Enabled (dual-ROI on) | Disabled (control) | Δ |")
    lines.append(f"|---|---:|---:|---:|")
    for k, label in [
        ("summit_total", "Records summit"),
        ("far_total", "Records far"),
        ("far_match", "TP_far (far+match MIROVA)"),
        ("far_no_match", "FP_far (far sin match)"),
    ]:
        e = agg[PROFILES[0]][k]
        d = agg[PROFILES[1]][k]
        lines.append(f"| {label} | {e} | {d} | {e-d:+d} |")
    lines.append("")

    # Veredicto
    lines.append("## Veredicto P3.1 dual-ROI")
    lines.append("")
    fp_en = agg[PROFILES[0]]["far_no_match"]
    fp_dis = agg[PROFILES[1]]["far_no_match"]
    summit_en = agg[PROFILES[0]]["summit_total"]
    summit_dis = agg[PROFILES[1]]["summit_total"]

    if fp_dis > 0:
        fp_drop = (fp_dis - fp_en) / fp_dis
        lines.append(f"- **FP_far reduction**: {fp_dis} → {fp_en} ({fp_drop*100:+.1f}% vs control).")
    else:
        lines.append(f"- **FP_far reduction**: 0 → 0 (no scene FPs en la ventana — sin señal).")

    if summit_dis == summit_en:
        lines.append(f"- **Summit estable**: {summit_en} = {summit_dis} (P3.1 no toca summit, esperado).")
    else:
        lines.append(f"- **⚠ Summit cambió**: {summit_dis} → {summit_en} (no esperado; revisar implementación).")

    lines.append("")
    lines.append("**Interpretación**:")
    lines.append("- Si Δ FP_far ≪ 0 y summit estable → P3.1 cumple su rol diseñado: filtra ruido scene sin tocar señal summit. **MANTENER**.")
    lines.append("- Si Δ FP_far ≈ 0 → P3.1 no aporta señal en la ventana. **EVALUAR si la ventana es informativa** (más volcanes / más días).")
    lines.append("- Si Δ FP_far > 0 (enabled tiene MÁS FP) → bug. **INVESTIGAR**.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Delta report escrito en {OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
