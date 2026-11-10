# -*- coding: utf-8 -*-
"""S175, respuesta parcial a C-05 de docs/COLA_CAMPO.md: cuántos records MODIS salen de la vía con MxD03.

POR QUÉ. C-05 pregunta si la geolocalización MODIS se corre hacia el nadir por la interpolación de la
grilla de 5 km. La vía «código MIROVA» toma la posición del MxD03 y no pasa por esa interpolación, pero
sólo los records marcados `via_codigo_mirova: true` vienen de ahí: el resto del histórico es K.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten", "Copahue", "PlanchonPeteroa",
        "PuyehueCordonCaulle", "NevadosDeChillan", "Tupungatito"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    conteo = Counter()
    primero, ultimo = {}, {}
    for v in VOLS:
        with open(ROOT / "data" / "mirova_equivalent" / f"{v}.json", encoding="utf-8") as fh:
            registros = json.load(fh)["records"]
        for r in registros:
            if r.get("sensor", "").startswith("MODIS"):
                marca = str(r.get("via_codigo_mirova", "sin campo"))
                conteo[marca] += 1
                t = r["datetime_utc"]
                primero[marca] = min(primero.get(marca, t), t)
                ultimo[marca] = max(ultimo.get(marca, t), t)
    print("records MODIS de los 11 Tier A por marca:", dict(conteo))
    print("primer record:", primero)
    print("ultimo record:", ultimo)


if __name__ == "__main__":
    main()
