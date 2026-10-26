# -*- coding: utf-8 -*-
"""Parte una ventana de fechas en trozos que SÍ caben en un job de CI.

POR QUÉ: GitHub Actions mata cualquier job a las 6 h (límite duro, no
configurable). Un reproceso de Villarrica cuesta ~2.6 min por día-volcán, así
que una ventana de ~146 días necesita ~6 h 10 min: no entra, y el intento del
2026-08-25 se perdió entero tras 5 h 29 min de cómputo porque el commit iba
al final. Partir la ventana en trozos cortos hace que cada uno termine con
margen y que el resultado parcial sobreviva.

`max_days` sale de dividir el presupuesto de un job por el costo diario, con
holgura. No lo subas sin remedir el costo por día del volcán en cuestión.

Emite JSON (lista de {idx, start, end}) apto para una matrix de Actions.
"""
import argparse
import json
from datetime import date, timedelta


def _parse(s: str) -> date:
    return date.fromisoformat(s.strip())


def split_window(start: str, end: str, max_days: int = 37) -> list[dict]:
    """Trozos contiguos y disjuntos que cubren [start, end] completo."""
    d0, d1 = _parse(start), _parse(end)
    if d1 < d0:
        raise ValueError(f"ventana invertida: {start} > {end}")
    if max_days < 1:
        raise ValueError("max_days debe ser >= 1")

    trozos = []
    cur = d0
    while cur <= d1:
        fin = min(cur + timedelta(days=max_days - 1), d1)
        trozos.append({
            "idx": len(trozos) + 1,
            "start": cur.isoformat(),
            "end": fin.isoformat(),
        })
        cur = fin + timedelta(days=1)
    return trozos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--max-days", type=int, default=37)
    args = ap.parse_args(argv)

    trozos = split_window(args.start, args.end, args.max_days)
    print(json.dumps(trozos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
