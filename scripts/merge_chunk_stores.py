# -*- coding: utf-8 -*-
"""Une los JSON de un reproceso partido en trozos de fechas.

POR QUÉ: un reproceso largo no cabe en un job de GitHub Actions (6 h duras).
Al partirlo por ventanas, cada trozo corre en paralelo sobre su propio
checkout y produce el JSON del volcán con SOLO sus fechas. Si cada trozo
hiciera su propio `git push`, volveríamos a la carrera documentada en S25
(`pull --rebase -X theirs` puede descartar records del commit anterior).
Este script hace la unión off-line para que haya UN solo push al final.

La clave de identidad de un record es la misma que usa `pipeline/store.py`:
(datetime_utc, sensor) — una pasada de un sensor sobre el volcán. Los trozos
no se solapan, así que la unión no debería encontrar duplicados; si los
encuentra (por un relanzamiento parcial), gana el más reciente por `updated`
del store que lo trae, y se informa cuántos hubo.

Uso:
    python scripts/merge_chunk_stores.py --out data/<perfil>/<Vol>.json \
        chunk1/<Vol>.json chunk2/<Vol>.json ...
"""
import argparse
import json
import sys
from pathlib import Path


def _key(record: dict) -> tuple:
    return (record.get("datetime_utc"), record.get("sensor"))


def merge_stores(paths: list[Path]) -> tuple[dict, int]:
    """Devuelve (store unido, n_duplicados). Orden estable por datetime_utc."""
    merged: dict[tuple, dict] = {}
    volcano = ""
    updated = ""
    duplicados = 0
    # Se procesan en orden de `updated` ascendente para que, ante un choque,
    # el store escrito más tarde sea el que sobrescriba.
    cargados = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            cargados.append((json.load(f), p))
    cargados.sort(key=lambda t: t[0].get("updated", ""))

    for store, p in cargados:
        volcano = store.get("volcano") or volcano
        updated = max(updated, store.get("updated", ""))
        n = 0
        for rec in store.get("records", []):
            k = _key(rec)
            if k in merged:
                duplicados += 1
            merged[k] = rec
            n += 1
        print(f"  {p}: {n} records")

    records = sorted(merged.values(), key=lambda r: r.get("datetime_utc", ""))
    return {"volcano": volcano, "updated": updated, "records": records}, duplicados


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="JSON de salida")
    ap.add_argument("inputs", nargs="+", help="JSON de cada trozo")
    args = ap.parse_args(argv)

    paths = [Path(p) for p in args.inputs if Path(p).exists()]
    faltantes = [p for p in args.inputs if not Path(p).exists()]
    for p in faltantes:
        print(f"AVISO: falta {p} (trozo sin resultado)", file=sys.stderr)
    if not paths:
        print("ERROR: ningún trozo aportó JSON", file=sys.stderr)
        return 1

    print(f"Uniendo {len(paths)} trozos:")
    store, duplicados = merge_stores(paths)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)

    print(f"-> {out}: {len(store['records'])} records "
          f"({duplicados} duplicados resueltos, {len(faltantes)} trozos faltantes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
