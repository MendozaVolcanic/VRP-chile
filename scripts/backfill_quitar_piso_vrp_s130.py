"""S130 · Devuelve el VRP a los records que el piso habia puesto en cero.

POR QUE: quitar el piso del perfil (mirova_equivalent.yaml, S130) solo afecta a
records NUEVOS — los ya persistidos conservan el cero escrito por store.py. Este
script los restaura sin reprocesar.

La restauracion es EXACTA, no una estimacion: el propio store.py guardaba el
valor crudo en `diag_vrp_raw_mw` antes de pisarlo. No hay reseleccion de cluster
de por medio (el piso es un post-proceso sobre un numero ya calculado), asi que
A18 —"el preview offline no predice la seleccion real"— no aplica aca.

Deja rastro de la operacion en `diag_vrp_floor_removed_s130: true` para que una
auditoria posterior pueda separar estos records de los que nunca se pisaron.

A47: NUNCA correr en paralelo sobre data/mirova_equivalent/. Este script es
secuencial a proposito, un archivo a la vez, con escritura atomica via .tmp.

Uso:
    python scripts/backfill_quitar_piso_vrp_s130.py --dry-run
    python scripts/backfill_quitar_piso_vrp_s130.py
"""
import argparse
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="cuenta y reporta sin escribir nada")
    ap.add_argument("--data-dir", default=DATA)
    args = ap.parse_args()

    archivos = sorted(f for f in os.listdir(args.data_dir) if f.endswith(".json"))
    total_rest = 0
    por_vol = {}
    por_sensor = defaultdict(int)

    for nombre in archivos:
        path = os.path.join(args.data_dir, nombre)
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] {nombre}: {e}", file=sys.stderr)
            return 1

        recs = doc.get("records") if isinstance(doc, dict) else doc
        if not recs:
            continue

        n = 0
        for r in recs:
            raw = r.get("diag_vrp_raw_mw")
            if raw is None:
                continue
            # Idempotente: si ya se restauro, no volver a tocar.
            if r.get("diag_vrp_floor_removed_s130"):
                continue
            if (r.get("vrp_mw") or 0) != 0:
                # El piso solo escribe cero; si hay valor, esto no es un pisado
                # pendiente (o alguien ya lo toco). No adivinar: se deja igual.
                continue
            r["vrp_mw"] = raw
            r["diag_vrp_floor_removed_s130"] = True
            n += 1
            por_sensor[r.get("sensor", "?")] += 1

        if n:
            por_vol[nombre[:-5]] = n
            total_rest += n
            if not args.dry_run:
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    # MISMO formato que store.py:212 (indent=2, ASCII escapado).
                    # Escribirlo de otra forma reformatea el archivo entero y
                    # produce un diff de millones de lineas por un cambio de
                    # 1.634 valores — pasó en el primer intento de este script.
                    json.dump(doc, fh, indent=2)
                os.replace(tmp, path)

    modo = "DRY-RUN (no se escribio nada)" if args.dry_run else "ESCRITO"
    print(f"=== backfill piso VRP S130 — {modo} ===")
    print(f"records restaurados: {total_rest}")
    print("\npor volcan:")
    for v, n in sorted(por_vol.items(), key=lambda kv: -kv[1]):
        print(f"  {v:26s} {n:5d}")
    print("\npor sensor:")
    for s, n in sorted(por_sensor.items(), key=lambda kv: -kv[1]):
        print(f"  {s:26s} {n:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
