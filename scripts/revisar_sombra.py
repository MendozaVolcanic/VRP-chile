"""S167: revisa que una corrida de la sombra (.github/workflows/sombra-codigo-mirova.yml) haya producido records de la vía.

POR QUÉ. run_pipeline.py atrapa toda excepción por gránulo, imprime `ERROR processing` y termina con salida 0. Si en el
runner falta una dependencia de la vía (sin pyproj, cada gránulo da error) o el MxD03 no calza, el job queda verde con
«sin cambios» y la sombra no mide nada durante semanas sin que nadie lo note: el pipeline zombie del CLAUDE.md global
(regla 6). Y si la vía no puede correr en un gránulo (`via_codigo_mirova` = "sin_grilla", "sin_mxd03" o
"geo_distinta"), el procesador cae a K y el record de K queda en la carpeta de la sombra: el lector lo tiene que poder
filtrar, pero además hay que verlo el mismo día.

QUÉ HACE. Cuenta, en la ventana corrida, los records del volcán con `via_codigo_mirova` igual a true y distinto, y las
líneas `ERROR processing` del log. Sale 1 (el job queda rojo) si hubo errores, si algún record de la ventana no es de
la vía, o si no hay ningún record de la vía (en 8 días siempre hay pasadas nocturnas; cero es una falla, aunque sea de
NASA). Imprime el resumen igual.

Uso: python scripts/revisar_sombra.py --json data/sombra_codigo_mirova/<Volcan>.json --log pipeline.log --ini A --fin B
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def revisar(registros, log_txt, ini, fin):
    """(ok, resumen). ini y fin en AAAA-MM-DD, inclusive, sobre la fecha UTC de la pasada."""
    en_ventana = [r for r in registros if ini <= str(r.get("datetime_utc") or "")[:10] <= fin]
    via = sum(1 for r in en_ventana if r.get("via_codigo_mirova") is True)
    otros = {}
    for r in en_ventana:
        if r.get("via_codigo_mirova") is not True:
            k = str(r.get("via_codigo_mirova"))
            otros[k] = otros.get(k, 0) + 1
    errores = sum(1 for ln in log_txt.splitlines() if "ERROR processing" in ln)
    fallas = []
    if errores:
        fallas.append(f"{errores} gránulos con ERROR processing")
    if otros:
        fallas.append(f"records que no son de la vía: {otros}")
    if via == 0:
        fallas.append("ningún record de la vía en la ventana")
    resumen = (f"ventana {ini} a {fin}: {len(en_ventana)} records, {via} de la vía, {sum(otros.values())} de otra "
               f"fuente, {errores} errores de gránulo")
    return not fallas, resumen + ("" if not fallas else " | FALLA: " + "; ".join(fallas))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--ini", required=True)
    ap.add_argument("--fin", required=True)
    a = ap.parse_args(argv)
    p = Path(a.json)
    registros = json.loads(p.read_text(encoding="utf-8")).get("records", []) if p.exists() else []
    lg = Path(a.log)
    log_txt = lg.read_text(encoding="utf-8", errors="replace") if lg.exists() else ""
    ok, resumen = revisar(registros, log_txt, a.ini, a.fin)
    print(resumen)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
