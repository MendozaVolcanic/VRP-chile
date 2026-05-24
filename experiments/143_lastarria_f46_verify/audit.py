"""S77 — Simulación del impacto del fix F46 (PR #177) sobre Lastarria.

Tarea read-only sin re-procesar L1B. Simulamos el efecto del fix sobre los JSON
operacionales (`data/mirova_equivalent/<Volcano>.json`) usando los campos ya
persistidos en cada record.

Lógica del fix (post-PR #177, ver `pipeline/process_viirs.py:_compute_vrp_tir_with_gate`):

  - **Opción A (gate consistencia MIR/NTI)**: si la unión de paths MIR/NTI
    (`hot_mask_2d` pre-clustering) está vacía → `vrp_tir_mw = 0`. Se proxia
    desde el record sumando los conteos de paths que efectivamente alimentan
    esa máscara: `n_bt_path + n_nti_path + n_nti_rel_path + n_dnti_ctx_path`.
    Si la suma es 0, A capa el record.
  - **Opción B (threshold subido)**: `max(3K, 6σ)` en lugar de `max(0.5K, 4σ)`.
    No reproducible sin BT raw; clasificamos como "B-likely" los records con
    `vrp_tir_mw > 100 MW` que sobrevivieron A (heurística conservadora: el doc
    F46 indica que el threshold viejo era 12-22 K efectivo en los outliers y
    el nuevo será 18-36 K → muchos de esos pixels dejan de contar).

Output:
  - audit.out.json: tabla por volcán con A_killed / B_likely_reduced / survives,
    y recall MIROVA pre vs post simulado.
"""
from __future__ import annotations
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "mirova_equivalent"
CSV_PATH = ROOT / "latest_consolidado.csv"

# Volcanes a auditar — Lastarria (foco), Chaiten (contraejemplo patognomónico),
# 3 Tier A más para contexto.
VOLCANOES = [
    "Lastarria",
    "Chaiten",
    "Villarrica",
    "Lascar",
    "PlanchonPeteroa",
    "Copahue",
]

# Mapping volcán-VRP-Chile → nombre en CSV consolidado.
CSV_NAME = {
    "Lastarria": "Lastarria",
    "Chaiten": "Chaiten",
    "Villarrica": "Villarrica",
    "Lascar": "Lascar",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Copahue": "Copahue",
}

# Match window contra CSV consolidado (granule pass ±60 min).
MATCH_DELTA_MIN = 60

# Threshold "B-likely-reduced" — vrp_tir > este valor probablemente cae mucho
# con el nuevo threshold 3K/6σ (per §4.1 outliers tienen σ_bg ≥ 3K, threshold
# pasa de ~12-22 K a ~18-36 K → la mayoría de pixels contaminantes salen).
B_LIKELY_THRESHOLD_MW = 100.0


def parse_dt(s: str) -> datetime | None:
    """Parse `YYYY-MM-DD HH:MM` (record) o `YYYY-MM-DD HH:MM:SS` (CSV)."""
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def load_records(volcano: str) -> list[dict]:
    p = DATA_DIR / f"{volcano}.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    recs = d.get("records", d) if isinstance(d, dict) else d
    return [r for r in recs if isinstance(r, dict)]


def is_viirs_iband(sensor: str) -> bool:
    """El fix F46 toca SOLO VIIRS I-band (process_viirs.py)."""
    if not sensor:
        return False
    s = sensor.upper()
    # VIIRS_SNPP, VIIRS_NOAA20, VIIRS_NOAA21 corresponden a process_viirs.py
    # (I-band 375m). VIIRS_*_M / process_viirs_mod NO tiene path TIR.
    if not s.startswith("VIIRS"):
        return False
    # Excluir M-band si aparece marcado (no afectado).
    if "_M" in s or s.endswith("M") or "750" in s:
        return False
    return True


def mir_nti_path_sum(rec: dict) -> int:
    """Conteo unión paths MIR/NTI que alimentan hot_mask_2d pre-clustering.

    En el código (process_viirs.py), hot_mask_2d = unión de:
      - eruption-path BT (n_bt_path)
      - NTI absoluto (n_nti_path)
      - NTI relativo (n_nti_rel_path)
      - dNTI contextual (n_dnti_ctx_path)
    Si la suma de los 4 contadores es 0, el código setea hot_mask_2d vacía
    (o el fallback default) y el gate A captura.

    Caveat: si por algún motivo el record viene de un volcán donde el bloque
    eruption-path no ejecutó (sin I04), `hot_mask_2d` no se define y el helper
    `locals().get(...)` retorna una máscara cero → A también capa.
    """
    keys = ("n_bt_path", "n_nti_path", "n_nti_rel_path", "n_dnti_ctx_path")
    total = 0
    for k in keys:
        v = rec.get(k)
        if isinstance(v, (int, float)) and v > 0:
            total += int(v)
    return total


def classify(rec: dict) -> str:
    """Clasificar destino del vrp_tir_mw bajo el fix F46.

    Retorna:
      - 'no_tir'        — vrp_tir_mw <= 0, fix no aplica.
      - 'not_iband'     — no es VIIRS I-band, fix no aplica.
      - 'A_killed'      — gate A captura (paths MIR/NTI = 0). vrp_tir → 0.
      - 'B_likely_red'  — sobrevive A pero vrp_tir > 100 MW, threshold B
                          probablemente lo reduce mucho (no podemos
                          cuantificar sin BT raw).
      - 'survives'      — sobrevive A y vrp_tir bajo (<=100 MW), probable
                          que el fix lo deje similar.
    """
    vrp_tir = rec.get("vrp_tir_mw")
    if not isinstance(vrp_tir, (int, float)) or vrp_tir <= 0:
        return "no_tir"
    sensor = str(rec.get("sensor", ""))
    if not is_viirs_iband(sensor):
        return "not_iband"
    paths = mir_nti_path_sum(rec)
    if paths == 0:
        return "A_killed"
    if vrp_tir > B_LIKELY_THRESHOLD_MW:
        return "B_likely_red"
    return "survives"


def load_mirova_refs(volcano: str) -> list[dict]:
    """Refs MIROVA del CSV consolidado, solo alertas (VRP_MW > 0)."""
    csv_name = CSV_NAME.get(volcano)
    if not csv_name or not CSV_PATH.exists():
        return []
    refs = []
    with CSV_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Volcan") != csv_name:
                continue
            try:
                vrp_mw = float(row.get("VRP_MW", "0") or 0)
            except ValueError:
                vrp_mw = 0.0
            if vrp_mw <= 0:
                continue
            dt = parse_dt(row.get("Fecha_Satelite_UTC", ""))
            if not dt:
                continue
            sensor = row.get("Sensor", "")
            refs.append({
                "dt": dt,
                "sensor": sensor,
                "vrp_mw": vrp_mw,
            })
    return refs


def match_recall(
    recs_with_tir_pre: list[dict],
    recs_with_tir_post: list[dict],
    refs: list[dict],
) -> dict:
    """Calcula recall MIROVA pre vs post sobre VIIRS I-band.

    Para cada ref MIROVA-VIIRS, busca record nuestro ±MATCH_DELTA_MIN.
    Pre: cuenta como TP si existe record VIIRS I-band con vrp_tir_mw > 0.
    Post: cuenta como TP si existe record VIIRS I-band que sobrevive al fix
          (clasificación != A_killed; B_likely_red SÍ cuenta como sobrevive
          para recall ya que no llega a 0, solo se reduce).
    """
    pre_lookup = defaultdict(list)
    for r in recs_with_tir_pre:
        dt = parse_dt(r.get("datetime_utc", ""))
        if dt:
            pre_lookup[dt.date()].append(dt)
    post_lookup = defaultdict(list)
    for r in recs_with_tir_post:
        dt = parse_dt(r.get("datetime_utc", ""))
        if dt:
            post_lookup[dt.date()].append(dt)

    delta = timedelta(minutes=MATCH_DELTA_MIN)
    # Solo refs sensor VIIRS / VIIRS375 (no MODIS — fix no aplica).
    viirs_refs = [r for r in refs if str(r["sensor"]).upper().startswith("VIIRS")]

    tp_pre = 0
    tp_post = 0
    for ref in viirs_refs:
        d = ref["dt"].date()
        # Probar ventana día anterior y siguiente por overflow
        candidates_pre = pre_lookup.get(d, []) + pre_lookup.get(
            d - timedelta(days=1), []) + pre_lookup.get(d + timedelta(days=1), [])
        candidates_post = post_lookup.get(d, []) + post_lookup.get(
            d - timedelta(days=1), []) + post_lookup.get(d + timedelta(days=1), [])
        if any(abs((c - ref["dt"]).total_seconds()) <= delta.total_seconds()
               for c in candidates_pre):
            tp_pre += 1
        if any(abs((c - ref["dt"]).total_seconds()) <= delta.total_seconds()
               for c in candidates_post):
            tp_post += 1
    return {
        "viirs_refs_total": len(viirs_refs),
        "tp_pre_fix": tp_pre,
        "tp_post_fix": tp_post,
        "recall_pre": (tp_pre / len(viirs_refs)) if viirs_refs else None,
        "recall_post": (tp_post / len(viirs_refs)) if viirs_refs else None,
        "delta_tp": tp_post - tp_pre,
    }


def audit_volcano(volcano: str) -> dict:
    recs = load_records(volcano)
    counts = defaultdict(int)
    pre_recs = []
    post_recs = []
    # Por debug: agrupar A_killed por motivo
    a_killed_examples = []
    b_likely_examples = []
    for r in recs:
        cls = classify(r)
        counts[cls] += 1
        if cls in ("A_killed", "B_likely_red", "survives"):
            pre_recs.append(r)
            if cls != "A_killed":
                post_recs.append(r)
            if cls == "A_killed" and len(a_killed_examples) < 3:
                a_killed_examples.append({
                    "datetime_utc": r.get("datetime_utc"),
                    "sensor": r.get("sensor"),
                    "vrp_tir_mw": r.get("vrp_tir_mw"),
                    "vrp_mir_mw": r.get("vrp_mir_mw"),
                    "n_anomalous_pixels": r.get("n_anomalous_pixels"),
                    "paths_sum": mir_nti_path_sum(r),
                })
            if cls == "B_likely_red" and len(b_likely_examples) < 3:
                b_likely_examples.append({
                    "datetime_utc": r.get("datetime_utc"),
                    "sensor": r.get("sensor"),
                    "vrp_tir_mw": r.get("vrp_tir_mw"),
                    "vrp_mir_mw": r.get("vrp_mir_mw"),
                    "n_anomalous_pixels": r.get("n_anomalous_pixels"),
                })

    refs = load_mirova_refs(volcano)
    recall = match_recall(pre_recs, post_recs, refs)

    total_tir_iband = (counts["A_killed"] + counts["B_likely_red"]
                       + counts["survives"])
    a_pct = (counts["A_killed"] / total_tir_iband * 100) if total_tir_iband else 0
    b_pct = (counts["B_likely_red"] / total_tir_iband * 100) if total_tir_iband else 0

    return {
        "volcano": volcano,
        "total_records": len(recs),
        "viirs_iband_with_vrp_tir": total_tir_iband,
        "A_killed": counts["A_killed"],
        "A_killed_pct": round(a_pct, 1),
        "B_likely_reduced": counts["B_likely_red"],
        "B_likely_reduced_pct": round(b_pct, 1),
        "survives_low_tir": counts["survives"],
        "survives_low_tir_pct": round(100 - a_pct - b_pct, 1),
        "no_tir": counts["no_tir"],
        "not_iband": counts["not_iband"],
        "recall": recall,
        "a_killed_examples": a_killed_examples,
        "b_likely_examples": b_likely_examples,
    }


def main():
    results = {
        "meta": {
            "session": "S77",
            "task": "F46 fix impact verification on Lastarria",
            "fix_pr": 177,
            "fix_logic": "Opción A (gate consistencia MIR/NTI dilate k=3) + "
                         "Opción B (threshold max(3K, 6σ) vs legacy max(0.5K, 4σ))",
            "heuristic_A": "paths_sum := n_bt_path + n_nti_path + n_nti_rel_path "
                           "+ n_dnti_ctx_path. Si == 0 → record cae bajo gate A.",
            "heuristic_B": "Conservador: records con vrp_tir > 100 MW que "
                           "sobreviven A se marcan B_likely_red (probablemente "
                           "el threshold los reduce mucho). No se cuantifica "
                           "magnitud exacta sin BT raw.",
            "match_window_min": MATCH_DELTA_MIN,
            "scope": "Solo VIIRS I-band (process_viirs.py). MODIS y VIIRS-M no "
                     "tienen path TIR Stefan-Boltzmann separado.",
        },
        "by_volcano": [],
    }
    for v in VOLCANOES:
        print(f"Auditing {v}...")
        results["by_volcano"].append(audit_volcano(v))

    out = Path(__file__).parent / "audit.out.json"
    out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {out}")

    # Resumen consola
    print("\n=== RESUMEN ===")
    print(f"{'Volcán':<20}{'TIR-iband':>10}{'A_kill':>8}{'A%':>6}"
          f"{'B_red':>7}{'B%':>6}{'recall_pre':>12}{'recall_post':>13}")
    for r in results["by_volcano"]:
        rec = r["recall"]
        rp = f"{rec['recall_pre']:.3f}" if rec['recall_pre'] is not None else "—"
        rq = f"{rec['recall_post']:.3f}" if rec['recall_post'] is not None else "—"
        print(f"{r['volcano']:<20}{r['viirs_iband_with_vrp_tir']:>10}"
              f"{r['A_killed']:>8}{r['A_killed_pct']:>6}"
              f"{r['B_likely_reduced']:>7}{r['B_likely_reduced_pct']:>6}"
              f"{rp:>12}{rq:>13}")


if __name__ == "__main__":
    main()
