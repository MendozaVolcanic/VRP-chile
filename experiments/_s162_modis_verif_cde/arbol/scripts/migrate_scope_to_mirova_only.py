"""migrate_scope_to_mirova_only.py — S15 Tema E cleanup scope.

Limpia `data/mirova_equivalent/` dejando solo los 11 volcanes que MIROVA
efectivamente monitorea (Tier A). Mueve los otros 34 a `data/experimental/`
para que cuando se active el perfil experimental, sigan procesandose alli.

Tambien imprime los cambios propuestos a volcanoes.yaml:
  - Agregar `mirova_monitored: true` a los 11.
  - Agregar `mirova_monitored: false` a los 34 restantes.

Uso:
  python scripts/migrate_scope_to_mirova_only.py [--dry-run]
"""

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
MIROVA_MONITORED = {
    "Lascar", "Chaiten", "Villarrica", "Copahue", "Isluga", "Lastarria",
    "Llaima", "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
    "Tupungatito",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src_dir = ROOT / "data" / "mirova_equivalent"
    dst_dir = ROOT / "data" / "experimental"
    dst_dir.mkdir(parents=True, exist_ok=True)

    to_move = []
    to_keep = []
    for jf in sorted(src_dir.glob("*.json")):
        if jf.stem in MIROVA_MONITORED:
            to_keep.append(jf)
        else:
            to_move.append(jf)

    print(f"{'DRY RUN' if args.dry_run else 'APPLIED'}")
    print(f"Keeping in data/mirova_equivalent/: {len(to_keep)} volcanes MIROVA-monitoreados")
    for f in to_keep:
        print(f"  KEEP {f.name}")
    print()
    print(f"Moving to data/experimental/: {len(to_move)} volcanes no-MIROVA")
    for f in to_move:
        dst = dst_dir / f.name
        print(f"  MOVE {f.name} -> data/experimental/")
        if not args.dry_run:
            shutil.move(str(f), str(dst))
    print()
    print(f"Total records moved: {sum(1 for _ in to_move)} files")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
