"""
Audit F-S81-A — gate Path D MODIS intra-radio.

Compara 3 profiles sobre los 11 volcanes Tier A:
  - enabled : mirova_equivalent_f_s81_a_intra_radio_enabled (con gate)
  - disabled: mirova_equivalent_f_s81_a_intra_radio_disabled (sin gate, control)
  - baseline: mirova_equivalent (operacional pre-S83)

Métricas por (profile × volcano):
  - N records MODIS con detección (pc.vrp_mw > 0)
  - TP = match contra ALERTA_TERMICA MIROVA (CSV consolidado) ±60 min
  - FP = detección nuestra sin match MIROVA
  - FN = ALERTA MIROVA en ventana sin match nuestro
  - precision, recall, F1
  - FPs / vol-mes (normalizado a 30 días)
  - ratio mediano pc.vrp_mw / mirova_VRP_MW (solo records con match)
  - R3: # records con final_hotspot_source='eruption' y pc.centroid_dist_km > inner_radius_km
        (debe ser 0 en profile enabled)

Output: audit_results.md + audit_results.json en mismo directorio.

Ventana: 2026-04-12 → 2026-05-26 (45 días, == workflow A/B run).
Sensor: MODIS solo (el gate F-S81-A es MODIS-only por diseño).

Uso:
    python experiments/_s83_f_s81_a/audit.py
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "_s83_f_s81_a"

# Ventana A/B (igual al workflow reproc)
WINDOW_START = datetime(2026, 4, 12, 0, 0)
WINDOW_END = datetime(2026, 5, 26, 23, 59)
WINDOW_DAYS = (WINDOW_END - WINDOW_START).days + 1

# Match tolerance temporal
MATCH_TOLERANCE_MIN = 60

# Profiles a auditar
PROFILES = {
    "enabled": "mirova_equivalent_f_s81_a_intra_radio_enabled",
    "disabled": "mirova_equivalent_f_s81_a_intra_radio_disabled",
    "baseline": "mirova_equivalent",
}

# Tier A — orden canónico
TIER_A = [
    "PuyehueCordonCaulle",
    "Villarrica",
    "Lascar",
    "Copahue",
    "NevadosDeChillan",
    "Llaima",
    "Chaiten",
    "PlanchonPeteroa",
    "Lastarria",
    "Isluga",
    "Tupungatito",
]

# Mapping nombre JSON → nombre CSV consolidado (A14 lección)
VOL_NAME_MAP_JSON_TO_CSV = {
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
    "NevadosDeChillan": "Nevados de Chillan",
    "PlanchonPeteroa": "PlanchonPeteroa",  # exact match
    # resto coincide tal cual
}


def vol_csv_name(json_name: str) -> str:
    return VOL_NAME_MAP_JSON_TO_CSV.get(json_name, json_name)


def load_inner_radius() -> dict[str, float]:
    """Lee inner_radius_km por volcán desde volcanoes.yaml."""
    y = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
    return {v["name"]: float(v.get("inner_radius_km", 5)) for v in y["volcanoes"]}


def load_mirova_alertas() -> dict[tuple[str, str], list[dict[str, Any]]]:
    """
    Carga ALERTA_TERMICA del CSV consolidado.

    Returns: dict {(vol_csv_name, sensor_short): [alertas]} donde sensor_short in {MODIS, VIIRS}.
    Cada alerta: {dt, vrp_mw, dist_km, tipo, clasificacion}.
    """
    csv_path = ROOT / "latest_consolidado.csv"
    if not csv_path.exists():
        # fallback al snapshot
        csv_path = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"
    alertas: dict[tuple[str, str], list[dict[str, Any]]] = {}
    with csv_path.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            tipo = (row.get("Tipo_Registro") or "").strip().upper()
            # ALERTAs reales (excluir RUTINA con VRP=0)
            if "ALERTA" not in tipo:
                continue
            vol = (row.get("Volcan") or "").strip()
            sensor = (row.get("Sensor") or "").strip().upper()
            if sensor not in {"MODIS", "VIIRS"}:
                continue
            dt_raw = (row.get("Fecha_Satelite_UTC") or "").strip()
            if not dt_raw:
                continue
            try:
                dt = datetime.strptime(dt_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if not (WINDOW_START <= dt <= WINDOW_END):
                continue
            try:
                vrp = float(row.get("VRP_MW") or 0)
                dist = float(row.get("Distancia_km") or 0)
            except ValueError:
                vrp = dist = 0.0
            alertas.setdefault((vol, sensor), []).append({
                "dt": dt,
                "vrp_mw": vrp,
                "dist_km": dist,
                "tipo": tipo,
                "clasificacion": (row.get("Clasificacion Mirova") or "").strip(),
            })
    return alertas


def sensor_short(sensor_full: str) -> str:
    s = (sensor_full or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if "VIIRS" in s:
        return "VIIRS"
    return s


def parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def load_profile_records(profile_dir: str, vol: str) -> list[dict[str, Any]]:
    """Carga records MODIS de un profile/volcán."""
    p = ROOT / "data" / profile_dir / f"{vol}.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for r in data.get("records", []):
        sensor = sensor_short(r.get("sensor", ""))
        if sensor != "MODIS":
            continue
        dt = parse_dt(r.get("datetime_utc", ""))
        if dt is None:
            continue
        if not (WINDOW_START <= dt <= WINDOW_END):
            continue
        pc = r.get("primary_cluster") or {}
        out.append({
            "dt": dt,
            "sensor": sensor,
            "pc_vrp_mw": float(pc.get("vrp_mw") or 0),
            "pc_dist_km": float(pc.get("centroid_dist_km") or 0),
            "pc_n_pixels": int(pc.get("n_pixels") or 0),
            "n_anomalous_pixels": int(r.get("n_anomalous_pixels") or 0),
            "final_hotspot_source": r.get("final_hotspot_source"),
            "final_hotspot_dist_km": float(r.get("final_hotspot_dist_km") or 0),
            "vrp_mw_scene": float(r.get("vrp_mw") or 0),
        })
    return out


def match_record_to_alerta(rec: dict, alertas: list[dict]) -> dict | None:
    """Busca alerta MIROVA dentro de ±MATCH_TOLERANCE_MIN del record dt."""
    if not alertas:
        return None
    tol = timedelta(minutes=MATCH_TOLERANCE_MIN)
    best = None
    best_dt = None
    for a in alertas:
        if abs(a["dt"] - rec["dt"]) <= tol:
            d = abs(a["dt"] - rec["dt"])
            if best is None or d < best_dt:
                best = a
                best_dt = d
    return best


def audit_volcano(vol: str, profile_key: str, profile_dir: str,
                  mirova: dict, inner_radius: dict) -> dict[str, Any]:
    """Audit un (volcano, profile). Retorna métricas."""
    recs = load_profile_records(profile_dir, vol)
    csv_name = vol_csv_name(vol)
    alertas = mirova.get((csv_name, "MODIS"), [])

    # Detecciones nuestras: pc.vrp_mw > 0 (cluster válido)
    detections = [r for r in recs if r["pc_vrp_mw"] > 0]

    tp = []
    fp = []
    used_alerta_idx = set()
    for r in detections:
        match = match_record_to_alerta(r, alertas)
        if match is not None:
            # encontrar índice de la alerta matched (single-use)
            idx = next((i for i, a in enumerate(alertas)
                        if a is match and i not in used_alerta_idx), None)
            if idx is not None:
                used_alerta_idx.add(idx)
                tp.append({"rec": r, "alerta": match})
            else:
                # alerta ya consumida → FP (over-detection)
                fp.append(r)
        else:
            fp.append(r)

    # FN: alertas MIROVA sin match nuestro
    fn = [a for i, a in enumerate(alertas) if i not in used_alerta_idx]

    # Métricas
    n_tp, n_fp, n_fn = len(tp), len(fp), len(fn)
    precision = n_tp / (n_tp + n_fp) if (n_tp + n_fp) else float("nan")
    recall = n_tp / (n_tp + n_fn) if (n_tp + n_fn) else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if (precision and recall and precision + recall > 0)
          else float("nan"))
    fps_per_vol_month = n_fp * 30.0 / WINDOW_DAYS

    # Ratio mediano (solo TPs)
    ratios = []
    for m in tp:
        gt = m["alerta"]["vrp_mw"]
        ours = m["rec"]["pc_vrp_mw"]
        if gt > 0:
            ratios.append(ours / gt)
    ratio_med = median(ratios) if ratios else float("nan")

    # R3: 'eruption' con cluster fuera de inner_radius
    inner_r = inner_radius.get(vol, 5.0)
    r3_violators = [
        r for r in recs
        if r["final_hotspot_source"] == "eruption"
        and r["pc_dist_km"] > inner_r
        and r["pc_vrp_mw"] > 0
    ]

    return {
        "volcano": vol,
        "profile": profile_key,
        "n_records_modis": len(recs),
        "n_detections": len(detections),
        "n_alertas_mirova": len(alertas),
        "tp": n_tp, "fp": n_fp, "fn": n_fn,
        "precision": round(precision, 3) if precision == precision else None,
        "recall": round(recall, 3) if recall == recall else None,
        "f1": round(f1, 3) if f1 == f1 else None,
        "fps_per_vol_month": round(fps_per_vol_month, 2),
        "ratio_median": round(ratio_med, 3) if ratio_med == ratio_med else None,
        "n_ratios": len(ratios),
        "r3_violators": len(r3_violators),
        "inner_radius_km": inner_r,
    }


def main() -> int:
    print(f"[audit S83 F-S81-A] window {WINDOW_START.date()} -> {WINDOW_END.date()} ({WINDOW_DAYS}d)")
    inner_radius = load_inner_radius()
    mirova = load_mirova_alertas()
    n_alertas = sum(len(v) for v in mirova.values())
    print(f"[audit] {n_alertas} ALERTAs MODIS+VIIRS MIROVA en ventana")

    all_rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for profile_key, profile_dir in PROFILES.items():
        for vol in TIER_A:
            p = ROOT / "data" / profile_dir / f"{vol}.json"
            if not p.exists():
                missing.append(f"{profile_dir}/{vol}.json")
                continue
            row = audit_volcano(vol, profile_key, profile_dir, mirova, inner_radius)
            all_rows.append(row)

    # Output
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "audit_results.json").write_text(
        json.dumps({"window_days": WINDOW_DAYS, "rows": all_rows, "missing": missing}, indent=2),
        encoding="utf-8",
    )

    # Markdown
    md = ["# Audit F-S81-A — gate Path D MODIS intra-radio\n"]
    md.append(f"**Ventana**: {WINDOW_START.date()} → {WINDOW_END.date()} ({WINDOW_DAYS}d)\n")
    md.append(f"**Sensor**: MODIS solo (gate por diseño)\n")
    md.append(f"**Tolerancia match temporal**: ±{MATCH_TOLERANCE_MIN} min\n")
    md.append(f"**Profiles**: {', '.join(PROFILES.keys())}\n")
    if missing:
        md.append(f"\n⚠️  JSONs faltantes ({len(missing)}): {missing[:5]}...\n")

    # Tabla por profile
    for profile_key in PROFILES:
        md.append(f"\n## Profile: `{profile_key}`\n")
        md.append("| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | inner |\n")
        md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        rows_p = [r for r in all_rows if r["profile"] == profile_key]
        for r in rows_p:
            md.append(
                f"| {r['volcano']} | {r['n_records_modis']} | {r['n_detections']} | "
                f"{r['n_alertas_mirova']} | {r['tp']} | {r['fp']} | {r['fn']} | "
                f"{r['precision']} | {r['recall']} | {r['f1']} | "
                f"{r['fps_per_vol_month']} | {r['ratio_median']} | {r['r3_violators']} | "
                f"{r['inner_radius_km']} |\n"
            )
        # Agregados
        sum_tp = sum(r["tp"] for r in rows_p)
        sum_fp = sum(r["fp"] for r in rows_p)
        sum_fn = sum(r["fn"] for r in rows_p)
        prec_agg = sum_tp / (sum_tp + sum_fp) if (sum_tp + sum_fp) else float("nan")
        rec_agg = sum_tp / (sum_tp + sum_fn) if (sum_tp + sum_fn) else float("nan")
        md.append(
            f"| **TOTAL** | — | — | — | **{sum_tp}** | **{sum_fp}** | **{sum_fn}** | "
            f"**{prec_agg:.3f}** | **{rec_agg:.3f}** | — | "
            f"**{sum_fp*30.0/WINDOW_DAYS/11:.2f}** | — | "
            f"**{sum(r['r3_violators'] for r in rows_p)}** | — |\n"
        )

    # Decisión adopción
    md.append("\n## Decisión adopción (umbrales objetivo)\n")
    md.append("- Precision MODIS Tier A: **≥ 0.70**\n")
    md.append("- Recall MIROVA: **≥ 0.85** (no regresión >5pp per-vol vs disabled/baseline)\n")
    md.append("- FPs/vol-mes MODIS: **≤ 15**\n")
    md.append("- R3 violators (eruption fuera inner_radius en `enabled`): **0**\n")

    # Comparativa per-vol enabled vs disabled (delta recall, FPs)
    md.append("\n### Δ enabled - disabled (per-volcano)\n")
    md.append("| Volcán | Δ TP | Δ FP | Δ FN | Δ Recall | Δ Precision | Δ FPs/mes |\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|\n")
    by_key = {(r["volcano"], r["profile"]): r for r in all_rows}
    for vol in TIER_A:
        e = by_key.get((vol, "enabled"))
        d = by_key.get((vol, "disabled"))
        if not e or not d:
            continue
        d_tp = e["tp"] - d["tp"]
        d_fp = e["fp"] - d["fp"]
        d_fn = e["fn"] - d["fn"]
        d_rec = ((e["recall"] or 0) - (d["recall"] or 0)) if e["recall"] is not None and d["recall"] is not None else None
        d_pre = ((e["precision"] or 0) - (d["precision"] or 0)) if e["precision"] is not None and d["precision"] is not None else None
        d_fpm = e["fps_per_vol_month"] - d["fps_per_vol_month"]
        rec_str = f"{d_rec:+.3f}" if d_rec is not None else "n/a"
        pre_str = f"{d_pre:+.3f}" if d_pre is not None else "n/a"
        md.append(
            f"| {vol} | {d_tp:+d} | {d_fp:+d} | {d_fn:+d} | "
            f"{rec_str} | {pre_str} | {d_fpm:+.2f} |\n"
        )

    (OUT_DIR / "audit_results.md").write_text("".join(md), encoding="utf-8")
    print(f"[audit] OK -> {OUT_DIR/'audit_results.md'}")
    print(f"[audit] OK -> {OUT_DIR/'audit_results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
