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

S180 (2026-11-13): LOS 34. Nicolás pidió tener hacia atrás los 34 volcanes sin MIROVA que el tablero ya muestra desde
la sombra diaria (plan docs/superpowers/plans/2026-11-13-historia-34-volcanos-via.md). El sellado rehúsa todo volcán
fuera de sus 11; este módulo cambia `PT.TIER_A` por los 34 dentro del mismo try/finally, sólo cuando la lista pedida
es entera de los 34, y lo restaura al salir. Una lista que mezcla los dos grupos la rehúsa el sellado.

Guard: tests/test_reproc_historia_via_s180.py.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s172_retro_paquete"))
import plan_trozos as PT  # noqa: E402

PERFIL_VIA = "_s172_retro_paquete"
INICIO_SERIE = "2025-02-15"   # inicio de la serie publicada de los 11 Tier A (#883)


_GRILLAS = RAIZ / "pipeline" / "grillas_mirova.yaml"
# Los 34 sin MIROVA: los volcanes con grilla que no son de los 11 (S172). Se leen de la grilla, no de una lista
# escrita a mano, para que la lista no se desvíe de lo que la vía puede correr.
LOS_34 = tuple(v for v in yaml.safe_load(_GRILLAS.read_text(encoding="utf-8"))["volcanes"] if v not in PT.TIER_A)


def planificar(perfil, volcanes_txt, ventanas_txt, max_dias=20, max_dias_chillan=10):
    if perfil.strip() != PERFIL_VIA:
        raise PT.Rehusado(f"REHUSADO: este despacho es sólo del brazo de la vía ({PERFIL_VIA}), no de {perfil!r}")
    # Un despacho es de los 11 o de los 34: si la lista es toda de los 34 se planifica contra los 34; si mezcla, se
    # planifica contra los 11 y el sellado rehúsa el primer volcán de los 34 (no hace falta otra regla).
    pedidos = {v.strip() for v in volcanes_txt.split(",") if v.strip()}
    grupo = LOS_34 if pedidos and pedidos <= set(LOS_34) else PT.TIER_A
    previo_ini, previo_tier = PT.INICIO_TUPUNGATITO, PT.TIER_A
    PT.INICIO_TUPUNGATITO, PT.TIER_A = INICIO_SERIE, grupo
    try:
        return PT.planificar(perfil, volcanes_txt, ventanas_txt, max_dias, max_dias_chillan)
    finally:
        PT.INICIO_TUPUNGATITO, PT.TIER_A = previo_ini, previo_tier


def main():
    jobs, saltados = planificar(os.environ["PERFIL"], os.environ["VOLCANES"], os.environ["VENTANAS"],
                                int(os.environ.get("MAX_DIAS") or 20), int(os.environ.get("MAX_DIAS_CHILLAN") or 10))
    print(f"jobs={json.dumps(jobs)}")
    for s in saltados:
        print("AVISO:", s, file=sys.stderr)
    print(f"{len(jobs)} trozos", file=sys.stderr)


if __name__ == "__main__":
    main()
