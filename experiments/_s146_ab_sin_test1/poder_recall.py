# -*- coding: utf-8 -*-
"""Poder de cada metrica de recall candidata, medido ANTES de fijar el umbral del A/B.

POR QUE. El frente I de la auditoria (I-01) midio que "78 de 78 noches" no discrimina: publicamos
algo en casi todas las noches de casi todos los volcanes, asi que barajando al azar nuestros
"publica" el recall por noche sigue en 78 de 78. Un criterio construido sobre esa vara lo cumple
casi cualquier brazo, incluso uno malo. Antes de escribir el umbral del A/B hay que saber cual de
las varas de recall tiene poder HOY, sobre los records de produccion.

QUE HACE. Para cada vara candidata (noche de volcan cualquier sensor; noche del sensor que alerto;
pasada del sensor que alerto, por sensor) calcula el valor observado y el nulo: barajar el vector
"publica" DENTRO de cada volcan y sensor, N veces. Si el nulo alcanza el valor observado, la vara
no distingue un brazo bueno de uno que publicara al azar con la misma tasa, y no puede decidir.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
 (1) Si lo que mide estuviera roto, fallaria? Si: incluye dos controles de borde sobre el mismo
     denominador, "todo publica" y "nada publica", que tienen que dar recall 1 y 0 exactos. Si el
     conteo estuviera mal, esos dos no darian 1 y 0.
 (2) Si el instrumento estuviera muerto (por ejemplo, si el barajado no barajara), se veria
     distinto? Si: el nulo de una vara con poder tiene que quedar POR DEBAJO del observado. Si
     todas las varas dieran nulo igual al observado, habria que sospechar del barajado antes que
     de las varas; por eso se informa tambien la dispersion del nulo, que con un barajado muerto
     seria cero en todas.

Solo lectura. Sin red: la referencia son dos CSV en disco.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402


def recalls(recs):
    """Las tres varas candidatas, sobre un vector de publicacion ya fijado en cada record."""
    out = {}
    # Vara 1: la noche del volcan, cualquier sensor.
    g = collections.defaultdict(list)
    for r in recs:
        g[(r["vol"], r["noche"])].append(r)
    n1 = [v for v in g.values() if any(x["lab"] == "pos" for x in v)]
    out["noche_volcan"] = (sum(any(x["pub"] for x in v) for v in n1), len(n1))
    # Vara 2: la noche del SENSOR en que MIROVA alerto.
    g2 = collections.defaultdict(list)
    for r in recs:
        g2[(r["vol"], r["b"], r["noche"])].append(r)
    n2 = [v for v in g2.values() if any(x["lab"] == "pos" for x in v)]
    out["noche_sensor"] = (sum(any(x["pub"] for x in v) for v in n2), len(n2))
    for b in bp.BUCKETS:
        sub = [v for v in n2 if v[0]["b"] == b]
        out["noche_sensor_" + b] = (sum(any(x["pub"] for x in v) for v in sub), len(sub))
    # Vara 3: la PASADA que MIROVA alerto, por sensor.
    pos = [r for r in recs if r["lab"] == "pos"]
    out["pasada_pos"] = (sum(r["pub"] for r in pos), len(pos))
    for b in bp.BUCKETS:
        sub = [r for r in pos if r["b"] == b]
        out["pasada_pos_" + b] = (sum(r["pub"] for r in sub), len(sub))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default=str(ROOT / "data" / "mirova_equivalent"))
    ap.add_argument("--cons", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--inicio", default="2026-09-01")
    ap.add_argument("--fin", default="2026-09-20")
    ap.add_argument("--barajados", type=int, default=200)
    ap.add_argument("--semilla", type=int, default=146)
    ap.add_argument("--out", default=str(AQUI / "poder_recall.json"))
    a = ap.parse_args(argv)

    ventana = (a.inicio, a.fin)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(Path(a.cons), Path(a.ocr))
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana)
    recs = cargar_brazo(a.data, coords, inner, ventana)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)

    obs = recalls(recs)
    # Tasa base de publicacion: la probabilidad con que el barajado reparte los "publica".
    base = {}
    for b in bp.BUCKETS:
        sub = [r for r in recs if r["b"] == b]
        base[b] = {"n_pasadas": len(sub), "n_publica": sum(r["pub"] for r in sub),
                   "tasa": round(sum(r["pub"] for r in sub) / len(sub), 4) if sub else None}
    noches_con_algo = len({(r["vol"], r["noche"]) for r in recs if r["pub"]})
    noches_totales = len({(r["vol"], r["noche"]) for r in recs})

    # Controles de borde sobre el mismo denominador.
    guardado = [r["pub"] for r in recs]
    for r in recs:
        r["pub"] = 1
    todo = recalls(recs)
    for r in recs:
        r["pub"] = 0
    nada = recalls(recs)
    for r, p in zip(recs, guardado):
        r["pub"] = p

    # Nulo: barajar "publica" dentro de cada volcan y sensor.
    rnd = random.Random(a.semilla)
    grupos = collections.defaultdict(list)
    for i, r in enumerate(recs):
        grupos[(r["vol"], r["b"])].append(i)
    acum = collections.defaultdict(list)
    for _ in range(a.barajados):
        for idxs in grupos.values():
            vals = [recs[i]["pub"] for i in idxs]
            rnd.shuffle(vals)
            for i, v in zip(idxs, vals):
                recs[i]["pub"] = v
        for k, (num, den) in recalls(recs).items():
            acum[k].append(num)
    for r, p in zip(recs, guardado):
        r["pub"] = p

    tabla = {}
    for k, (num, den) in obs.items():
        xs = sorted(acum[k])
        if not xs or den == 0:
            tabla[k] = {"observado": [num, den], "nulo": None, "poder": "SIN DATO"}
            continue
        p05 = xs[int(0.05 * (len(xs) - 1))]
        mediana = xs[len(xs) // 2]
        # La vara tiene poder si el azar NO alcanza el valor observado casi siempre.
        alcanza = sum(1 for x in xs if x >= num) / len(xs)
        tabla[k] = {
            "observado": [num, den],
            "nulo_min": xs[0], "nulo_p05": p05, "nulo_mediana": mediana, "nulo_max": xs[-1],
            "nulo_dispersion": xs[-1] - xs[0],
            "fraccion_del_nulo_que_alcanza_lo_observado": round(alcanza, 3),
            "poder": "NO DISCRIMINA" if alcanza >= 0.5 else ("DEBIL" if alcanza >= 0.05 else "DISCRIMINA"),
            "control_todo_publica": list(todo[k]), "control_nada_publica": list(nada[k]),
        }

    salida = {"meta": {"ventana": list(ventana), "data": str(a.data),
                       "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "barajados": a.barajados, "semilla": a.semilla,
                       "n_records": len(recs), "n_filas_referencia": n_ref,
                       "sha_index_html": bp.sha_git(bp.HTML),
                       "etiquetas": dict(collections.Counter(r["lab"] for r in recs)),
                       "tasa_base_publicacion": base,
                       "noches_de_volcan_con_algo_publicado": [noches_con_algo, noches_totales]},
              "varas": tabla}
    Path(a.out).write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")

    print("ventana %s a %s | records %d | etiquetas %s"
          % (ventana[0], ventana[1], len(recs), salida["meta"]["etiquetas"]))
    print("tasa base de publicacion:", json.dumps(base, ensure_ascii=False))
    print("noches de volcan en que publicamos algo: %d de %d" % (noches_con_algo, noches_totales))
    print("\n%-26s %10s %10s %26s %14s %s"
          % ("vara", "observado", "nulo med", "nulo min a max", "alcanza obs", "poder"))
    for k, v in tabla.items():
        if v.get("nulo") is None and v["poder"] == "SIN DATO":
            print("%-26s %10s %10s %26s %14s %s" % (k, v["observado"], "-", "-", "-", "SIN DATO"))
            continue
        print("%-26s %10s %10s %26s %14s %s"
              % (k, "%d/%d" % tuple(v["observado"]), v["nulo_mediana"],
                 "%d a %d" % (v["nulo_min"], v["nulo_max"]),
                 v["fraccion_del_nulo_que_alcanza_lo_observado"], v["poder"]))
    print("\ncontroles de borde (todo publica / nada publica) en cada vara: ver el JSON")
    print("->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
