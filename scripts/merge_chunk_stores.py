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


def _en_alguna(fecha: str, ventanas) -> bool:
    return any(v[0] <= fecha <= v[1] for v in ventanas)


def merge_stores(paths: list[Path], ventanas: list[tuple[str, str]] | None = None,
                 base: dict | None = None) -> tuple[dict, int]:
    """Devuelve (store unido, n_duplicados). Orden estable por datetime_utc.

    `base`: store que el destino ya tiene; ver el docstring del modulo."""
    if base is not None and ventanas is None:
        raise ValueError("--base exige --ventanas")
    merged: dict[tuple, dict] = {}
    volcano = ""
    updated = ""
    duplicados = 0
    if base is not None:
        volcano = base.get("volcano") or ""
        updated = base.get("updated", "") or ""
        conservados = reemplazados = 0
        for rec in base.get("records", []):
            # POR QUE se descarta lo de dentro aunque el trozo no lo traiga: el
            # trozo reproceso ese tramo entero, y una pasada que ya no sale es
            # parte de su resultado. Lo de fuera nadie lo toco en esta corrida.
            if _en_alguna((rec.get("datetime_utc") or "")[:10], ventanas):
                reemplazados += 1
                continue
            merged[_key(rec)] = rec
            conservados += 1
        print(f"  base: {conservados} records conservados fuera de las ventanas, "
              f"{reemplazados} dentro (los reemplaza la corrida)")
    # Se procesan en orden de `updated` ascendente para que, ante un choque,
    # el store escrito más tarde sea el que sobrescriba.
    cargados = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            cargados.append((json.load(f), p))
    cargados.sort(key=lambda t: t[0].get("updated", ""))

    # ventana por archivo (misma posicion que en `paths`), si se declararon
    vent_por_path = dict(zip([str(x) for x in paths], ventanas or []))

    for store, p in cargados:
        if (base is not None and volcano and store.get("volcano")
                and store["volcano"] != volcano):
            raise ValueError(f"la base es de {volcano!r} y {p} de {store['volcano']!r}")
        volcano = store.get("volcano") or volcano
        updated = max(updated, store.get("updated", ""))
        v = vent_por_path.get(str(p))
        n = fuera = 0
        for rec in store.get("records", []):
            # Un trozo aporta SOLO lo de SU ventana. Sin esto, el archivo que
            # el job subio (completo, con los otros meses en su version vieja)
            # resucita records que otro trozo acaba de reprocesar. Ver el
            # comentario del workflow: paso de verdad en S124.
            if v is not None:
                f = (rec.get("datetime_utc") or "")[:10]
                if not (v[0] <= f <= v[1]):
                    fuera += 1
                    continue
            k = _key(rec)
            if k in merged:
                duplicados += 1
            merged[k] = rec
            n += 1
        extra = f"  (+{fuera} fuera de su ventana {v[0]}..{v[1]}, ignorados)" if v else ""
        print(f"  {p}: {n} records{extra}")

    records = sorted(merged.values(), key=lambda r: r.get("datetime_utc") or "")
    if base is not None:
        # mismas claves y en el mismo orden que la base: si la corrida no cambia
        # nada, el archivo sale identico byte a byte
        out = dict(base)
        out.update({"volcano": volcano, "updated": updated, "records": records})
        return out, duplicados
    return {"volcano": volcano, "updated": updated, "records": records}, duplicados


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="JSON de salida")
    ap.add_argument("--ventanas", nargs="*", default=None, metavar="INI:FIN",
                    help="ventana de cada trozo, en el MISMO orden que inputs "
                         "(ej. 2026-05-01:2026-05-30). Con esto, cada trozo "
                         "aporta solo sus records: sin ellas, el archivo "
                         "completo que subio el job resucita meses viejos.")
    ap.add_argument("--base", default=None,
                    help="JSON que el destino ya tiene (S157): se conservan sus "
                         "records fuera de las ventanas. Exige --ventanas. Si "
                         "no existe, es como no pasarlo.")
    ap.add_argument("inputs", nargs="+", help="JSON de cada trozo")
    args = ap.parse_args(argv)

    paths_raw = args.inputs
    vent_raw = args.ventanas
    if vent_raw is not None and len(vent_raw) != len(paths_raw):
        print(f"ERROR: {len(vent_raw)} ventanas para {len(paths_raw)} trozos",
              file=sys.stderr)
        return 1
    existe = [Path(p).exists() for p in paths_raw]
    paths = [Path(p) for p, e in zip(paths_raw, existe) if e]
    ventanas = ([tuple(v.split(":")) for v, e in zip(vent_raw, existe) if e]
                if vent_raw is not None else None)
    faltantes = [p for p, e in zip(paths_raw, existe) if not e]
    for p in faltantes:
        print(f"AVISO: falta {p} (trozo sin resultado)", file=sys.stderr)
    if not paths:
        print("ERROR: ningún trozo aportó JSON", file=sys.stderr)
        return 1

    base = None
    if args.base is not None:
        if vent_raw is None:
            print("ERROR: --base exige --ventanas (sin ellas no se sabe que "
                  "tramo cubre la corrida)", file=sys.stderr)
            return 1
        if Path(args.base).exists():
            with open(args.base, "r", encoding="utf-8") as f:
                base = json.load(f)
        else:
            print(f"AVISO: no existe la base {args.base}; se une sin base",
                  file=sys.stderr)

    print(f"Uniendo {len(paths)} trozos:")
    try:
        store, duplicados = merge_stores(paths, ventanas, base)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)

    print(f"-> {out}: {len(store['records'])} records "
          f"({duplicados} duplicados resueltos, {len(faltantes)} trozos faltantes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
