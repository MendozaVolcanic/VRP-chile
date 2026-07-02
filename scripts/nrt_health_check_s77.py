"""S77 NRT health check — verificar que F46+F47 fixes funcionan post-merge.

Script de auditoría rápida (~5-10 segundos) sobre `data/mirova_equivalent/`
para confirmar que los próximos ciclos de NRT cron están aplicando los
fixes mergeados S77:

- **F47 H4** (PR #175, sha 34b74f20): records nuevos con cluster cerca del
  vent pero hotspot single lejano deben tener `final_hotspot_source ==
  "cluster_rescue"` y `discarded_reason == "single_pixel_far_overridden_by_cluster"`.
  Antes del fix esto NO existía.

- **F46 A+B** (PR #177, sha a80807f0): records nuevos VIIRS I-band NO deben
  tener `vrp_tir_mw > 1000 MW` con `n_anomalous_pixels == 0` (caso Chaitén
  patognomónico que el gate consistencia veta por construcción).

Uso:
    python scripts/nrt_health_check_s77.py [--days 1] [--quiet]

Salida (stdout):
- Tabla por volcán Tier A: n_records últimos N días, n_rescued, max vrp_mw,
  count F46-susp post-fix (esperado ~0 en records nuevos).
- Verdict por bug:
  * F47: PASS si hay ≥1 record con source='cluster_rescue' en ventana
    (signo de que el fix se activó), o INDETERMINATE si no había records
    elegibles para rescate (volcanes quietos).
  * F46: PASS si count F46-susp en records últimas N días == 0.
    FAIL si >0 records nuevos siguen mostrando el patrón.

Exit code:
- 0 si todos los volcanes Tier A están healthy (NRT alive + fixes activos).
- 1 si algún FAIL (F46 sigue produciendo espurios).
- 2 si NRT mute (sin records nuevos en N días → cron caído).

Refs:
- PR #175 F47 H4 fix
- PR #177 F46 A+B fix
- experiments/138_audit_mw_outliers_s76 (baseline pre-fix F46)
- experiments/141_f47_h4_rootcause (baseline pre-fix F47)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# stdout Windows default cp1252 no imprime Unicode (regla encoding del proyecto);
# reconfigure no re-envuelve el stream (patrón S118 analyze.py).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


TIER_A = (
    "Chaiten",
    "Copahue",
    "Isluga",
    "Lascar",
    "Lastarria",
    "Llaima",
    "NevadosDeChillan",
    "PlanchonPeteroa",
    "PuyehueCordonCaulle",
    "Tupungatito",
    "Villarrica",
)
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "mirova_equivalent"


def _parse_iso(s: str) -> datetime | None:
    """Parse ISO o 'YYYY-MM-DD HH:MM' del schema VRP. None si falla."""
    if not s:
        return None
    try:
        if " " in s and "T" not in s:
            s = s.replace(" ", "T")
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _is_f46_susp(r: dict) -> bool:
    """Patrón F46 susp: vrp_tir_mw alto + MIR/anomaly = 0. Post-fix esperado 0."""
    return (
        (r.get("vrp_tir_mw") or 0) > 1000
        and (r.get("vrp_mir_mw") or 0) < 10
        and (r.get("n_anomalous_pixels") or 0) <= 0
    )


def _is_f47_rescued(r: dict) -> bool:
    """Record rescatado por F47 fix (signo de que el fix se activó)."""
    return r.get("final_hotspot_source") == "cluster_rescue"


def analyze_volcano(name: str, days: int) -> dict:
    """Análisis de un volcán Tier A. Devuelve dict con métricas."""
    path = DATA_DIR / f"{name}.json"
    out = {"volcano": name, "n_total": 0, "n_window": 0,
           "n_f47_rescued": 0, "n_f46_susp": 0,
           "max_vrp_mw": 0.0, "latest_record_utc": None,
           "status": "no_data"}
    if not path.exists():
        return out

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        out["status"] = f"parse_error: {e}"
        return out

    records = data.get("records", [])
    out["n_total"] = len(records)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    in_window = []
    latest = None
    for r in records:
        dt = _parse_iso(r.get("datetime_utc"))
        if dt is None:
            continue
        if latest is None or dt > latest:
            latest = dt
        if dt >= cutoff:
            in_window.append(r)

    out["latest_record_utc"] = latest.isoformat() if latest else None
    out["n_window"] = len(in_window)

    if not in_window:
        out["status"] = "muted"
        return out

    out["n_f47_rescued"] = sum(1 for r in in_window if _is_f47_rescued(r))
    out["n_f46_susp"] = sum(1 for r in in_window if _is_f46_susp(r))
    out["max_vrp_mw"] = max((r.get("vrp_mw") or 0) for r in in_window)
    out["status"] = "alive"
    return out


def verdict_overall(results: list[dict], days: int) -> dict:
    """Veredictos finales F46/F47 + NRT alive."""
    alive_count = sum(1 for r in results if r["status"] == "alive")
    muted_count = sum(1 for r in results if r["status"] == "muted")
    nodata_count = sum(1 for r in results if r["status"] == "no_data")
    # S120 (cacería de bugs): un JSON corrupto (escenario race A47) caía en un
    # bucket que nadie contaba → "Health check OK" con data rota.
    parse_err_count = sum(
        1 for r in results if str(r["status"]).startswith("parse_error"))

    nrt = "PASS" if alive_count >= 6 else ("PARTIAL" if alive_count > 0 else "FAIL")

    total_f47 = sum(r["n_f47_rescued"] for r in results)
    if total_f47 > 0:
        f47 = "PASS — fix activo, {} record(s) rescatado(s)".format(total_f47)
    else:
        f47 = ("INDETERMINATE — sin records elegibles para rescate en ventana "
               "{}d (volcanes quietos o NRT corto)".format(days))

    total_f46 = sum(r["n_f46_susp"] for r in results)
    if total_f46 == 0:
        f46 = "PASS — 0 records F46-susp en ventana {}d".format(days)
    else:
        f46 = "FAIL — {} record(s) F46-susp en ventana {}d (revisar)".format(total_f46, days)

    return {
        "nrt_alive": nrt,
        "f47_fix": f47,
        "f46_fix": f46,
        "alive": alive_count,
        "muted": muted_count,
        "no_data": nodata_count,
        "parse_errors": parse_err_count,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=1,
                   help="Ventana hacia atras en dias (default 1 = ultimos 24h).")
    p.add_argument("--quiet", action="store_true",
                   help="Solo imprime verdict final + exit code.")
    args = p.parse_args()

    if not DATA_DIR.exists():
        print(f"ERROR: no encuentro {DATA_DIR}", file=sys.stderr)
        return 2

    results = [analyze_volcano(v, args.days) for v in TIER_A]
    v = verdict_overall(results, args.days)

    if not args.quiet:
        print()
        print(f"=== NRT health check S77 — ventana {args.days}d ===\n")
        print(f"{'Volcan':<22} {'n_total':>8} {'n_win':>6} {'rescued':>8} "
              f"{'F46susp':>8} {'max_vrp':>9}  status")
        for r in results:
            print(f"{r['volcano']:<22} {r['n_total']:>8} {r['n_window']:>6} "
                  f"{r['n_f47_rescued']:>8} {r['n_f46_susp']:>8} "
                  f"{r['max_vrp_mw']:>9.2f}  {r['status']}")
        print()
        print(f"NRT alive : {v['nrt_alive']}  "
              f"(alive={v['alive']}, muted={v['muted']}, no_data={v['no_data']})")
        print(f"F47 fix   : {v['f47_fix']}")
        print(f"F46 fix   : {v['f46_fix']}")
        print()

    if v["parse_errors"] > 0:
        print(f"[EXIT 2] {v['parse_errors']} JSON con parse error (posible race "
              "A47 — restaurar con git checkout origin/main -- <archivo>).",
              file=sys.stderr)
        return 2
    if v["nrt_alive"] == "FAIL":
        print("[EXIT 2] NRT mute — 0 volcanes con records en ventana.", file=sys.stderr)
        return 2
    if v["f46_fix"].startswith("FAIL"):
        print("[EXIT 1] F46 fix produciendo records susp en ventana.", file=sys.stderr)
        return 1
    print("[EXIT 0] Health check OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
