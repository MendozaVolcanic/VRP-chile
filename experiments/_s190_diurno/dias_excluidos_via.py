# -*- coding: utf-8 -*-
"""Días con hueco de NASA que se excluyen del A/B diurno sobre la vía (adenda V, que deja la regla de S163 tal cual).

EL FENÓMENO. A veces el archivo de NASA no tiene los gránulos de un satélite para un día. Ese día ningún brazo puede
procesar esas pasadas, de noche ni de día, y la compuerta I4 leería el hueco como una falla del brazo diurno.

LA REGLA, sin cambios: la (a) más (b') de la adenda 1 de S163, implementada en
`experiments/_s163_diurno_k/dias_excluidos_nasa.py`, que este archivo importa y no copia. Un día se excluye si, para
alguna plataforma VIIRS, CMR no devuelve ningún gránulo L1B ese día sobre la caja de los 11 volcanes (a) y el control
tampoco tiene ningún record de esa plataforma ese día (b'). Lo único distinto de S163 es lo que la adenda V cambia
alrededor: las ventanas son W2 a W7 (`sustrato_via.VENTANAS`) y el control es `_s190_ab_diurno_via_control`.

MODIS. La regla sellada nombra sólo plataformas VIIRS. La adenda V agregó MODIS al A/B pero no a esta regla, así que
MODIS (MOD021KM y MYD021KM) se consulta y se informa con la misma (a) y (b'), y NO entra a `excluir_dias`. Si apareciera
un día MODIS que la regla habría excluido, se informa como desviación posible para Nicolás; no se decide aquí.

Uso: python -I experiments/_s190_diurno/dias_excluidos_via.py --raiz <W2> ... --raiz <W7> --ref <referencia congelada>
--salida <json>
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
S163 = ROOT / "experiments" / "_s163_diurno_k"
for _p in (str(ROOT), str(ROOT / "scripts"), str(S163), str(AQUI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import dias_excluidos_nasa as dn  # noqa: E402
import sustrato_via as sv  # noqa: E402

CONTROL = "_s190_ab_diurno_via_control"
# Informativo: la regla sellada no nombra MODIS (ver el docstring). Colección 6.1 en CMR.
PRODUCTOS_MODIS = {"MOD021KM": "6.1", "MYD021KM": "6.1"}  # version_id de CMR (los archivos dicen .061)
PRODUCTO_DE_SENSOR_MODIS = {"MODIS_TERRA": "MOD021KM", "MODIS_AQUA": "MYD021KM"}


def dias_con_records_modis(raices, control, ventanas):
    """producto MODIS -> días con al menos un record del control de esa plataforma."""
    import banco_paridad as bp
    out = collections.defaultdict(set)
    for raiz in raices:
        for vol in bp.VOLS:
            ruta = Path(raiz) / control / ("%s.json" % vol)
            if not ruta.exists():
                continue
            for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
                prod, d = PRODUCTO_DE_SENSOR_MODIS.get(r.get("sensor")), str(r.get("datetime_utc", ""))[:10]
                if prod and any(w[1] <= d <= w[2] for w in ventanas):
                    out[prod].add(d)
    return dict(out)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", action="append", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--control", default=CONTROL)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args(argv)
    import banco_paridad as bp
    import evaluar_diurno_via as ev
    import sustrato_k as sk
    ventanas = [(w[0], w[1], w[2]) for w in sv.VENTANAS]
    recs = ev.cargar_brazo(a.raiz, a.control, ventanas, bp.inner_desde_html())
    pas = ev.pasadas_de(sk.cargar_ref(Path(a.ref)), "union", ventanas)
    faltas = dn.faltas_nocturnas_del_control(pas, recs)
    consulta = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    vacios = collections.defaultdict(set)
    for prods in dn.PRODUCTOS.values():
        for prod, ver in prods.items():
            for _, d0, d1 in ventanas:
                vacios[prod] |= dn.dias_sin_granulos(prod, ver, d0, d1)
    con_records = dn.dias_con_records_por_producto(a.raiz, a.control, ventanas)
    excluir = dn.dias_a_excluir(dict(vacios), con_records)
    excluir_b = dn.dias_a_excluir_b(dict(vacios), faltas)
    out = dn.armar_salida(excluir, dict(vacios), con_records, excluir_b, faltas, consulta, ventanas)
    vacios_m = collections.defaultdict(set)
    for prod, ver in PRODUCTOS_MODIS.items():
        for _, d0, d1 in ventanas:
            vacios_m[prod] |= dn.dias_sin_granulos(prod, ver, d0, d1)
    con_m = dias_con_records_modis(a.raiz, a.control, ventanas)
    excluir_m = dn.dias_a_excluir(dict(vacios_m), con_m)
    out["informativo_modis"] = {"nota": "la regla sellada no nombra MODIS: no entra a excluir_dias",
                                "cmr_dias_sin_granulos": {p: sorted(ds) for p, ds in vacios_m.items()},
                                "dias_que_la_regla_excluiria": excluir_m}
    out["control"] = a.control
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("consulta CMR %s, ventanas %s" % (consulta, ventanas))
    print("días sin gránulos en CMR (VIIRS): %s" % {p: v for p, v in out["cmr_dias_sin_granulos"].items() if v})
    print("EXCLUIR_DIAS (regla a y b', decide): %s  evidencia: %s" % (excluir, out["evidencia"]))
    print("informativo, regla (b) original: %s; noches nocturnas perdidas por el control: %s"
          % (excluir_b, out["informativo_regla_b"]["control_dias_con_noches_perdidas"]))
    print("informativo MODIS (no decide): sin gránulos %s; la regla excluiría %s"
          % ({p: v for p, v in out["informativo_modis"]["cmr_dias_sin_granulos"].items() if v}, excluir_m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
