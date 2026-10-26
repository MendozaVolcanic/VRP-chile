# -*- coding: utf-8 -*-
"""Días con hueco de NASA que se excluyen del A/B diurno sobre K (adenda del 2026-10-26, §11 del pre-registro).

EL FENÓMENO. A veces el archivo de NASA no tiene los gránulos de un satélite para un día: en W1, Suomi NPP no tiene
ninguno el 10, 11 y 12 de marzo de 2026 (ni en el archivo estándar ni en el NRT). Ese día ninguno de los dos brazos
puede procesar esas pasadas, de noche ni de día, y la compuerta I4 lee el hueco como una falla del brazo diurno. No es
una falla del brazo: es un dato que no existe. Repetir el job no lo arregla.

LA REGLA (mecánica, de fuera del A/B; adenda 1 del §11, con (b') desde la decisión de la coordinadora S164). Un día d
se excluye de los dos brazos si, para alguna plataforma VIIRS P (Suomi NPP, NOAA-20, NOAA-21, en I y en M):
  (a)  el catálogo CMR de NASA devuelve 0 gránulos del producto L1B de P ese día sobre la caja de los 11 volcanes
       (VNP02IMG, VJ102IMG, VJ202IMG, VNP02MOD, VJ102MOD, VJ202MOD), y
  (b') el CONTROL no tiene ningún record de P ese día (contado con el campo `sensor` del record, que nombra la
       plataforma: VIIRS_SNPP, VIIRS_SNPP_750, ...).
Las dos a la vez y en la misma plataforma. (a) prueba que NASA no tiene el dato; (b'), que nuestro pipeline tampoco lo
tuvo, también donde el brazo diurno no actúa. Las dos preguntan lo mismo: si alguien pudo tener ese dato. Nada se
decide caso a caso.
La primera versión de la regla usaba (b) en vez de (b'): el control pierde al menos una pasada NOCTURNA de MIROVA de ese
sensor ese día. En W1 eso dependía de lo que MIROVA listó de noche y no de si el dato existía (el 11 y el 12 de marzo
NASA no tiene Suomi NPP, pero MIROVA no lista pasadas nocturnas de Suomi NPP de Láscar esos días). Se cambió a (b')
después de ver W1, que es informativa; (b) se sigue calculando e informando. La salida es la lista
`excluir_dias` que se le pasa al evaluador sellado (`evaluar(..., excluir_dias=...)`), que no se toca. Si I4 vuelve a
fallar después de excluir, el resultado es INVÁLIDO POR INSTRUMENTO (condición 3).

Uso: python -I experiments/_s163_diurno_k/dias_excluidos_nasa.py --raiz <W2> ... --raiz <W6> --ref <referencia
congelada> --salida <json>   (con --w1 para la ventana W1 de Láscar)
Pruebas: test_dias_excluidos_nasa.py.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for _p in (str(ROOT), str(ROOT / "scripts"), str(AQUI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import clase_mirova as cm  # noqa: E402

PRODUCTOS = {"VIIRS375": {"VNP02IMG": "2", "VJ102IMG": "2.1", "VJ202IMG": "2.1"},
             "VIIRS750": {"VNP02MOD": "2", "VJ102MOD": "2.1", "VJ202MOD": "2.1"}}
CAJA = "-72.5,-39.5,-67.5,-23.0"      # de Villarrica a Láscar (los 11 Tier A)
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"


def dias_a_excluir_b(vacios, faltas):
    """INFORMATIVO (la regla (b) original, no decide). vacios: producto -> días sin gránulos en CMR; faltas: sensor ->
    días en que el control pierde una pasada nocturna. Las dos condiciones, en el mismo sensor."""
    out = set()
    for s, prods in PRODUCTOS.items():
        sin = set().union(*(set(vacios.get(p, ())) for p in prods))
        out |= sin & set(faltas.get(s, ()))
    return sorted(out)


def faltas_nocturnas_del_control(pasadas, recs_control):
    """sensor -> días con al menos una pasada NOCTURNA VIIRS de MIROVA sin record del control a ±120 s."""
    import evaluar_diurno_k as ev
    idx = collections.defaultdict(list)
    for r in recs_control:
        if not r["es_dia"]:
            idx[(r["vol"], r["b"])].append(r["dt"])
    out = collections.defaultdict(set)
    for p in pasadas:
        if p.sensor_bucket not in PRODUCTOS:
            continue
        t = p.instante.replace(tzinfo=None)
        if ev.es_dia_vol(p.volcano, t):
            continue
        if not any(abs((x - t).total_seconds()) <= cm.VENTANA_S for x in idx.get((p.volcano, p.sensor_bucket), [])):
            out[p.sensor_bucket].add(t.strftime("%Y-%m-%d"))
    return dict(out)


# Plataforma de un record (campo `sensor`) -> producto L1B de CMR, para la condición (b').
PRODUCTO_DE_SENSOR = {"VIIRS_SNPP": "VNP02IMG", "VIIRS_NOAA20": "VJ102IMG", "VIIRS_NOAA21": "VJ202IMG",
                      "VIIRS_SNPP_750": "VNP02MOD", "VIIRS_NOAA20_750": "VJ102MOD", "VIIRS_NOAA21_750": "VJ202MOD"}


def dias_a_excluir(vacios, dias_con_records):
    """LA REGLA QUE DECIDE, (a) y (b'): días en que CMR no tiene gránulos de una plataforma y el control tampoco tiene
    ningún record de esa plataforma. `vacios`: producto -> días sin gránulos; `dias_con_records`: producto -> días con
    al menos un record del control de esa plataforma."""
    return sorted({d for p, ds in vacios.items() for d in ds if d not in dias_con_records.get(p, set())})


def dias_con_records_por_producto(raices, control, ventanas):
    """producto -> días con al menos un record del control de esa plataforma (lee el campo `sensor` de los JSON)."""
    import banco_paridad as bp
    out = collections.defaultdict(set)
    for raiz in raices:
        for vol in bp.VOLS:
            ruta = Path(raiz) / control / ("%s.json" % vol)
            if not ruta.exists():
                continue
            for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
                prod, d = PRODUCTO_DE_SENSOR.get(r.get("sensor")), str(r.get("datetime_utc", ""))[:10]
                if prod and any(w[1] <= d <= w[2] for w in ventanas):
                    out[prod].add(d)
    return dict(out)


def dias_sin_granulos(producto, version, desde, hasta):
    """Días de [desde, hasta] sin ningún gránulo del producto sobre CAJA, según CMR (público, sin credencial)."""
    dias, pagina = collections.Counter(), 1
    while True:
        q = urllib.parse.urlencode({"short_name": producto, "version": version, "bounding_box": CAJA, "page_size": 2000,
                                    "temporal": "%sT00:00:00Z,%sT23:59:59Z" % (desde, hasta), "page_num": pagina})
        e = json.load(urllib.request.urlopen(CMR + "?" + q, timeout=60))["feed"]["entry"]
        for g in e:
            dias[g["time_start"][:10]] += 1
        if len(e) < 2000:
            break
        pagina += 1
    n = (dt.date.fromisoformat(hasta) - dt.date.fromisoformat(desde)).days + 1
    return {x for x in ((dt.date.fromisoformat(desde) + dt.timedelta(i)).isoformat() for i in range(n)) if not dias[x]}


def armar_salida(excluir, vacios, con_records, excluir_b, faltas, consulta_utc, ventanas):
    """La lista que decide (a y b'), con su evidencia, y la de la regla (b) original, informativa."""
    ev_ = {}
    for d in excluir:
        ev_[d] = {"cmr_sin_granulos_y_control_sin_records": sorted(
            p for p, ds in vacios.items() if d in ds and d not in con_records.get(p, set()))}
    return {"excluir_dias": excluir, "regla": "a y b' (adenda 1, §11)", "consulta_cmr_utc": consulta_utc, "caja": CAJA,
            "ventanas": ventanas, "evidencia": ev_, "cmr_dias_sin_granulos": {p: sorted(ds) for p, ds in vacios.items()},
            "informativo_regla_b": {"excluir_dias": excluir_b,
                                    "control_dias_con_noches_perdidas": {s: sorted(ds) for s, ds in faltas.items()}}}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", action="append", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--control", default="_s154_ab_diurno_k_control")
    ap.add_argument("--w1", action="store_true", help="ventana W1 (Láscar, sólo la tabla) en vez de W2 a W6")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args(argv)
    import banco_paridad as bp
    import evaluar_diurno_k as ev
    import sustrato_k as sk
    if a.w1:
        w = next(x for x in sk.VENTANAS if x[0] == "W1")
        ventanas, canal, vols = [w[:3]], "tabla", w[3]
    else:
        ventanas, canal, vols = [x[:3] for x in sk.VENTANAS if x[0] in sk.DECIDEN], "union", None
    recs = ev.cargar_brazo(a.raiz, a.control, ventanas, bp.inner_desde_html())
    pas = ev.pasadas_de(sk.cargar_ref(Path(a.ref)), canal, ventanas, vols)
    faltas = faltas_nocturnas_del_control(pas, recs)
    consulta = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    vacios = collections.defaultdict(set)
    for s, prods in PRODUCTOS.items():
        for prod, ver in prods.items():
            for _, d0, d1 in ventanas:
                vacios[prod] |= dias_sin_granulos(prod, ver, d0, d1)
    con_records = dias_con_records_por_producto(a.raiz, a.control, ventanas)
    excluir = dias_a_excluir(dict(vacios), con_records)
    excluir_b = dias_a_excluir_b(dict(vacios), faltas)
    out = armar_salida(excluir, dict(vacios), con_records, excluir_b, faltas, consulta, ventanas)
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("consulta CMR %s" % consulta)
    print("días sin gránulos en CMR: %s" % {p: v for p, v in out["cmr_dias_sin_granulos"].items() if v})
    print("EXCLUIR_DIAS (regla a y b', decide): %s  evidencia: %s" % (excluir, out["evidencia"]))
    print("informativo, regla (b) original (el control pierde pasadas nocturnas de MIROVA): %s; noches perdidas: %s"
          % (excluir_b, out["informativo_regla_b"]["control_dias_con_noches_perdidas"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
