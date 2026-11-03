"""S173 (hallazgo 209, V2-02): hace fallar el job del NRT si un gránulo MODIS terminó en `ERROR processing`.

POR QUÉ. Con la vía «código MIROVA» encendida en MODIS (PR B), una excepción de la vía en un gránulo no cae a K:
scripts/run_pipeline.py la atrapa (`except Exception`), imprime `ERROR processing <archivo>: <error>` y sigue con el
gránulo siguiente. Esa pasada queda sin record de producción y el job sale verde. La vigilancia de la guardia K de
MODIS lo vería recién a las 24 h (protegida sin record, regla §4.4 (a)) o a los 3 días (frescura). Con este paso el
job queda rojo el mismo día y lo ve el monitor del NRT. No revierte nada: se investiga (regla de reversión de MODIS,
experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §4.4 (a), ronda 3).

QUÉ HACE. Lee el log de la corrida (el `pipeline.log` que nrt.yml llena con `tee`) y busca líneas
`ERROR processing <archivo>` cuyo archivo es un L1B de MODIS (`MOD021KM` de Terra o `MYD021KM` de Aqua, los mismos
nombres con que run_pipeline separa los L1B de MODIS). Si hay alguna: un `::error::` por gránulo y salida 1. Los
`ERROR processing` de VIIRS (375 m y 750 m) se cuentan y se informan, pero NO hacen fallar el job: B no cambia VIIRS y
el NRT los trata hoy igual que antes. Si el log no existe, FALLA (no se puede decir que no hubo errores sin mirarlos).
Salida 0 = sin errores de MODIS, 1 = con errores de MODIS o sin log.

Uso: python scripts/revisar_errores_modis_nrt.py --log pipeline.log [--volcan Lascar]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# `ERROR processing ` y después el nombre del archivo hasta los dos puntos que run_pipeline pone antes del error.
_ERROR = re.compile(r"(?<![A-Za-z0-9_])ERROR processing\s+([^\s:]+)")
# L1B de MODIS: MOD021KM (Terra) o MYD021KM (Aqua), como token propio del nombre (A92: no por subcadena suelta).
_L1B_MODIS = re.compile(r"(?<![A-Za-z0-9])M[OY]D021KM(?![A-Za-z0-9])")


def clasificar(log_txt: str) -> tuple[list[str], list[str]]:
    """Devuelve (líneas de error de MODIS, líneas de error de otros sensores)."""
    modis, otros = [], []
    for ln in log_txt.splitlines():
        m = _ERROR.search(ln)
        if not m:
            continue
        (modis if _L1B_MODIS.search(m.group(1)) else otros).append(ln.strip())
    return modis, otros


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--log", required=True)
    ap.add_argument("--volcan", default="")
    a = ap.parse_args(argv)
    sufijo = f" ({a.volcan})" if a.volcan else ""
    lg = Path(a.log)
    try:
        log_txt = lg.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"::error title=NRT sin log{sufijo}::no se pudo leer {a.log} ({type(e).__name__}); "
              "no se puede comprobar si hubo errores de MODIS")
        return 1
    modis, otros = clasificar(log_txt)
    for ln in modis[:20]:
        print(f"::error title=Error en un granulo MODIS{sufijo}::{ln}")
    if len(modis) > 20:
        print(f"::error title=Error en un granulo MODIS{sufijo}::y {len(modis) - 20} mas")
    resumen = (f"gránulos MODIS con ERROR processing: {len(modis)}; de otros sensores (no hacen fallar): "
               f"{len(otros)}")
    print(resumen)
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta and modis:
        try:
            with open(ruta, "a", encoding="utf-8") as fh:
                fh.write("### Error en un gránulo MODIS%s\n\n%s. Esa pasada quedó sin record de producción "
                         "(la vía no cae a K). Investigar según §4.4 (a) de la regla de reversión de MODIS.\n\n```\n%s\n```\n"
                         % (sufijo, resumen, "\n".join(modis[:20])))
        except OSError:
            pass
    return 1 if modis else 0


if __name__ == "__main__":
    sys.exit(main())
