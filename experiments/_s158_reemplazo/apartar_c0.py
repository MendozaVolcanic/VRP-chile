# -*- coding: utf-8 -*-
"""Aparta de la serie publicada los records del detector anterior (C0) que quedan dentro de la serie K (S158).

POR QUE. Tras el reemplazo del historico con K quedan pasadas sin reprocesar porque NASA no tiene el archivo: 64 de
Suomi NPP del 2026-08-05 y 06 (ni NRT ni estandar en CMR) y 26 de MODIS Terra que el NRT escribio con C0 antes de la
adopcion y que el reproceso de 30 dias no reemplazo (sin estandar de Terra). El detector anterior publicaba en 85 a
88 % de las pasadas en que MIROVA no vio nada; sin marca, 25 de las de agosto publican juntas en dos pasadas del
2026-08-06 en 8 volcanes, un pulso que es el detector y no los volcanes. Nicolas decidio el 2026-10-21 sacarlas a un
archivo aparte, sin borrar nada (`tasks/LOOP_OBJETIVOS.md`, entrada S158).

Que hace, por volcan Tier A: mueve a `data/_c0_residuales/<Volcan>.json` todo record de
`data/mirova_equivalent/<Volcan>.json` con fecha de pasada desde `--desde` y sin `regimen.codigo_sha`. Si el archivo de
residuos ya existe, une por clave (datetime_utc, sensor) y no duplica. Escribe con `json.dump(indent=2)`, como
`pipeline/store.py`, para que el diff sea solo de los records movidos. Sin `--aplicar` solo informa.

Uso (desde la raiz del repo):
    python experiments/_s158_reemplazo/apartar_c0.py --desde 2025-02-15 [--aplicar]
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "data" / "mirova_equivalent"
RESIDUOS = RAIZ / "data" / "_c0_residuales"
TIER_A = ["Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
          "Villarrica", "PuyehueCordonCaulle", "Chaiten", "Isluga"]
MOTIVO = ("Records del detector anterior (C0) que quedaban dentro de la serie K y no se pudieron reprocesar porque "
          "NASA no tiene el archivo (Suomi NPP 2026-08-03 a 08-06 sin NRT ni estandar en CMR; MODIS Terra sin "
          "estandar para el reproceso de 30 dias). Apartados de la serie publicada por decision de Nicolas del "
          "2026-10-21 para que el tablero no mezcle detectores; se conservan aca sin cambios. "
          "Guard: tests/test_guard_serie_k_pura_s158.py.")


def es_k(r: dict) -> bool:
    return bool((r.get("regimen") or {}).get("codigo_sha"))


def clave(r: dict) -> tuple:
    return (r.get("datetime_utc"), r.get("sensor"))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", required=True, help="fecha de pasada (AAAA-MM-DD) desde la que la serie es K")
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    total = 0
    for v in TIER_A:
        p = DATOS / f"{v}.json"
        store = json.loads(p.read_text(encoding="utf-8"))
        recs = store.get("records", [])
        fuera = [r for r in recs if (r.get("datetime_utc") or "")[:10] >= a.desde and not es_k(r)]
        total += len(fuera)
        print(f"{v:20s} {len(recs):6d} records, {len(fuera):3d} C0 desde {a.desde}: "
              f"{sorted({(clave(r)[0] or '')[:10] + ' ' + str(r.get('sensor')) for r in fuera})}")
        if not a.aplicar or not fuera:
            continue
        rp = RESIDUOS / f"{v}.json"
        previo = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else {"volcano": v, "records": []}
        por_clave = {clave(r): r for r in previo["records"]}
        for r in fuera:
            por_clave[clave(r)] = r
        previo.update({"volcano": v, "motivo": MOTIVO,
                       "records": sorted(por_clave.values(), key=lambda r: (r.get("datetime_utc"), r.get("sensor")))})
        RESIDUOS.mkdir(parents=True, exist_ok=True)
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(previo, f, indent=2)
        sacar = {clave(r) for r in fuera}
        store["records"] = [r for r in recs if clave(r) not in sacar]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
    print(f"total C0 desde {a.desde}: {total}{' (apartados)' if a.aplicar else ' (ensayo, nada escrito)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
