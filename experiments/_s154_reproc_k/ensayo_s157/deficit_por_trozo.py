# -*- coding: utf-8 -*-
"""Las pasadas que el reproceso no trajo, por trozo y por producto de origen del record operacional.

POR QUE (S157): una pasada que falta en el reproceso queda en C0 tras el reemplazo. Si el record operacional se
escribio con producto `nrt` (LANCE), puede que el producto estandar no exista (caso de Terra en la tarea 1.27) y
repetir el trozo no la traiga; si es `standard`, el granulo existia y repetir el trozo deberia traerla. Lee
`cobertura.json` (de `cobertura.py`) y la serie operacional.

Uso (desde la raiz del repo): python experiments/_s154_reproc_k/ensayo_s157/deficit_por_trozo.py
Salida: deficit_por_trozo.md
"""
import json
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
AQUI = Path(__file__).resolve().parent


def main() -> int:
    cob = json.loads((AQUI / "cobertura.json").read_text(encoding="utf-8"))
    ventanas = {t["idx"]: (t["start"], t["end"]) for t in cob["trozos"]}
    tabla = defaultdict(lambda: defaultdict(lambda: {"nrt": 0, "standard": 0, "otro": 0}))
    for v, x in cob["volcanes"].items():
        if not x["dias_con_deficit"]:
            continue
        op = {(r.get("datetime_utc"), r.get("sensor")): r
              for r in json.loads((RAIZ / "data" / "mirova_equivalent" / f"{v}.json").read_text(encoding="utf-8"))["records"]}
        for e in x["dias_con_deficit"]:
            for h in e["faltan"]:
                pv = op[(h, e["sensor"])].get("product_version")
                tabla[e["trozo"]][v][pv if pv in ("nrt", "standard") else "otro"] += 1
    md = ["# Pasadas ausentes del reproceso, por trozo", "",
          "Generado por `deficit_por_trozo.py`. `nrt` y `standard` es el `product_version` del record operacional que "
          "se conservaria en C0.", "",
          "| Trozo | Ventana | Volcan | nrt | standard |", "|---:|---|---|---:|---:|"]
    for idx in sorted(tabla):
        for v, c in sorted(tabla[idx].items()):
            md.append(f"| {idx} | {ventanas[idx][0]} a {ventanas[idx][1]} | {v} | {c['nrt']} | {c['standard']} |")
    (AQUI / "deficit_por_trozo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
