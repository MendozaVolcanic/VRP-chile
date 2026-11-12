# -*- coding: utf-8 -*-
"""Plan de trozos de .github/workflows/reproc-historia-via.yml (S180, reemplazo de la historia con la vía).

POR QUÉ EXISTE. Nicolás decidió el 2026-11-11 (opción 1 de docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md, §3) reprocesar
con la vía «código MIROVA» Tupungatito del 2025-02-15 al 2026-02-22, para que su serie publicada sea de un solo
método. El planificador SELLADO de la retrospectiva (experiments/_s172_retro_paquete/plan_trozos.py) recorta
Tupungatito al 2026-02-23 por una razón de la REFERENCIA de esa prueba (§3.2 del pre-registro: MIROVA no lo cubre
antes), no de la vía, que corre con su grilla. El sellado no se toca: este módulo lo llama con ese inicio corrido al
2025-02-15, sólo para el brazo de la vía (`_s172_retro_paquete`), y lo deja como estaba al salir. Todas las demás
reglas (trozos de 20 días y de 10 en Chillán, un job no cruza de tramo, C-via de 90 % en 2025 y 100 % en 2026,
ventanas solapadas rehusadas, tope de 256 jobs) son las del sellado, sin copia.

Guard: tests/test_reproc_historia_via_s180.py.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s172_retro_paquete"))
import plan_trozos as PT  # noqa: E402

PERFIL_VIA = "_s172_retro_paquete"
INICIO_SERIE = "2025-02-15"   # inicio de la serie publicada de los 11 Tier A (#883)


def planificar(perfil, volcanes_txt, ventanas_txt, max_dias=20, max_dias_chillan=10):
    if perfil.strip() != PERFIL_VIA:
        raise PT.Rehusado(f"REHUSADO: este despacho es sólo del brazo de la vía ({PERFIL_VIA}), no de {perfil!r}")
    previo = PT.INICIO_TUPUNGATITO
    PT.INICIO_TUPUNGATITO = INICIO_SERIE
    try:
        return PT.planificar(perfil, volcanes_txt, ventanas_txt, max_dias, max_dias_chillan)
    finally:
        PT.INICIO_TUPUNGATITO = previo


def main():
    jobs, saltados = planificar(os.environ["PERFIL"], os.environ["VOLCANES"], os.environ["VENTANAS"],
                                int(os.environ.get("MAX_DIAS") or 20), int(os.environ.get("MAX_DIAS_CHILLAN") or 10))
    print(f"jobs={json.dumps(jobs)}")
    for s in saltados:
        print("AVISO:", s, file=sys.stderr)
    print(f"{len(jobs)} trozos", file=sys.stderr)


if __name__ == "__main__":
    main()
