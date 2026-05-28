"""
B0 audit — distribución de R3 violators por path activo.

Identifica los R3 violators del profile `mirova_equivalent_f_s81_a_intra_radio_enabled`
(records MODIS con final_hotspot_source='eruption' + pc.centroid_dist_km > inner_radius_km)
y cuenta qué paths del primer pase contribuyeron (diag_n_*_path > 0).

Output: docs/R3_RESIDUAL_BY_PATH.md con:
- Tabla per-vol: # R3 violators con cada path activo.
- Top-K records con sus paths (para debugging).
- Recomendación priorización Fase B (qué path atacar primero).

Uso:
    python experiments/_s85_f_s81_b/audit_r3_by_path.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "_s85_f_s81_b"
DOCS_OUT = ROOT / "docs" / "R3_RESIDUAL_BY_PATH.md"

# Profile que adoptamos (post-S84). El gate Path D ya está activo.
PROFILE_DIR = "mirova_equivalent_f_s81_a_intra_radio_enabled"

# Ventana A/B S83-S84
WINDOW_START = datetime(2026, 4, 12, 0, 0)
WINDOW_END = datetime(2026, 5, 26, 23, 59)

TIER_A = [
    "PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue",
    "NevadosDeChillan", "Llaima", "Chaiten", "PlanchonPeteroa",
    "Lastarria", "Isluga", "Tupungatito",
]

PATH_FIELDS = {
    "A_bt": "diag_n_bt_path",
    "B_nti": "diag_n_nti_path",
    "C_eti": "diag_n_eti_path",
    "D_dnti_ctx": "diag_n_dnti_ctx_path",
}


def sensor_short(s: str) -> str:
    s = (s or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if "VIIRS" in s:
        return "VIIRS"
    return s


def parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def load_inner_radius() -> dict[str, float]:
    y = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
    return {v["name"]: float(v.get("inner_radius_km", 5)) for v in y["volcanoes"]}


def find_r3_violators(vol: str, inner_r: float) -> list[dict[str, Any]]:
    p = ROOT / "data" / PROFILE_DIR / f"{vol}.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for r in data.get("records", []):
        if sensor_short(r.get("sensor", "")) != "MODIS":
            continue
        dt = parse_dt(r.get("datetime_utc", ""))
        if dt is None or not (WINDOW_START <= dt <= WINDOW_END):
            continue
        if r.get("final_hotspot_source") != "eruption":
            continue
        pc = r.get("primary_cluster") or {}
        pc_dist = float(pc.get("centroid_dist_km") or 0)
        pc_vrp = float(pc.get("vrp_mw") or 0)
        if pc_vrp <= 0 or pc_dist <= inner_r:
            continue
        # R3 violator
        paths_active = {
            path_label: int(r.get(field, 0) or 0)
            for path_label, field in PATH_FIELDS.items()
        }
        out.append({
            "vol": vol,
            "dt": dt.isoformat(),
            "sensor": r.get("sensor"),
            "pc_dist_km": pc_dist,
            "pc_vrp_mw": pc_vrp,
            "pc_n_pixels": int(pc.get("n_pixels") or 0),
            "inner_radius_km": inner_r,
            "paths_active": paths_active,
            "n_first_pass_pixels": int(r.get("diag_n_first_pass_pixels", 0) or 0),
            "n_second_pass_recapture": int(r.get("diag_n_second_pass_recapture", 0) or 0),
        })
    return out


def main() -> int:
    print(f"[B0] R3 audit sobre {PROFILE_DIR}")
    print(f"[B0] window {WINDOW_START.date()} -> {WINDOW_END.date()}")
    inner_radius = load_inner_radius()

    all_violators: list[dict] = []
    per_vol_count: dict[str, int] = {}
    for vol in TIER_A:
        inner_r = inner_radius.get(vol, 5.0)
        vs = find_r3_violators(vol, inner_r)
        per_vol_count[vol] = len(vs)
        all_violators.extend(vs)

    total = len(all_violators)
    print(f"[B0] {total} R3 violators encontrados")

    # Distribución per-path: # records con ese path > 0 (no exclusivo)
    path_count: Counter = Counter()
    path_exclusive: Counter = Counter()  # records donde SOLO ese path se disparó
    no_path = 0
    multi_path = 0
    for v in all_violators:
        active = [k for k, n in v["paths_active"].items() if n > 0]
        if not active:
            no_path += 1
        elif len(active) == 1:
            path_exclusive[active[0]] += 1
        else:
            multi_path += 1
        for k in active:
            path_count[k] += 1

    # Per-volcano breakdown
    per_vol_path: dict[str, Counter] = defaultdict(Counter)
    for v in all_violators:
        for k, n in v["paths_active"].items():
            if n > 0:
                per_vol_path[v["vol"]][k] += 1

    # Output JSON
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "r3_violators_detail.json").write_text(
        json.dumps({
            "profile": PROFILE_DIR,
            "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
            "total_violators": total,
            "per_vol_count": per_vol_count,
            "path_count_any_active": dict(path_count),
            "path_exclusive": dict(path_exclusive),
            "no_path_active": no_path,
            "multi_path_active": multi_path,
            "violators": all_violators,
        }, indent=2, default=str),
        encoding="utf-8",
    )

    # Markdown
    md = []
    md.append("# Audit B0 — R3 violators residuales por path\n")
    md.append(f"**Profile**: `{PROFILE_DIR}` (operacional adoptado S84)\n")
    md.append(f"**Ventana**: {WINDOW_START.date()} → {WINDOW_END.date()} (45d)\n")
    md.append(f"**Definición R3 violator**: MODIS record con "
              f"`final_hotspot_source='eruption'` + `pc.centroid_dist_km > inner_radius_km` "
              f"+ `pc.vrp_mw > 0`. Esto significa que el pipeline marcó actividad eruptiva "
              f"pero el centroide del cluster cae FUERA del cono caliente esperado.\n\n")

    md.append(f"## Total: {total} R3 violators en 45d × 11 Tier A\n\n")

    md.append("### Distribución per-volcano\n\n")
    md.append("| Volcán | # R3 violators | inner_km |\n|---|---:|---:|\n")
    for vol in TIER_A:
        n = per_vol_count[vol]
        ir = inner_radius.get(vol, 5.0)
        md.append(f"| {vol} | {n} | {ir} |\n")
    md.append("\n")

    md.append("### Distribución por path activo (no exclusivo)\n\n")
    md.append("Un record puede tener varios paths activos simultáneamente. "
              "Esta tabla cuenta cuántos R3 violators tienen ese path activo "
              "(diag_n_*_path > 0), independiente de los demás.\n\n")
    md.append("| Path | Campo diag | # R3 con path activo | % del total |\n")
    md.append("|---|---|---:|---:|\n")
    for label, field in PATH_FIELDS.items():
        n = path_count.get(label, 0)
        pct = (100 * n / total) if total else 0
        md.append(f"| {label} | `{field}` | {n} | {pct:.1f}% |\n")
    md.append(f"| (ningún path 1er pase) | — | {no_path} | "
              f"{(100*no_path/total if total else 0):.1f}% |\n")
    md.append("\n")

    md.append("### Distribución por path EXCLUSIVO (único path activo)\n\n")
    md.append("Records donde SOLO un path se disparó (otros 3 en 0). Indica "
              "qué path es el que ÚNICO causa el R3 violator → atacar ese path "
              "elimina ese record sin afectar otros.\n\n")
    md.append("| Path único | # R3 exclusivos | % del total |\n|---|---:|---:|\n")
    for label in PATH_FIELDS:
        n = path_exclusive.get(label, 0)
        pct = (100 * n / total) if total else 0
        md.append(f"| {label} | {n} | {pct:.1f}% |\n")
    md.append(f"| (multi-path) | {multi_path} | "
              f"{(100*multi_path/total if total else 0):.1f}% |\n")
    md.append(f"| (no path 1er pase) | {no_path} | "
              f"{(100*no_path/total if total else 0):.1f}% |\n")
    md.append("\n")

    md.append("### Per-vol × path (heatmap textual)\n\n")
    md.append("| Volcán | A_bt | B_nti | C_eti | D_dnti_ctx | n_first | n_2nd |\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|\n")
    for vol in TIER_A:
        vs = [v for v in all_violators if v["vol"] == vol]
        if not vs:
            md.append(f"| {vol} | 0 | 0 | 0 | 0 | — | — |\n")
            continue
        a = sum(1 for v in vs if v["paths_active"]["A_bt"] > 0)
        b = sum(1 for v in vs if v["paths_active"]["B_nti"] > 0)
        c = sum(1 for v in vs if v["paths_active"]["C_eti"] > 0)
        d = sum(1 for v in vs if v["paths_active"]["D_dnti_ctx"] > 0)
        n_fp = sum(v["n_first_pass_pixels"] for v in vs)
        n_2nd = sum(v["n_second_pass_recapture"] for v in vs)
        md.append(f"| {vol} | {a} | {b} | {c} | {d} | {n_fp} | {n_2nd} |\n")
    md.append("\n")

    # Recomendación Fase B
    md.append("## Recomendación priorización Fase B\n\n")
    sorted_paths = sorted(path_count.items(), key=lambda x: -x[1])
    if sorted_paths:
        md.append("Atacar paths en orden de cobertura R3 (mayor → menor):\n\n")
        for i, (label, n) in enumerate(sorted_paths, 1):
            pct = (100 * n / total) if total else 0
            md.append(f"{i}. **{label}**: {n} R3 ({pct:.1f}%). "
                      f"Implementar gate intra-radio análogo al F-S81-A en `{PATH_FIELDS[label]}`.\n")
        md.append("\n")
    if no_path > 0:
        md.append(f"⚠️  **{no_path} R3 violators ({100*no_path/total:.1f}%) "
                  f"no tienen NINGÚN path 1er pase activo**. Probablemente vienen del "
                  f"second_pass_recapture o de paths sin diag_n_*_path field "
                  f"(Test 1 integrated, vent_anchored rescue, cluster_rescue). "
                  f"Estos NO los cubre ningún gate del primer pase — requieren "
                  f"investigación separada (Fase C o mecanismo distinto).\n\n")
    md.append("\n## Refs\n\n")
    md.append("- Profile auditado: `pipeline/profiles/{PROFILE_DIR}.yaml` (mergeado S84).\n")
    md.append("- Backlog Fase B: `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md`\n")
    md.append("- Helper actual Path D: `pipeline/path_d_intra_radio.py`\n")
    md.append("- Detalle JSON: `experiments/_s85_f_s81_b/r3_violators_detail.json`\n")

    DOCS_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOCS_OUT.write_text("".join(md), encoding="utf-8")
    print(f"[B0] -> {DOCS_OUT}")
    print(f"[B0] -> {OUT_DIR/'r3_violators_detail.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
