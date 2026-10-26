# -*- coding: utf-8 -*-
"""S162 V750-A: compara record por record el JSON de un volcán producido por main y por la rama del cableado.

Ignora sólo la hora de proceso (`processed_utc`, `first_processed_utc`), que cambia entre corridas por construcción.
Instrumento: si los dos archivos están vacíos no hay nada comparado y el resultado es SIN DATO (salida 2), no VERDE;
si algún record de la rama trae `via_codigo_mirova`, el flag no estaba apagado y es ROJO.
Uso: python comparar_bitabit_nrt.py <json de main> <json de la rama>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

IGNORAR = ("processed_utc", "first_processed_utc")


def cargar(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    recs = d if isinstance(d, list) else d.get("records", d)
    for r in recs:
        for k in IGNORAR:
            r.pop(k, None)
    return {(r.get("datetime_utc"), r.get("sensor")): r for r in recs}


def main(a, b):
    A, B = cargar(a), cargar(b)
    marcados = [k for k, r in B.items() if "via_codigo_mirova" in r]
    solo_a, solo_b = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    distintos = [k for k in sorted(set(A) & set(B)) if json.dumps(A[k], sort_keys=True) != json.dumps(B[k], sort_keys=True)]
    print(f"records main {len(A)} rama {len(B)} | sólo en main {len(solo_a)} | sólo en la rama {len(solo_b)} | "
          f"distintos {len(distintos)} | con la marca de la vía {len(marcados)}")
    for k in (solo_a + solo_b + distintos + marcados)[:20]:
        print("   ", k)
    if not A and not B:
        print("== bit a bit: SIN DATO (ningún record en los dos)")
        return 2
    bien = not (solo_a or solo_b or distintos or marcados)
    print("== bit a bit:", "VERDE" if bien else "ROJO")
    return 0 if bien else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
