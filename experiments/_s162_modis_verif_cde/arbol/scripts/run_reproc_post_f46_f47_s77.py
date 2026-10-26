"""S77 reproc histórico 11 Tier A post-fixes F46 + F47 (PR #175 + #177).

Wrapper sobre `scripts/run_pipeline.py --profile mirova_equivalent` para
reprocesar la ventana histórica de los 11 volcanes Tier A con el código
actual de main (post-F46 gate consistencia TIR + post-F47 cluster rescate).

**Por qué este script existe**:

NRT cron (cada 2h) aplica los fixes a records NUEVOS. Pero los records
históricos en `data/mirova_equivalent/<Volcano>.json` ya fueron procesados
por código viejo y siguen mostrando:
- F46: `vrp_tir_mw` espurios (143 records 1 000-9 606 MW por Stefan-Boltzmann
  sobre 4σ-mask sin gate MIR).
- F47: `vrp_mw=0` con cluster válido cerca (~400 records, sobre todo PCC 110,
  Copahue 79, Villarrica 59, Chaitén 49, NdC 33).

Reproc local con código actual = sobreescribe esos records con valores
correctos. El dashboard absorbe automáticamente porque lee los JSONs.

**Por qué local y no GH Actions** (regla S15):

11 volcanes × 30-90 días × 1-3 granules/día × 5-15 min/granule
≈ 8-30 horas máquina. GH Actions free tier corta a 50 min/step. Local
entra (Windows + Python 3.12 + pyhdf via .whl manual desde S46).

**Caveat operacional importante**:

- Reproc **sobreescribe** `data/mirova_equivalent/<Volcano>.json` directamente.
  Pre-reproc convien hacer backup: `cp -r data/mirova_equivalent data/mirova_equivalent.pre_s77`.
- Mientras corre, el NRT cron también puede escribir. **Pausar cron**
  durante el reproc o usar `--no-overwrite` (TBD: check si run_pipeline lo soporta).
  Para reproc corto (30d) puede no valer la pena pausar; para 90d sí.

Uso:
    # 30 días (default), 11 Tier A, modo dry-run primero
    python scripts/run_reproc_post_f46_f47_s77.py --dry-run

    # Ventana corta (14d) para confirmar fixes funcionan antes de full
    python scripts/run_reproc_post_f46_f47_s77.py --days 14

    # Full 90d para regenerar histórico que el dashboard muestra
    python scripts/run_reproc_post_f46_f47_s77.py --days 90

    # Subset de volcanes para test
    python scripts/run_reproc_post_f46_f47_s77.py --volcanoes NevadosDeChillan PuyehueCordonCaulle

Validación post-reproc:
- Comparar count `vrp_tir_mw > 1000` pre vs post (esperado: drop ≥95%).
- Comparar count `vrp_mw == 0 AND primary_cluster.vrp_mw > 0` pre vs post
  (esperado: ~400 records pasan a vrp_mw > 0 con final_hotspot_source='cluster_rescue').
- Re-correr `experiments/139_recall_precision_s76/audit.py` y verificar
  NdC recall 0.20 → 0.60-0.80.

Refs:
- PR #175 (F47 H4 fix Opción A)
- PR #177 (F46 A+B fix)
- experiments/138_audit_mw_outliers_s76/ (baseline pre-fix F46)
- experiments/141_f47_h4_rootcause/ (baseline pre-fix F47)
- docs/F46_AB_TEST_PLAN.md
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


# Los 11 Tier A en orden alfabético (mismo que volcanoes.yaml mirova_monitored=true).
DEFAULT_TIER_A = (
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
PROFILE = "mirova_equivalent"
REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_PIPELINE = REPO_ROOT / "scripts" / "run_pipeline.py"


def build_command(volcano: str, start: str, end: str) -> list[str]:
    return [
        sys.executable, str(RUN_PIPELINE),
        "--profile", PROFILE,
        "--volcano", volcano,
        "--start", start,
        "--end", end,
    ]


def main() -> int:
    p = argparse.ArgumentParser(
        description="S77 reproc histórico post-F46+F47 — wrapper local 11 Tier A.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--days", type=int, default=30,
                   help="Ventana hacia atras desde hoy en dias (default 30).")
    p.add_argument("--volcanoes", nargs="+", default=list(DEFAULT_TIER_A),
                   help="Subset de volcanes a reprocesar (default los 11 Tier A).")
    p.add_argument("--dry-run", action="store_true",
                   help="Solo imprime los comandos.")
    p.add_argument("--continue-on-error", action="store_true",
                   help="Si un volcan falla, sigue con los demas (default: stop).")
    args = p.parse_args()

    end = date.today()
    start = end - timedelta(days=args.days)
    start_s = start.isoformat()
    end_s = end.isoformat()

    print()
    print(f"[S77 reproc] Profile           : {PROFILE}")
    print(f"[S77 reproc] Output sobreescribe: data/{PROFILE}/<Volcano>.json")
    print(f"[S77 reproc] Ventana            : {start_s} -> {end_s} ({args.days} dias)")
    print(f"[S77 reproc] Volcanes           : {len(args.volcanoes)} -> {', '.join(args.volcanoes)}")
    print(f"[S77 reproc] Dry-run            : {args.dry_run}")
    print()
    print("[S77 reproc] CAVEAT: sobreescribe JSONs operacionales. Backup recomendado:")
    print("  Windows : robocopy data\\mirova_equivalent data\\mirova_equivalent.pre_s77 /E")
    print("  POSIX   : cp -r data/mirova_equivalent data/mirova_equivalent.pre_s77")
    print()
    print("[S77 reproc] CAVEAT: NRT cron puede escribir en paralelo. Considerar")
    print("            pausar el workflow durante el reproc si ventana >30d.")
    print()

    if not RUN_PIPELINE.exists():
        print(f"ERROR: no encuentro {RUN_PIPELINE}", file=sys.stderr)
        return 2

    failures: list[tuple[str, int]] = []
    for i, vol in enumerate(args.volcanoes, 1):
        cmd = build_command(vol, start_s, end_s)
        print(f"--- [{i}/{len(args.volcanoes)}] {vol} ---")
        print("  " + " ".join(cmd))
        if args.dry_run:
            continue
        rc = subprocess.call(cmd, cwd=str(REPO_ROOT))
        if rc != 0:
            print(f"  [FAIL] {vol} -> exit {rc}")
            failures.append((vol, rc))
            if not args.continue_on_error:
                print(f"  [STOP] --continue-on-error no especificado. Abortando.")
                break
        else:
            print(f"  [OK]   {vol}")
        print()

    if args.dry_run:
        print("\n[S77 reproc] dry-run, ningun pipeline corrido.")
        return 0

    print("\n[S77 reproc] Resumen:")
    print(f"  exito : {len(args.volcanoes) - len(failures)} / {len(args.volcanoes)}")
    for vol, rc in failures:
        print(f"  fail  : {vol} (exit {rc})")

    if failures:
        return 1

    print()
    print("[S77 reproc] Post-reproc validacion sugerida:")
    print("  1. Audit MW outliers post-fix (esperado drop >=95% en vrp_tir_mw>1000):")
    print("     python experiments/138_audit_mw_outliers_s76/audit2.py")
    print("  2. Audit recall/precision F47 (esperado NdC 0.20 -> 0.60-0.80):")
    print("     python experiments/139_recall_precision_s76/audit.py")
    print("  3. Dashboard: refrescar y verificar Llaima/Copahue/NdC con VRP visible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
