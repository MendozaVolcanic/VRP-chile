# -*- coding: utf-8 -*-
"""Reemplaza una ventana de fechas de la serie operacional con los records de un reproceso aislado.

POR QUE (S154): al adoptar K (#850) la historia de `data/mirova_equivalent/` quedo escrita con el detector
anterior. Reprocesarla directo contra la replica (`backfill-tier-a.yml`) toma el grupo `push-main` horas por ola y
deja al NRT esperando. En cambio se reprocesa por trozos en un perfil aislado identico a la replica
(`_s154_reproc_k_historico`, vigilado por tests/test_reproceso_historico_k_s154.py) y este script pasa el
resultado a la serie operacional en un solo commit.

REGLAS, y por que cada una:
- Por clave (datetime_utc, sensor), la misma de `pipeline/store.py`, y solo dentro de [desde, hasta] por la fecha
  de la pasada. Fuera de la ventana no se toca nada: es la parte que el NRT sigue escribiendo.
- Una pasada que esta en la operacional y NO vino en el reproceso se CONSERVA y se informa. El pipeline escribe
  un record por pasada aunque no detecte nada, asi que una pasada ausente es un corte de NASA (A64, A108), no
  «K no la ve»; borrarla perderia un dato. Si son demasiadas (--max-solo-operacional, fraccion por volcan), el
  trozo no se cubrio y el script se niega a escribir: hay que repetir ese trozo.
- `first_processed_utc` se hereda del record operacional como en `store.append_record` (S150): describe cuando
  la pasada se vio por primera vez, no esta version.
- Todo record del reproceso dentro de la ventana debe traer `regimen.perfil` igual al perfil esperado. Asi no se
  puede pasar por K un archivo de otro A/B.
- La marca `regimen` del record queda como la escribio el reproceso (perfil aislado + sha del codigo): dice la
  verdad sobre de donde viene, y el test garantiza que ese perfil resuelve igual que la replica.

Por defecto es un ENSAYO: informa y no escribe. Con --aplicar escribe el archivo operacional.

Uso:
    python scripts/reemplazar_ventana_reproceso.py --operacional data/mirova_equivalent/Villarrica.json \
        --reproceso data/_s154_reproc_k_historico/Villarrica.json --desde 2025-02-15 --hasta 2026-09-17 \
        --perfil-esperado _s154_reproc_k_historico --informe informe.json [--aplicar]
"""
import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _key(r: dict) -> tuple:
    return (r.get("datetime_utc"), r.get("sensor"))


def _en_ventana(r: dict, desde: str, hasta: str) -> bool:
    return desde <= (r.get("datetime_utc") or "")[:10] <= hasta


def reemplazar_ventana(operacional: dict, reproceso: dict, desde: str, hasta: str,
                       perfil_esperado: str) -> tuple[dict, dict]:
    """Devuelve (store nuevo, informe). No modifica las entradas."""
    if operacional.get("volcano") != reproceso.get("volcano"):
        raise ValueError(f"volcanes distintos: {operacional.get('volcano')!r} contra {reproceso.get('volcano')!r}")

    nuevos = {}
    fuera = 0
    for r in reproceso.get("records", []):
        if not _en_ventana(r, desde, hasta):
            fuera += 1
            continue
        perfil = (r.get("regimen") or {}).get("perfil")
        if perfil != perfil_esperado:
            raise ValueError(f"record {_key(r)} del reproceso viene del perfil {perfil!r}, no de {perfil_esperado!r}")
        nuevos[_key(r)] = copy.deepcopy(r)

    salida, reemplazados, solo_op, op_en_ventana = [], 0, [], 0
    for r in operacional.get("records", []):
        if not _en_ventana(r, desde, hasta):
            salida.append(copy.deepcopy(r))
            continue
        op_en_ventana += 1
        k = _key(r)
        if k in nuevos:
            n = nuevos.pop(k)
            if r.get("first_processed_utc"):
                n["first_processed_utc"] = r["first_processed_utc"]
            else:
                n.pop("first_processed_utc", None)
            salida.append(n)
            reemplazados += 1
        else:
            salida.append(copy.deepcopy(r))
            solo_op.append(list(k))
    agregados = len(nuevos)
    salida.extend(nuevos.values())
    salida.sort(key=lambda r: r.get("datetime_utc", ""))

    store = {k: v for k, v in operacional.items() if k != "records"}
    store["records"] = salida
    informe = {
        "volcano": operacional.get("volcano"), "desde": desde, "hasta": hasta,
        "operacional_en_ventana": op_en_ventana, "reemplazados": reemplazados, "agregados": agregados,
        "solo_operacional": len(solo_op), "solo_operacional_claves": solo_op,
        "reproceso_fuera_de_ventana": fuera,
        "records_antes": len(operacional.get("records", [])), "records_despues": len(salida),
    }
    return store, informe


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--operacional", required=True)
    ap.add_argument("--reproceso", required=True)
    ap.add_argument("--desde", required=True, help="YYYY-MM-DD, inclusive")
    ap.add_argument("--hasta", required=True, help="YYYY-MM-DD, inclusive")
    ap.add_argument("--perfil-esperado", required=True)
    ap.add_argument("--informe", required=True, help="JSON con el conteo")
    ap.add_argument("--max-solo-operacional", type=float, default=0.02,
                    help="fraccion maxima de pasadas operacionales de la ventana ausentes del reproceso")
    ap.add_argument("--aplicar", action="store_true", help="escribir el archivo operacional (si no, ensayo)")
    a = ap.parse_args(argv)

    op_path = Path(a.operacional)
    with open(op_path, encoding="utf-8") as f:
        op = json.load(f)
    with open(a.reproceso, encoding="utf-8") as f:
        re_ = json.load(f)
    store, inf = reemplazar_ventana(op, re_, a.desde, a.hasta, a.perfil_esperado)

    frac = inf["solo_operacional"] / inf["operacional_en_ventana"] if inf["operacional_en_ventana"] else 0.0
    inf["fraccion_solo_operacional"] = round(frac, 4)
    inf["max_solo_operacional"] = a.max_solo_operacional
    rehusado = frac > a.max_solo_operacional
    inf["aplicado"] = bool(a.aplicar and not rehusado)
    print(f"{inf['volcano']}: {inf['operacional_en_ventana']} en ventana, {inf['reemplazados']} reemplazados, "
          f"{inf['agregados']} agregados, {inf['solo_operacional']} solo operacional ({frac:.2%}), "
          f"{inf['records_antes']} -> {inf['records_despues']} records")
    if rehusado:
        print(f"REHUSADO: {frac:.2%} de las pasadas de la ventana no vinieron en el reproceso "
              f"(tope {a.max_solo_operacional:.2%}); repetir los trozos faltantes", file=sys.stderr)
    if inf["aplicado"]:
        store["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(op_path, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
    Path(a.informe).write_text(json.dumps(inf, indent=2, ensure_ascii=False), encoding="utf-8")
    return 2 if rehusado else 0


if __name__ == "__main__":
    raise SystemExit(main())
