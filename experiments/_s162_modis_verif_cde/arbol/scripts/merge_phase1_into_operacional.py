"""S32+ — Merge inteligente data A/B Phase 1 → operacional.

Como `mirova_equivalent_test1pix_filter` profile es IDÉNTICO a
`mirova_equivalent` operacional post-S32 (mismas flags incluyendo
enable_test1_pixel_filter:true; difieren solo en data_subdir), los
records 90d producidos por el A/B son exactamente lo que el reproc
operacional intenta generar.

Pero `--overwrite` borraría records FUERA de la ventana 90d (NRT pre o
post). Este script hace merge inteligente:
- Cargar JSON operacional (full history).
- Cargar JSON A/B filter_ON (90d Phase 1).
- Sustituir records 90d (2026-01-29 → 2026-04-29) por los A/B.
- Mantener records fuera de ventana intactos.
- Escribir resultado a operacional.

Identidad de record: (datetime_utc, sensor, granule).

Aplicar a los 11 Tier A. Dry-run por default; --apply para escribir.
"""
from __future__ import annotations
import json, sys, io, argparse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
OPER = ROOT / "data" / "mirova_equivalent"
AB   = ROOT / "data" / "mirova_equivalent_test1pix_filter"

VOLCS = ['Lascar','Lastarria','Tupungatito','Villarrica','PuyehueCordonCaulle',
         'Copahue','NevadosDeChillan','Llaima','Chaiten','PlanchonPeteroa','Isluga']

WINDOW_START = datetime(2026,1,29,0,0,tzinfo=timezone.utc)
WINDOW_END   = datetime(2026,4,29,23,59,59,tzinfo=timezone.utc)


def parse_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M"):
        try: return datetime.strptime(s.split("+")[0], fmt).replace(tzinfo=timezone.utc)
        except ValueError: continue
    return datetime.fromisoformat(s)


def in_window(rec):
    try:
        dt = parse_dt(rec.get('datetime_utc',''))
        return WINDOW_START <= dt <= WINDOW_END
    except Exception:
        return False


def record_key(rec):
    """Identidad: (datetime_utc, sensor, granule). Granule incluido para
    desambiguar pasadas múltiples del mismo sensor en mismo timestamp."""
    return (rec.get('datetime_utc',''), rec.get('sensor',''), rec.get('granule',''))


def merge_volcano(vol, apply=False):
    f_oper = OPER / f"{vol}.json"
    f_ab   = AB / f"{vol}.json"
    if not f_oper.exists():
        print(f"  ❌ {vol}: operacional no existe"); return
    if not f_ab.exists():
        print(f"  ⚠️  {vol}: A/B no existe — skip"); return

    oper = json.loads(f_oper.read_text(encoding='utf-8'))
    ab   = json.loads(f_ab.read_text(encoding='utf-8'))
    oper_recs = oper.get('records', [])
    ab_recs   = ab.get('records', [])

    # Records operacionales fuera de ventana 90d (preservar)
    out_window = [r for r in oper_recs if not in_window(r)]
    # Records operacionales DENTRO de ventana (a sustituir por A/B)
    in_window_oper = [r for r in oper_recs if in_window(r)]

    # A/B records — todos en ventana 90d (lo que sustituye)
    # En caso de records A/B fuera de ventana (no debería pasar), filtramos
    in_window_ab = [r for r in ab_recs if in_window(r)]

    # Merge: preservar fuera de ventana + reemplazar dentro de ventana con A/B
    new_recs = out_window + in_window_ab

    # Sort por datetime_utc para mantener orden cronológico
    def sort_key(r):
        try: return parse_dt(r.get('datetime_utc',''))
        except: return datetime.min.replace(tzinfo=timezone.utc)
    new_recs.sort(key=sort_key)

    # Stats
    n_oper_total = len(oper_recs)
    n_ab_total   = len(ab_recs)
    n_out = len(out_window)
    n_in_oper = len(in_window_oper)
    n_in_ab   = len(in_window_ab)
    n_final   = len(new_recs)

    # Comparar VRP por record en ventana (sample)
    print(f"  {vol}: oper={n_oper_total}, A/B={n_ab_total} | out_window={n_out}, "
          f"in_window oper={n_in_oper} → ab={n_in_ab} | final={n_final}")

    if apply:
        # Preservar metadata top-level (volcano name, lat/lon, etc.)
        oper['records'] = new_recs
        # Update timestamp
        oper['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        f_oper.write_text(json.dumps(oper, indent=2), encoding='utf-8')
        print(f"    ✓ {vol} escrito ({n_final} records)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Escribir cambios (default dry-run)")
    args = ap.parse_args()

    print(f"# Merge Phase 1 A/B → operacional")
    print(f"Ventana: {WINDOW_START.date()} → {WINDOW_END.date()}")
    print(f"Modo: {'APPLY' if args.apply else 'DRY-RUN'}\n")

    for vol in VOLCS:
        merge_volcano(vol, apply=args.apply)

    if not args.apply:
        print(f"\n(Dry run. Re-ejecutar con --apply para escribir cambios.)")
    else:
        print(f"\n✓ Merge completado.")


if __name__ == "__main__":
    main()
