"""
Simulación integrada F61 + F63 (+ F57 cualitativo) sobre snapshot operacional.

Read-only. NO modifica data ni pipeline. Solo emite tabla cuantitativa para
documentar impacto combinado antes de implementar.

Salida:
- stdout: tabla síntesis
- experiments/150_brainstorm_integrado/sim_results.json: resultados crudos

Lógica simulación:

F61 (gate global NTI > -0.85 sobre hot_mask):
  - Proxy disponible: `diag_nti_max` per record (NTI máximo entre pixels del granule).
  - Si `diag_nti_max < -0.85`: el record entero se filtraría post-F61 (TODOS los pixels
    están por debajo del gate). vrp_mw → 0 efectivo, record eliminado del dashboard.
  - Si `diag_nti_max >= -0.85`: al menos 1 pixel sobrevive el gate. Asumimos
    conservadoramente que el record sobrevive con vrp_mw posiblemente reducido pero >0.
  - Limitación: este proxy puede ser optimista en pixels VRP — un solo pixel "lava-like"
    salva todo el record. En la práctica F61 también re-calcularía vrp_mw sobre el subset
    de pixels que sobreviven, pero esa cuantificación exacta requiere reproc completo.
    Para el brainstorm, contamos records preservados/eliminados.

F63 (revertir filtro `with_vrp` en clustering S43):
  - Proxy: records con `primary_cluster.centroid_dist_km > inner_radius_km`
    Y con `anomaly_pixels` que SÍ caen dentro del inner_radius.
  - Esos records post-F63 pasarían a tener primary_cluster summit (vrp posiblemente 0
    por clip D4, pero ubicación correcta). El dashboard dejaría de pintarlos como
    "lago a 14 km".
  - Métrica reportada: % records "far" antes vs después (esperado <5% Copahue post-F63).

F57 (local_kernel_bg Copahue+Llaima):
  - Cualitativo — sin reproc completo no se puede simular exacto.
  - Estimación: 70-90% FPs lago en estos 2 volcanes desaparecerían adicionalmente
    sobre la base ya filtrada por F61. Reportamos como rango.

Combinado:
  - Tabla per volcán: n_records actual / post-F61 / post-F61+F63 / post-F61+F63+F57.
  - Métrica clave: "records lava-like preservados" (diag_nti_max > -0.80) — debe
    ser ≥ 99% post combinación.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "mirova_equivalent"
OUT = Path(__file__).parent / "sim_results.json"

TIER_A = [
    ("Lascar", 5),
    ("Lastarria", 3),
    ("Tupungatito", 7),
    ("PlanchonPeteroa", 3),
    ("Copahue", 4),
    ("Llaima", 5),
    ("Villarrica", 5),
    ("NevadosDeChillan", 5),
    ("Chaiten", 5),
    ("Isluga", 5),
    ("PuyehueCordonCaulle", 20),
]

# F57 estimación impacto incremental sobre base F61
F57_VOLS = {"Copahue", "Llaima"}
F57_INCREMENTAL_REDUCTION_PCT = 0.80  # 70-90%, punto medio

NTI_GATE = -0.85  # F61 Opción A recomendada (margen sobre k1 MIROVA -0.80)
LAVA_LIKE_THR = -0.80  # records con diag_nti_max > -0.80 = lava-like según F61 doc


def load_records(vol: str) -> list[dict]:
    p = DATA_DIR / f"{vol}.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(d, list):
        return d
    return d.get("records", [])


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def simulate_volcano(vol: str, inner_km: float, window_30d: bool = False) -> dict:
    rs = load_records(vol)
    if not rs:
        return {"volcano": vol, "n_total": 0}

    if window_30d:
        # Anclar ventana al record más reciente del propio archivo (robusto a snapshots).
        max_dt = None
        for r in rs:
            dt = parse_dt(r.get("datetime_utc"))
            if dt is not None and (max_dt is None or dt > max_dt):
                max_dt = dt
        if max_dt is None:
            rs = []
        else:
            cutoff = max_dt - timedelta(days=30)
            rs = [r for r in rs if (dt := parse_dt(r.get("datetime_utc"))) and dt >= cutoff]

    n_total = len(rs)
    n_with_vrp = sum(1 for r in rs if r.get("vrp_mw", 0) > 0)

    # F61 simulation: records preservados (diag_nti_max >= -0.85 OR vrp_mw == 0)
    # records con vrp_mw=0 ya no son detecciones — ni se cuentan como FP ni se eliminan.
    # Métrica: detecciones (vrp_mw>0) que sobreviven F61.
    n_post_f61 = 0
    n_filtered_by_f61 = 0
    for r in rs:
        if r.get("vrp_mw", 0) <= 0:
            continue
        nti_max = r.get("diag_nti_max")
        if nti_max is None:
            # sin diagnóstico NTI — asumir preservado (conservador)
            n_post_f61 += 1
            continue
        if nti_max >= NTI_GATE:
            n_post_f61 += 1
        else:
            n_filtered_by_f61 += 1

    # F63 simulation: records cuyo primary_cluster está fuera del inner
    # pero hay anomaly_pixels dentro del inner. Post-F63 esos quedan re-asignados
    # a summit (cluster summit gana aunque vrp=0). En conteo de detecciones,
    # el record sigue existiendo pero deja de mostrarse como "lejano".
    # Si post-F61 ya fue filtrado, F63 no aplica adicional.
    # Aplicamos F63 SOLO a los que sobreviven F61.
    n_far_pre_f63 = 0      # records far (con vrp>0, sobrevivientes F61)
    n_far_post_f63 = 0     # records que SIGUEN far post-F63 (no había pixel cerca tampoco)
    n_reassigned_f63 = 0   # records re-asignados a summit por F63

    for r in rs:
        if r.get("vrp_mw", 0) <= 0:
            continue
        nti_max = r.get("diag_nti_max")
        if nti_max is not None and nti_max < NTI_GATE:
            continue  # filtrado por F61, F63 no aplica
        pc = r.get("primary_cluster") or {}
        pc_dist = pc.get("centroid_dist_km")
        if pc_dist is None or pc_dist <= inner_km:
            continue  # ya summit
        n_far_pre_f63 += 1
        # ¿hay anomaly_pixels dentro del inner?
        aps = r.get("anomaly_pixels") or []
        inner_ap_count = sum(1 for ap in aps if ap.get("dist_km", 999) <= inner_km)
        if inner_ap_count > 0:
            n_reassigned_f63 += 1
        else:
            n_far_post_f63 += 1

    # Records que el dashboard ya NO mostraría como "lago lejos" tras F61+F63:
    # - filtrados por F61: n_filtered_by_f61 (desaparecen)
    # - re-asignados por F63: n_reassigned_f63 (siguen pero pintados en summit, no en lago)
    # n_post_f61_f63 = detecciones reportadas como far residuales = n_far_post_f63

    n_post_f61_f63 = n_post_f61  # mismo conteo de records, solo cambia atribución
    n_far_residual = n_far_post_f63  # los que aún se ven lejanos post ambos fixes

    # F57 (cualitativo): solo Copahue + Llaima. Reduce ~80% de los FPs lago restantes.
    if vol in F57_VOLS:
        # restantes post-F61: n_post_f61. Asumimos los que son lago-residual (NTI cerca del gate
        # pero pasaron por ser >=-0.85) bajan ~80%. Proxy: aplicar 20% retention sobre records
        # con -0.85 <= diag_nti_max < -0.80 (borderline lago-fumarólica débil).
        n_borderline = sum(
            1 for r in rs
            if r.get("vrp_mw", 0) > 0
            and r.get("diag_nti_max") is not None
            and NTI_GATE <= r["diag_nti_max"] < LAVA_LIKE_THR
        )
        n_filtered_by_f57 = int(round(n_borderline * F57_INCREMENTAL_REDUCTION_PCT))
        n_post_f61_f63_f57 = max(0, n_post_f61_f63 - n_filtered_by_f57)
    else:
        n_borderline = 0
        n_filtered_by_f57 = 0
        n_post_f61_f63_f57 = n_post_f61_f63

    # Records "lava-like" preservados (diag_nti_max > -0.80) — control de pérdida
    n_lava_like_total = sum(
        1 for r in rs
        if r.get("vrp_mw", 0) > 0
        and r.get("diag_nti_max") is not None
        and r["diag_nti_max"] > LAVA_LIKE_THR
    )
    # Por construcción F61 con gate -0.85 NO toca records con NTI>-0.80.
    n_lava_like_post_all = n_lava_like_total

    pct_reduc = (
        100.0 * (n_with_vrp - n_post_f61_f63_f57) / n_with_vrp if n_with_vrp else 0.0
    )

    return {
        "volcano": vol,
        "inner_km": inner_km,
        "n_total": n_total,
        "n_with_vrp": n_with_vrp,
        "n_post_f61": n_post_f61,
        "n_filtered_by_f61": n_filtered_by_f61,
        "n_far_pre_f63": n_far_pre_f63,
        "n_reassigned_f63": n_reassigned_f63,
        "n_far_residual": n_far_residual,
        "n_post_f61_f63": n_post_f61_f63,
        "n_borderline_for_f57": n_borderline,
        "n_filtered_by_f57": n_filtered_by_f57,
        "n_post_f61_f63_f57": n_post_f61_f63_f57,
        "n_lava_like_total": n_lava_like_total,
        "n_lava_like_post_all": n_lava_like_post_all,
        "pct_reduccion_total": round(pct_reduc, 1),
    }


def main():
    results_full = []
    results_30d = []
    for vol, inner in TIER_A:
        results_full.append(simulate_volcano(vol, inner, window_30d=False))
        results_30d.append(simulate_volcano(vol, inner, window_30d=True))

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "nti_gate": NTI_GATE,
        "lava_like_threshold": LAVA_LIKE_THR,
        "f57_incremental_pct": F57_INCREMENTAL_REDUCTION_PCT,
        "f57_volcanoes": sorted(F57_VOLS),
        "full_history": results_full,
        "window_30d": results_30d,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    def fmt_row(r):
        return (
            f"{r['volcano']:<22}{r['inner_km']:>4}  "
            f"{r['n_with_vrp']:>6}  "
            f"{r['n_post_f61']:>6}  "
            f"{r['n_post_f61_f63']:>6}  "
            f"{r['n_post_f61_f63_f57']:>6}  "
            f"{r['pct_reduccion_total']:>5.1f}%  "
            f"{r['n_lava_like_post_all']:>5}/{r['n_lava_like_total']:<5}"
        )

    header = (
        f"{'Volcano':<22}{'inn':>4}  {'n_pre':>6}  {'+F61':>6}  "
        f"{'+F63':>6}  {'+F57':>6}  {'red%':>6}  {'lava':>11}"
    )
    print("\n=== HISTORIA COMPLETA (vrp_mw > 0) ===")
    print(header)
    print("-" * len(header))
    for r in results_full:
        print(fmt_row(r))

    print("\n=== VENTANA 30d (vrp_mw > 0) ===")
    print(header)
    print("-" * len(header))
    for r in results_30d:
        print(fmt_row(r))

    total_30d_pre = sum(r["n_with_vrp"] for r in results_30d)
    total_30d_post = sum(r["n_post_f61_f63_f57"] for r in results_30d)
    print(
        f"\nTOTAL 30d: {total_30d_pre} pre → {total_30d_post} post "
        f"(reducción {100.0 * (total_30d_pre - total_30d_post) / max(1, total_30d_pre):.1f}%)"
    )

    print(f"\nResultados crudos: {OUT}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
