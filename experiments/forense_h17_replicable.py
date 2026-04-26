"""S21 experiment #38 — Forense replicable de refs MIROVA.

Clasifica TP/T1/T2b/T3/T4 cruzando data/mirova_equivalent/<volcano>.json
contra data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv.

Reproduce sistemáticamente la clasificación narrativa H17 S20 (que era manual).
Filtra Tipo_Registro='ALERTA_TERMICA' (excluye 'ALERTA_TERMICA_OCR' sin
geocodificación → H_S21_6, y excluye 'RUTINA'/'NULO' que son no-detecciones).
NOTA: el CSV individual por volcán (registro_<Volcano>.csv) usa columna
'Origen_Dato'; el consolidado usa 'Tipo_Registro'. Este script usa el
consolidado.

Clases:
- T1   : Ref MIROVA presente, sin record nuestro en ventana → no granule fetched
- TP   : record con distance_class='summit' o final_hotspot_dist <= inner_radius
- T3   : vrp_vent>0 pero distance_class='far' y final_hotspot lejos (Regla D no
         aplicada — post-S20 esto debería ser cero; si aparece es bug regresión)
- T4   : n_anomalous_pixels>0, no summit, vrp_vent=0 → background no localizado (D6)
- T2b  : record presente pero n_anomalous=0 → escena fría real

Schema field names:
- record JSON: 'datetime_utc', 'sensor', 'vrp_mw', 'vrp_vent_mw',
               'distance_class', 'final_hotspot_dist_km', 'n_anomalous_pixels'
- CSV ref: 'Fecha_Satelite_UTC', 'Volcan', 'Sensor', 'VRP_MW',
           'Distancia_km', 'Origen_Dato'

Uso CLI:
    python experiments/forense_h17_replicable.py \\
        --volcano Tupungatito \\
        --start 2026-03-25 --end 2026-04-25 \\
        --output-json experiments/38_forense_Tupungatito.json \\
        --output-md experiments/38_forense_Tupungatito.md
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


# === Datetime parsing (multiple formats) ===

def _parse_dt_csv(s: str) -> datetime:
    """CSV Mirova-v1 'Fecha_Satelite_UTC' format: 'YYYY-MM-DD HH:MM:SS' UTC."""
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _parse_dt_record(s: str) -> datetime:
    """Record JSON 'datetime_utc' format. Tolerante: con/sin segundos, ISO."""
    s = s.strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            dt = datetime.strptime(s.split("+")[0], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.fromisoformat(s)


# === Sensor matching ===

def sensor_match(ref_sensor: str, rec_sensor: str) -> bool:
    """CSV usa 'VIIRS375', 'VIIRS' (750m), 'MODIS'.
    Record usa 'VIIRS_SNPP', 'VIIRS_NOAA20', 'VIIRS_NOAA21' (375m I-band)
                'VIIRS_*_750' (750m M-band), 'MODIS_AQUA', 'MODIS_TERRA'.
    """
    if ref_sensor == "MODIS":
        return rec_sensor.startswith("MODIS")
    if ref_sensor == "VIIRS":  # 750m
        return rec_sensor.startswith("VIIRS_") and rec_sensor.endswith("_750")
    if ref_sensor == "VIIRS375":
        return rec_sensor.startswith("VIIRS_") and not rec_sensor.endswith("_750")
    return False


def _find_match(ref: dict, records: Iterable[dict], tolerance_min: int) -> dict | None:
    """Busca record con datetime ± tolerance_min minutos y sensor compatible."""
    ref_dt = _parse_dt_csv(ref["Fecha_Satelite_UTC"])
    tol = timedelta(minutes=tolerance_min)
    best, best_delta = None, tol + timedelta(minutes=1)
    for rec in records:
        if not sensor_match(ref["Sensor"], rec.get("sensor", "")):
            continue
        try:
            rec_dt = _parse_dt_record(rec["datetime_utc"])
        except (ValueError, KeyError):
            continue
        delta = abs(rec_dt - ref_dt)
        if delta <= tol and delta < best_delta:
            best, best_delta = rec, delta
    return best


# === Classification ===

def classify_ref(ref: dict, records: Iterable[dict],
                 inner_radius_km: float, tolerance_min: int) -> dict:
    """Devuelve {class, reason, ref, rec}."""
    rec = _find_match(ref, records, tolerance_min)
    if rec is None:
        return {"class": "T1", "reason": "no_record_in_window",
                "ref": ref, "rec": None}

    vrp_vent = float(rec.get("vrp_vent_mw") or 0.0)
    n_anom = int(rec.get("n_anomalous_pixels") or 0)
    dist_class = rec.get("distance_class")
    final_dist = rec.get("final_hotspot_dist_km")

    # TP: summit o dentro de inner_radius
    if dist_class == "summit":
        return {"class": "TP", "reason": "summit_class",
                "ref": ref, "rec": rec}
    if final_dist is not None and final_dist <= inner_radius_km:
        return {"class": "TP", "reason": "within_inner_radius",
                "ref": ref, "rec": rec}

    # T3: vent positivo pero record clasificado far (Regla D no aplicada)
    if vrp_vent > 0:
        return {"class": "T3", "reason": "vent_positive_but_far_class_RegD_not_applied",
                "ref": ref, "rec": rec}

    # T4: pixels anómalos detectados pero todos far
    if n_anom > 0:
        return {"class": "T4", "reason": "pixels_detected_only_far",
                "ref": ref, "rec": rec}

    # T2b: escena fría real
    return {"class": "T2b", "reason": "cold_scene_no_pixels",
            "ref": ref, "rec": rec}


# === Pipeline runner ===

def run_forense(*, volcano: str, consolidado_csv: Path, records_json: Path,
                volcanoes_yaml: Path, start: str, end: str,
                tolerance_min: int = 60) -> dict:
    """Ejecuta forense para volcán + ventana. Devuelve dict con stats + per-ref."""
    df = pd.read_csv(consolidado_csv)
    df = df[df["Volcan"] == volcano]
    # Filtro consolidado: ALERTA_TERMICA = detección real geocodificada
    # (excluye ALERTA_TERMICA_OCR sin geocod, RUTINA y NULO no-detecciones)
    if "Tipo_Registro" in df.columns:
        df = df[df["Tipo_Registro"] == "ALERTA_TERMICA"]
    elif "Origen_Dato" in df.columns:
        # CSV individual por volcán
        df = df[df["Origen_Dato"] == "latest.php"]
    df["dt"] = pd.to_datetime(df["Fecha_Satelite_UTC"])
    df = df[(df["dt"] >= start) & (df["dt"] <= end)]
    refs = df.drop(columns=["dt"]).to_dict("records")

    records = json.loads(records_json.read_text(encoding="utf-8")).get("records", [])

    cfg = yaml.safe_load(volcanoes_yaml.read_text(encoding="utf-8"))
    # volcanoes.yaml es {volcanoes: [{name, ...}, ...]}, no dict por nombre.
    # Tests usan mini-yaml dict-style; soportar ambos.
    if isinstance(cfg, dict) and "volcanoes" in cfg:
        vol_cfg = next((v for v in cfg["volcanoes"]
                        if v.get("name") == volcano), {})
    else:
        vol_cfg = (cfg or {}).get(volcano, {}) if isinstance(cfg, dict) else {}
    inner_km = float(vol_cfg.get("inner_radius_km", 5.0))

    classifications = [classify_ref(r, records, inner_km, tolerance_min) for r in refs]
    counts = {c: 0 for c in ("TP", "T1", "T2b", "T3", "T4")}
    for x in classifications:
        counts[x["class"]] += 1

    n_refs = len(refs)
    return {
        "volcano": volcano,
        "window": [start, end],
        "n_refs": n_refs,
        "tolerance_min": tolerance_min,
        "inner_radius_km": inner_km,
        "counts": counts,
        "recall_summit": (counts["TP"] / n_refs) if n_refs else 0.0,
        "classifications": classifications,
    }


# === MD report ===

def render_md(out: dict) -> str:
    n_refs = out["n_refs"]
    lines = [
        f"# Forense H17 replicable — {out['volcano']}",
        "",
        f"Ventana: {out['window'][0]} → {out['window'][1]}  ·  "
        f"inner_radius_km={out['inner_radius_km']}  ·  "
        f"tolerance_min={out['tolerance_min']}",
        "",
        f"**N refs MIROVA (latest.php only)**: **{n_refs}**",
        "",
        "## Conteos",
        "",
        "| Clase | Count | % | Significado |",
        "|---|---:|---:|---|",
    ]
    meanings = {
        "TP":  "Detectamos correctamente (summit o inner)",
        "T1":  "No hay record nuestro en la ventana — sin granule",
        "T2b": "Record presente, escena fría (n_anomalous=0)",
        "T3":  "vrp_vent>0 pero clasificado far — Regla D NO aplicada (regresión)",
        "T4":  "n_anomalous>0, todos far — D6 background no localizado",
    }
    for c in ("TP", "T1", "T2b", "T3", "T4"):
        n = out["counts"][c]
        pct = (100 * n / n_refs) if n_refs else 0
        lines.append(f"| {c} | {n} | {pct:.1f}% | {meanings[c]} |")
    lines.append("")
    lines.append(f"**Recall summit-class (TP/N)**: {out['recall_summit']:.3f}")
    return "\n".join(lines)


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--consolidado",
                    default="data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
    ap.add_argument("--records", default=None,
                    help="Path al JSON; default data/mirova_equivalent/<volcano>.json")
    ap.add_argument("--yaml", default="volcanoes.yaml")
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    ap.add_argument("--tolerance-min", type=int, default=60)
    args = ap.parse_args()

    records_path = (Path(args.records) if args.records
                    else Path(f"data/mirova_equivalent/{args.volcano}.json"))

    out = run_forense(
        volcano=args.volcano,
        consolidado_csv=Path(args.consolidado),
        records_json=records_path,
        volcanoes_yaml=Path(args.yaml),
        start=args.start,
        end=args.end,
        tolerance_min=args.tolerance_min,
    )

    Path(args.output_json).write_text(json.dumps(out, default=str, indent=2),
                                       encoding="utf-8")
    Path(args.output_md).write_text(render_md(out), encoding="utf-8")
    print(f"OK · {args.volcano}: {out['counts']}")
    print(f"     recall_summit={out['recall_summit']:.3f} · n_refs={out['n_refs']}")


if __name__ == "__main__":
    _main()
