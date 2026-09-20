# -*- coding: utf-8 -*-
# ════════════════════════════════════════════════════════════════════
# FICHA SDA · clasificar_referencia.py  ·  SDA: VRP Chile · ID: VRP-CHILE / eje de referencia
# Objetivo      : correr el rotulado "confirmado por MIROVA / solo nuestro" sobre una ventana
#                 movil y dejarlo escrito en data/clasificacion_referencia/, un JSON por volcan.
# Logica        : toda la logica vive en scripts/clasificacion_referencia.py (ver su FICHA).
# Modelo/metodo : reglas deterministicas (cruce contra el CSV de MIROVA). Sin ML.
# Datos entrada : records del repo (solo lectura) + referencia MIROVA del repo. Sin datos personales.
# Variables     : --dias (largo de la ventana), --inicio/--fin, --cons/--ocr, --out.
# Limitaciones  : las del modulo. No modifica records, no filtra, no toca la deteccion.
# Refs/datos    : docs/audit_s145/CLASSIFICATION_SUSTRATO_Y_DISENO.md §5.2-5.3.
# ════════════════════════════════════════════════════════════════════
"""Post-proceso del eje de referencia (S146). Uso tipico, sin argumentos: ultimos 30 dias.

  python scripts/clasificar_referencia.py
  python scripts/clasificar_referencia.py --inicio 2026-09-01 --fin 2026-09-20 --stats salida.json

`--stats` agrega la distribucion por sensor y por volcan, sobre todas las pasadas y sobre las que
el dashboard publica (predicado ejecutado con node desde frontend/index.html, A97), mas un control
contra el banco de paridad. Necesita node; la corrida normal no.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import clasificacion_referencia as cr  # noqa: E402

bp = cr.bp


def _tabla(recs, clave):
    t = collections.defaultdict(collections.Counter)
    for r in recs:
        t[clave(r)][r["valor"]] += 1
    return {k: {v: t[k].get(v, 0) for v in cr.VALORES} | {"total": sum(t[k].values())}
            for k in sorted(t)}


def estadisticas(filas, ventana, procedencia):
    """Distribucion con denominador declarado. POR QUE pasa por el banco: asi el "publica" es el
    del operador y no uno reconstruido a mano, y de paso se controla que el cargador liviano del
    modulo recorre exactamente las mismas pasadas que el banco."""
    coords = bp._coords_por_volcan()
    recs = bp.cargar_nuestros(coords, bp.inner_desde_html(), ventana)  # trae `pub` (node)
    cr.clasificar_pasadas(recs, filas, coords, ventana)
    livianos = cr.cargar_pasadas(cr.DATA_RECORDS, coords, ventana)
    mismo = [(a["vol"], a["b"], a["dt"]) for a in recs] == [(b["vol"], b["b"], b["dt"]) for b in livianos]
    pub = [r for r in recs if r["pub"]]
    return {
        "ventana": list(ventana), "referencia": procedencia,
        "sha_index_html": bp.sha_git(bp.HTML),
        "denominadores": {"todas": "pasadas nocturnas de los 11 Tier A en la ventana",
                          "publicadas": "las de `todas` que el predicado del dashboard publica"},
        "control_mismo_recorrido_que_el_banco": mismo,
        "control_identidad_predicado": bp.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0]),
        "etiquetas_del_banco": dict(collections.Counter(r["lab"] for r in recs)),
        "todas": {"total": _tabla(recs, lambda r: "TOTAL"), "por_sensor": _tabla(recs, lambda r: r["b"]),
                  "por_volcan": _tabla(recs, lambda r: r["vol"])},
        "publicadas": {"total": _tabla(pub, lambda r: "TOTAL"), "por_sensor": _tabla(pub, lambda r: r["b"]),
                       "por_volcan": _tabla(pub, lambda r: r["vol"])},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Eje de referencia por pasada (post-proceso, S146)")
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--dias", type=int, default=30, help="largo de la ventana movil")
    ap.add_argument("--inicio", default=None, help="si se da, reemplaza a --dias")
    ap.add_argument("--cons", default=str(cr.CONS_DEFECTO))
    ap.add_argument("--ocr", default=str(cr.OCR_DEFECTO))
    ap.add_argument("--out", default=str(cr.OUT_DEFECTO))
    ap.add_argument("--stats", default=None, help="ruta de un JSON con la distribucion (usa node)")
    a = ap.parse_args(argv)

    fin = datetime.strptime(a.fin, "%Y-%m-%d")
    inicio = a.inicio or (fin - timedelta(days=a.dias)).strftime("%Y-%m-%d")
    if inicio < cr.PISO_REGIMEN:
        # POR QUE se recorta y no se aborta: el job corre solo; el piso es el cambio de regimen.
        print(f"aviso: inicio {inicio} recortado al piso del regimen {cr.PISO_REGIMEN} (A104)")
        inicio = cr.PISO_REGIMEN
    ventana = (inicio, a.fin)

    filas, procedencia = cr.cargar_referencia(a.cons, a.ocr)
    por_volcan = cr.construir(cr.DATA_RECORDS, filas, ventana)
    out = cr.escribir(a.out, por_volcan, ventana, procedencia)
    cuenta = collections.Counter(e["valor"] for d in por_volcan.values() for e in d.values())
    print(f"ventana {ventana[0]} a {ventana[1]} | pasadas {sum(cuenta.values())} | "
          f"{ {v: cuenta.get(v, 0) for v in cr.VALORES} }")
    print(f"referencia: {procedencia}")
    print(f"escrito en {out}")
    if a.stats:
        st = estadisticas(filas, ventana, procedencia)
        cr.negar_si_dentro_de_records(a.stats)
        Path(a.stats).parent.mkdir(parents=True, exist_ok=True)
        with open(a.stats, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(st, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"estadisticas en {a.stats} | publicadas {st['publicadas']['total']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
