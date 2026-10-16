# -*- coding: utf-8 -*-
"""Une los records de dos o más intentos del MISMO brazo y el mismo código (vuelta 68 del loop, 2026-10-16).

Por qué: en W1 cada intento del brazo diurno perdió pasadas nocturnas distintas por caídas sueltas de descarga
(intento 1 sin 03-20 MODIS ni 03-18 NOAA-20; intento 3 sin 03-14 NOAA-20), y repetir otra vez puede perder otra.
Antes de unir hay que comprobar que en los gránulos comunes los records son IDÉNTICOS (sin los campos de hora de
proceso): si lo son, el código es determinista y la unión es una corrida completa con el mismo código. Si no, no se
une y se informa. En W1: 325 comunes, 0 distintos; la unión cubre las 183 noches del control.

Uso: python unir_intentos.py --out <json> <intento1.json> <intento2.json> [...]
"""
import argparse
import json
import sys

PROCESO = {"processed_utc", "first_processed_utc", "regimen", "updated"}


def clave(r):
    return (r.get("sensor"), r.get("datetime_utc"), r.get("granule"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("intentos", nargs="+")
    a = ap.parse_args()
    docs = [json.load(open(p, encoding="utf-8")) for p in a.intentos]
    union, distintos = {}, []
    for d in docs:
        for r in d["records"]:
            k = clave(r)
            if k in union:
                x = {c: v for c, v in union[k].items() if c not in PROCESO}
                y = {c: v for c, v in r.items() if c not in PROCESO}
                if x != y:
                    distintos.append(k)
            union[k] = r
    if distintos:
        print("NO SE UNE: %d gránulos comunes con records distintos, p. ej. %s" % (len(distintos), distintos[:3]))
        sys.exit(1)
    salida = dict(docs[-1])
    salida["records"] = sorted(union.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
    json.dump(salida, open(a.out, "w", encoding="utf-8"))
    print("intentos %s -> unión %d records, 0 distintos en los comunes" % ([len(d["records"]) for d in docs], len(union)))


if __name__ == "__main__":
    main()
