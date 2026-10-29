# -*- coding: utf-8 -*-
"""S167 V375-E, adenda 3 (§9.6): conteo de DISEÑO, antes de leer, de cuántas noches del marco pueden dar pares para la
curva de cenit. Lee sólo la lista de objetivos (volcán, hora, cenit, VRP de MIROVA, plataforma, canal): ninguna grilla,
ningún resultado de run, ninguna publicación de K ni del paquete.

POR QUÉ. El §5.3 exige 8 noches en la lectura y 8 en el nulo de cenit parecido. Si el marco no las puede dar ni con
todas sus alertas publicadas, la curva da SIN SUSTRATO por construcción, y eso hay que decirlo antes de medir.
Uso: python -I contar_pares_curva.py  (escribe contar_pares_curva_salida.txt)
"""
from __future__ import annotations

import collections
import io
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import leer_posicion_v375e as LP  # noqa: E402


def pares(por, dz_lect=15.0, dz_nulo=5.0):
    lect = sum(1 for v in por.values() if len(v) >= 2 and max(v) - min(v) >= dz_lect)
    nulo = sum(1 for v in por.values() if len(v) >= 2
               and min(abs(a - b) for i, a in enumerate(v) for b in v[i + 1:]) < dz_nulo)
    return lect, nulo


def main():
    L = []
    obj = LP.objetivos(None)
    L.append(f"clases del marco: {sorted(collections.Counter((o.get('lote'), o['clase']) for o in obj.values()).items())}")
    pos = [o for o in obj.values() if o["clase"].startswith("pos") and (o.get("mirova_vrp") or 0) > 0]
    L.append(f"alertas con VRP de MIROVA: {len(pos)} ({collections.Counter(o['clase'] for o in pos)}); con cenit "
             f"{sum(1 for o in pos if o.get('z') is not None)}")
    por = collections.defaultdict(list)
    for o in pos:
        if o.get("z") is not None:
            por[(o["volcan"], o["hora_utc"][:10])].append(o["z"])
    lect, nulo = pares(por)
    L.append(f"noches-volcán con 2 o más alertas: {sum(1 for v in por.values() if len(v) >= 2)}; con 15° o más de cenit "
             f"(lectura): {lect}; con un par a menos de 5° (nulo): {nulo}")
    for tr, f in (("T", lambda d: d < "2026-06-13"), ("O", lambda d: d >= "2026-06-13")):
        lt, nt = pares({k: v for k, v in por.items() if f(k[1])})
        L.append(f"  {tr}: lectura {lt}, nulo {nt}")
    L.append(f"plataformas: {sorted(collections.Counter(o.get('sensor') for o in pos).items())}; alerta de la tabla: "
             f"{sum(1 for o in pos if o.get('alerta_tabla'))} de {len(pos)}")
    L.append("mínimo del §5.3: 8 noches en la lectura y 8 en el nulo => " + (
        "SIN SUSTRATO POR CONSTRUCCIÓN (el nulo no llega)" if nulo < 8 else "puede tener sustrato"))
    print("\n".join(L))
    (AQUI / "contar_pares_curva_salida.txt").write_text("".join(x + chr(10) for x in L), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
