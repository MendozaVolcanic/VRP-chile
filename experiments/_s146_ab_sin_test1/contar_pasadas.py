# -*- coding: utf-8 -*-
"""Cobertura pareja entre brazos: cuenta las pasadas de cada brazo y las compara con el control.

POR QUE (A108). Un run con todos los jobs en verde no prueba que los brazos hayan procesado las
mismas pasadas: un corte de NASA deja un brazo con gránulos de menos y el cortacircuitos por host
(A64) hace que el job igual termine bien. Si eso pasa, la diferencia entre brazos mezcla el efecto
del flag con el efecto de la cobertura, y el veredicto no significa nada. Este conteo se corre
ANTES de mirar cualquier resultado y FALLA si un brazo tiene menos pasadas que el control.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
 (1) Si lo que mide estuviera roto, fallaria? Si: el control se compara consigo mismo y tiene que
     dar cero faltantes. Si el conteo perdiera pasadas, esa fila lo mostraria.
 (2) Si el instrumento estuviera muerto (por ejemplo, si no leyera los archivos), se veria
     distinto? Si: informa el total de pasadas por brazo y por volcan; con cero pasadas el
     programa falla en vez de declarar cobertura pareja.

Uso:  python contar_pasadas.py --control <dir_control> --brazo <dir> [--brazo <dir> ...]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return "?"


def claves(d, ventana):
    d = Path(d)
    out = set()
    faltan_archivos = []
    for vol in VOLS:
        p = d / f"{vol}.json"
        if not p.exists():
            faltan_archivos.append(vol)
            continue
        recs = json.loads(p.read_text(encoding="utf-8")).get("records", [])
        for r in recs:
            f = (r.get("datetime_utc") or "")[:10]
            if ventana and not (ventana[0] <= f <= ventana[1]):
                continue
            out.add((vol, bucket(r.get("sensor")), r.get("datetime_utc"), r.get("granule")))
    return out, faltan_archivos


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True)
    ap.add_argument("--brazo", action="append", default=[])
    ap.add_argument("--inicio", default="2026-09-01")
    ap.add_argument("--fin", default="2026-09-20")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    kc, faltan_c = claves(a.control, ventana)
    if not kc:
        print("::error::el control no tiene ninguna pasada en la ventana: no hay nada que comparar")
        return 1
    filas = [{"brazo": Path(a.control).name, "n": len(kc), "faltan": 0, "sobran": 0,
              "archivos_faltantes": faltan_c, "faltan_por_volcan": {}}]
    ok = not faltan_c
    for d in a.brazo:
        kb, faltan_arch = claves(d, ventana)
        faltan = kc - kb
        sobran = kb - kc
        por_vol = collections.Counter(k[0] for k in faltan)
        filas.append({"brazo": Path(d).name, "n": len(kb), "faltan": len(faltan),
                      "sobran": len(sobran), "archivos_faltantes": faltan_arch,
                      "faltan_por_volcan": dict(por_vol),
                      "ejemplos_faltantes": ["|".join(str(x) for x in k) for k in sorted(faltan)[:20]]})
        # S147 (verificador, H3): `sobran` tambien rompe la paridad. Se calculaba y no se usaba,
        # asi que un CONTROL al que le faltan pasadas (corte de red de NASA sobre el, A64) dejaba
        # a todos los brazos con sobran > 0 y faltan = 0, y el script imprimia COBERTURA PAREJA.
        # El control es la referencia de todos los demas criterios: si le faltan a EL, nada se
        # entera. La comparacion tiene que ser simetrica.
        if faltan or sobran or faltan_arch:
            ok = False

    print("%-34s %8s %8s %8s  %s" % ("brazo", "pasadas", "faltan", "sobran", "faltan por volcan"))
    for f in filas:
        print("%-34s %8d %8d %8d  %s"
              % (f["brazo"], f["n"], f["faltan"], f["sobran"], f["faltan_por_volcan"] or "-"))
        if f["archivos_faltantes"]:
            print("    archivos que no llegaron:", f["archivos_faltantes"])
    if a.out:
        Path(a.out).write_text(json.dumps({"ventana": list(ventana), "filas": filas},
                                          indent=1, ensure_ascii=False), encoding="utf-8")
    if ok:
        print("COBERTURA PAREJA: los brazos y el control tienen exactamente las mismas pasadas")
        return 0
    print("::error::COBERTURA DESPAREJA. Repetir los jobs de los volcanes listados con el MISMO "
          "codigo y volver a contar ANTES de evaluar (A108).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
