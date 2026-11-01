# -*- coding: utf-8 -*-
"""Verificador del censo del oraculo V750 (S159), camino (d): la poblacion del frente N contra la referencia.

Pregunta: las pasadas de VIIRS 750 nocturnas en que MIROVA miro (filas de la referencia en la ventana) que NO tienen
record nuestro a +-120 s quedan fuera del censo. Cuantas son, de que tipo (RUTINA o alerta), y cuantas entrarian a
+-480 s. Tambien: cuantas filas se parean con mas de un record nuestro.
Pregunta 1 (si el pareo estuviera roto, se veria?): con tolerancia 0 s el numero de filas sin record debe subir; se
imprime. Pregunta 2 (instrumento muerto): si no carga referencia o records, aborta por assert.
Vara: la referencia local de experiments/_s159/n (D:\\vrp-trabajo\\temporales\\s159_n\\ref) y los records de
origin/main 533398f8f en D:\\vrp-trabajo\\temporales\\s159_n\\data_main (los mismos insumos del frente N).
Ventana: 2026-04-01 a 2026-10-21; se informa aparte sin el 18 y 19 de octubre.
"""
from __future__ import annotations

import bisect
import collections
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

VENTANA = ("2026-04-01", "2026-10-21")
EXCL = ("2026-10-18", "2026-10-19")
REF = Path(r"D:\vrp-trabajo\temporales\s159_n\ref")
DATA = Path(r"D:\vrp-trabajo\temporales\s159_n\data_main")
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def main():
    coords = B._coords_por_volcan()
    inner = B.inner_desde_html()
    filas = cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    por_vb, ns, nv, n_ref = B.indexar_referencia(filas, coords, VENTANA, regla_minimas="SN")
    recs = B.cargar_nuestros(coords, inner, VENTANA, data=str(DATA))
    assert n_ref > 0 and recs
    v750 = [r for r in recs if r["b"] == "VIIRS750"]
    nuestros = collections.defaultdict(list)
    for r in v750:
        nuestros[r["vol"]].append(r["dt"])
    for v in nuestros.values():
        v.sort()
    pr(f"== referencia: filas nocturnas en ventana (todos los sensores) {n_ref}; records V750 nocturnos nuestros {len(v750)}")

    def tiene_record(vol, dt, tol):
        ts = nuestros.get(vol, [])
        i = bisect.bisect_left(ts, dt - timedelta(seconds=tol))
        n = 0
        while i < len(ts) and ts[i] <= dt + timedelta(seconds=tol):
            n += 1
            i += 1
        return n

    # filas V750 de la referencia, deduplicadas por (volcan, minuto): una pasada puede tener fila CONS y fila OCR
    pasadas = {}
    for (vol, b), lista in por_vb.items():
        if b != "VIIRS750":
            continue
        for dt, f in lista:
            k = (vol, f["fecha_utc"][:16])
            p = pasadas.setdefault(k, {"vol": vol, "dt": dt, "tipos": set(), "fuentes": set(), "noche": f["fecha_utc"][:10]})
            p["tipos"].add(f["tipo"])
            p["fuentes"].add(f["source"])
    pr(f"== pasadas V750 nocturnas de la referencia (vol, minuto) en ventana: {len(pasadas)}; "
       f"sin el 18 y 19 de octubre: {sum(1 for p in pasadas.values() if p['noche'] not in EXCL)}")
    for tol in (0, 120, 480):
        con = collections.Counter()
        sin = collections.Counter()
        multi = 0
        for p in pasadas.values():
            n = tiene_record(p["vol"], p["dt"], tol)
            clase = ("alerta" if any(B.es_alerta(t) for t in p["tipos"]) else
                     "falso_positivo" if any(B.es_fp(t) for t in p["tipos"]) else
                     "rutina" if "RUTINA" in p["tipos"] else "otra:" + "/".join(sorted(p["tipos"])))
            (con if n else sin)[clase] += 1
            if n > 1:
                multi += 1
        pr(f"   tolerancia {tol:3d} s: con record {sum(con.values())} {dict(con)} | SIN record {sum(sin.values())} {dict(sin)} "
           f"| filas pareadas con mas de un record {multi}")
    # detalle de las sin record a 120 s: por volcan, por mes, por tipo
    sin120 = [p for p in pasadas.values() if not tiene_record(p["vol"], p["dt"], 120)]
    pr("== pasadas de la referencia SIN record nuestro a 120 s:", len(sin120))
    pr("   por volcan:", dict(sorted(collections.Counter(p["vol"] for p in sin120).items())))
    pr("   por mes:", dict(sorted(collections.Counter(p["noche"][:7] for p in sin120).items())))
    pr("   por tipo:", dict(collections.Counter("/".join(sorted(p["tipos"])) for p in sin120)))
    pr("   por fuente:", dict(collections.Counter("/".join(sorted(p["fuentes"])) for p in sin120)))
    pr("   de ellas, con record nuestro a 480 s:", sum(1 for p in sin120 if tiene_record(p["vol"], p["dt"], 480)))
    pr("   del 18 y 19 de octubre:", sum(1 for p in sin120 if p["noche"] in EXCL))
    # negativos limpios potenciales entre las sin record: RUTINA en noche sin alerta ni fp del sensor
    negpot = [p for p in sin120 if "RUTINA" in p["tipos"] and not any(B.es_alerta(t) or B.es_fp(t) for t in p["tipos"])
              and not ns.get((p["vol"], "VIIRS750", p["noche"]), {}).get("alerta") and not ns.get((p["vol"], "VIIRS750", p["noche"]), {}).get("fp")]
    pr(f"   negativos limpios potenciales (RUTINA, noche del sensor sin alerta ni FP) sin record: {len(negpot)}; "
       f"sin el 18 y 19 de octubre: {sum(1 for p in negpot if p['noche'] not in EXCL)}")
    pr("   ejemplos:", [(p["vol"], p["dt"].strftime("%Y-%m-%d %H:%M")) for p in negpot[:8]])
    # el otro lado: records nuestros sin fila de la referencia (sin_info), para el denominador
    B.etiquetar(recs, por_vb, ns, nv)
    pr("== etiquetas de nuestros records V750 a 120 s:", dict(collections.Counter(r["lab"] for r in v750)))
    (AQUI / "verif_poblacion_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
