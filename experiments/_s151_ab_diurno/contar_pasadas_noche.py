# -*- coding: utf-8 -*-
"""Cobertura del A/B diurno separando noche y día (nulos 1 y 3 del PREREGISTRO.md).

POR QUÉ NO SE USA experiments/_s146_ab_sin_test1/contar_pasadas.py. Ese conteo exige que cada brazo
tenga EXACTAMENTE las mismas pasadas que el control, y el brazo diurno tiene por diseño pasadas que el
control no tiene (las de día): con él, el A/B diurno saldría siempre «cobertura despareja». Lo que el
pre-registro pide es otra cosa, y este script lo cuenta por separado:

  * NOCHE (nulo 3, A108): las pasadas nocturnas de cada brazo, contadas contra el control y en las dos
    direcciones (faltan y sobran, como S147 H3). El flag no toca la noche, así que una diferencia es un
    corte de NASA (A64) o un defecto del cableado; en los dos casos se repite el job antes de evaluar.
  * DÍA (nulo 1, A116): el control no puede traer NINGUNA pasada diurna (store la rechaza) y el brazo
    diurno no puede traer pasadas MODIS diurnas (la rama de D-10 es sólo VIIRS). Si al brazo diurno le
    falta TODA pasada diurna de VIIRS 375 o de VIIRS 750 (se exige cada sensor por separado), esa compuerta
    no se abrió (el caso S92) y se avisa.

Día y noche por la MISMA regla del pipeline (`pipeline.diurno.pasada_es_diurna`, elevación solar > 0
sobre el volcán a la hora del record), nunca por `es_pasada_diurna_descartada`, que sigue al flag.

Los volcanes se toman de los JSON del control (W1 es sólo Láscar); un volcán que el control trae y un
brazo no, falla.

Uso: python contar_pasadas_noche.py --control <dir> --brazo <dir> [--brazo <dir>] --inicio F --fin F --out x.json
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from pipeline.diurno import pasada_es_diurna  # noqa: E402
from auto_audit_weekly import _coords_por_volcan  # noqa: E402


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return "?"


def claves(d, vols, ventana, coords):
    """{'noche': set, 'dia': Counter por sensor} y los volcanes cuyo JSON no llegó."""
    noche, dia, faltan = set(), collections.Counter(), []
    for vol in vols:
        p = Path(d) / f"{vol}.json"
        if not p.exists():
            faltan.append(vol)
            continue
        lat, lon = coords[vol]
        for r in json.loads(p.read_text(encoding="utf-8")).get("records", []):
            t = r.get("datetime_utc") or ""
            if not (ventana[0] <= t[:10] <= ventana[1]):
                continue
            if pasada_es_diurna(t[:16], lat, lon):
                dia[bucket(r.get("sensor"))] += 1
            else:
                noche.add((vol, bucket(r.get("sensor")), t, r.get("granule")))
    return noche, dia, faltan


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):  # la autoprueba lo llama con la salida redirigida a un StringIO
        sys.stdout.reconfigure(encoding="utf-8")
    ap =argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True)
    ap.add_argument("--brazo", action="append", default=[])
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    coords = _coords_por_volcan()
    vols = sorted(p.stem for p in Path(a.control).glob("*.json") if p.stem in coords)
    if not vols:
        print("::error::el control no trae ningún JSON de volcán: no hay nada que comparar")
        return 1
    ventana = (a.inicio, a.fin)
    nc, dc, _ = claves(a.control, vols, ventana, coords)
    mal = []
    if not nc:
        mal.append("el control no tiene ninguna pasada nocturna en la ventana")
    if sum(dc.values()):
        mal.append("el CONTROL trae %d pasadas diurnas %s: store debía rechazarlas" % (sum(dc.values()), dict(dc)))
    filas = [{"brazo": Path(a.control).name, "volcanes": vols, "noche": len(nc), "faltan": 0, "sobran": 0,
              "dia_por_sensor": dict(dc)}]
    for d in a.brazo:
        nb, db, faltan_arch = claves(d, vols, ventana, coords)
        faltan, sobran = nc - nb, nb - nc
        fila = {"brazo": Path(d).name, "noche": len(nb), "faltan": len(faltan), "sobran": len(sobran),
                "faltan_por_volcan": dict(collections.Counter(k[0] for k in faltan)),
                "sobran_por_volcan": dict(collections.Counter(k[0] for k in sobran)),
                "ejemplos": ["|".join(str(x) for x in k) for k in sorted(faltan | sobran)[:20]],
                "dia_por_sensor": dict(db), "archivos_faltantes": faltan_arch}
        filas.append(fila)
        if faltan or sobran or faltan_arch:
            mal.append("%s: noches desparejas (faltan %d, sobran %d, archivos %s)" % (fila["brazo"], len(faltan), len(sobran), faltan_arch))
        if db.get("MODIS"):
            mal.append("%s: %d pasadas MODIS diurnas (la rama de D-10 es sólo VIIRS)" % (fila["brazo"], db["MODIS"]))
        # Por sensor (verificador del PR #822, hueco 6): 375 y 750 son dos compuertas; «375 o 750» dejaba pasar
        # una compuerta de 750 cerrada sin aviso.
        mudos = [s for s in ("VIIRS375", "VIIRS750") if not db.get(s)]
        if fila["brazo"] == "_s151_ab_diurno_on" and mudos:
            mal.append("%s: CERO pasadas diurnas de %s, el cableado no abrió el día en ese sensor (caso S92): INDECIDIBLE"
                       % (fila["brazo"], ", ".join(mudos)))
    print("%-28s %8s %7s %7s  %-40s %s" % ("brazo", "noche", "faltan", "sobran", "pasadas diurnas por sensor", "faltan/sobran por volcán"))
    for f in filas:
        print("%-28s %8d %7d %7d  %-40s %s" % (f["brazo"], f["noche"], f["faltan"], f["sobran"], f["dia_por_sensor"] or "-",
                                             {k: v for k, v in (("faltan", f.get("faltan_por_volcan")), ("sobran", f.get("sobran_por_volcan"))) if v} or "-"))
    if a.out:
        Path(a.out).write_text(json.dumps({"ventana": list(ventana), "filas": filas, "problemas": mal}, indent=1,
                                          ensure_ascii=False), encoding="utf-8")
    if not mal:
        print("COBERTURA NOCTURNA PAREJA y día como se espera (control sin día, brazo diurno con VIIRS diurno y sin MODIS diurno)")
        return 0
    for m in mal:
        print("::error::" + m)
    print("Repetir los jobs afectados con el MISMO código y volver a contar ANTES de evaluar (A108).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
