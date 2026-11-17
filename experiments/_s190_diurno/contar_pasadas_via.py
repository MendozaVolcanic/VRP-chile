# -*- coding: utf-8 -*-
"""Cobertura de una corrida del A/B diurno sobre la vía (S190, ADENDA_VIA.md §5 y §6), antes de mirar nada (A108).

POR QUÉ NO SE USA TAL CUAL experiments/_s151_ab_diurno/contar_pasadas_noche.py. Ése exige que el brazo diurno NO traiga
pasadas MODIS diurnas (la rama de S151 era sólo VIIRS); aquí MODIS de día es justo lo que se abre. Se reusa su lectura
(`claves`: noche como conjunto de pasadas, día como cuenta por sensor, con la regla día/noche del pipeline) y se cambia
sólo lo que se exige del día:
  * el control no trae ninguna pasada diurna (store la rechaza con los dos flags apagados);
  * cada brazo diurno trae pasadas diurnas con `diag_codigo_mirova.dayflag` 1 en los TRES sensores, cada uno por
    separado (la prueba de humo de la adenda §5: si MODIS da cero, el cambio de pipeline/diurno.py no llegó y no se
    despacha lo demás);
  * la noche es la misma en los dos brazos, en las dos direcciones (sin cambio).

Uso: python contar_pasadas_via.py --control <dir> --brazo <dir> --inicio F --fin F [--out x.json]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_ab_diurno"))

import contar_pasadas_noche as cpn  # noqa: E402

SENSORES = ("MODIS", "VIIRS375", "VIIRS750")


def dia_con_dayflag(d, vols, ventana, coords):
    """Pasadas diurnas (por elevación) con dayflag 1, por sensor."""
    c = collections.Counter()
    for vol in vols:
        p = Path(d) / f"{vol}.json"
        if not p.exists():
            continue
        lat, lon = coords[vol]
        for r in json.loads(p.read_text(encoding="utf-8")).get("records", []):
            t = r.get("datetime_utc") or ""
            if ventana[0] <= t[:10] <= ventana[1] and cpn.pasada_es_diurna(t[:16], lat, lon) \
                    and (r.get("diag_codigo_mirova") or {}).get("dayflag") == 1:
                c[cpn.bucket(r.get("sensor"))] += 1
    return c


def revisar(control, brazos, ventana, coords):
    """(filas, problemas). Separado de main() para la prueba."""
    vols = sorted(p.stem for p in Path(control).glob("*.json") if p.stem in coords)
    if not vols:
        return [], ["el control no trae ningún JSON de volcán: no hay nada que comparar"]
    nc, dc, _ = cpn.claves(control, vols, ventana, coords)
    mal = []
    if not nc:
        mal.append("el control no tiene ninguna pasada nocturna en la ventana")
    if sum(dc.values()):
        mal.append("el CONTROL trae %d pasadas diurnas %s: store debía rechazarlas" % (sum(dc.values()), dict(dc)))
    filas = [{"brazo": Path(control).name, "volcanes": vols, "noche": len(nc), "dia_por_sensor": dict(dc)}]
    for d in brazos:
        nb, db, faltan_arch = cpn.claves(d, vols, ventana, coords)
        faltan, sobran = nc - nb, nb - nc
        df = dia_con_dayflag(d, vols, ventana, coords)
        fila = {"brazo": Path(d).name, "noche": len(nb), "faltan": len(faltan), "sobran": len(sobran),
                "ejemplos": ["|".join(str(x) for x in k) for k in sorted(faltan | sobran)[:20]],
                "dia_por_sensor": dict(db), "dia_dayflag1_por_sensor": dict(df), "archivos_faltantes": faltan_arch}
        filas.append(fila)
        if faltan or sobran or faltan_arch:
            mal.append("%s: noches desparejas (faltan %d, sobran %d, archivos %s)"
                       % (fila["brazo"], len(faltan), len(sobran), faltan_arch))
        mudos = [s for s in SENSORES if not df.get(s)]
        if mudos:
            mal.append("%s: CERO pasadas diurnas con dayflag 1 en %s: el cableado no abrió el día ahí (caso S92)"
                       % (fila["brazo"], ", ".join(mudos)))
    return filas, mal


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True)
    ap.add_argument("--brazo", action="append", default=[])
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)
    filas, mal = revisar(a.control, a.brazo, ventana, cpn._coords_por_volcan())
    for f in filas:
        print(json.dumps(f, ensure_ascii=False))
    if a.out:
        Path(a.out).write_text(json.dumps({"ventana": list(ventana), "filas": filas, "problemas": mal}, indent=1,
                                          ensure_ascii=False), encoding="utf-8")
    if not mal:
        print("COBERTURA NOCTURNA PAREJA y día como se espera (control sin día; brazo diurno con dayflag 1 en MODIS, "
              "VIIRS 375 y VIIRS 750)")
        return 0
    for m in mal:
        print("::error::" + m)
    print("Repetir los jobs afectados con el MISMO código y volver a contar ANTES de evaluar (A108).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
