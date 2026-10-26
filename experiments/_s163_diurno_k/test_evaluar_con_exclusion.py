# -*- coding: utf-8 -*-
"""Pruebas de evaluar_con_exclusion.py y de la consulta a CMR de dias_excluidos_nasa.py (adenda 1 del §11).

POR QUÉ. La adenda manda evaluar con los días con hueco de NASA fuera de los dos brazos, sin tocar el evaluador sellado.
El script de unión saca esos días de la referencia y de los records; esto tiene que dar lo mismo que el mecanismo
`excluir_dias` del evaluador, y la lista tiene que salir de una consulta a CMR que cuente bien los días.

Correr: python -m pytest -q -p no:cacheprovider experiments/_s163_diurno_k/test_evaluar_con_exclusion.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for p in (str(ROOT), str(ROOT / "scripts"), str(AQUI)):
    if p not in sys.path:
        sys.path.insert(0, p)

import dias_excluidos_nasa as dx  # noqa: E402
import evaluar_con_exclusion as ex  # noqa: E402
import evaluar_diurno_k as ev  # noqa: E402
from test_evaluar_diurno_k import B, C, P_SUP, SHA, V375, Completa  # noqa: E402


def _resumen(r):
    out = {"global": r["global"]}
    for s, m in r["por_sensor"].items():
        out[s] = (m["veredicto"], m["caso"], m["P"], m["P_obs"], m["neg_pub"], m["neg_obs"], m["neto"], m["Qn"])
    return out


def _escena():
    c = Completa().protegida(datetime(2026, 7, 25, 18, 0))
    c.protegida(datetime(2026, 7, 26, 18, 0), vol="Isluga")
    for h in (17, 19):                                        # un negativo diurno publicado el 26
        ins = datetime(2026, 7, 26, h, 30)
        c.filas.append({"volcano": "Villarrica", "sensor_bucket": V375, "fecha_utc": ins.strftime("%Y-%m-%d %H:%M:%S"),
                        "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": 1.0, "source": "CONS"})
        from test_evaluar_diurno_k import rec
        c.rb.append(rec("Villarrica", V375, ins, pub=(h == 17), disp=0.3, diag=True))
    return c


def test_quitar_dias_equivale_a_excluir_dias():
    c = _escena()
    ventanas = c.VENT
    recs = {C: c.rc, B: c.rb}
    for dias in ([], ["2026-07-26"], ["2026-07-25", "2026-07-26"], ["2026-06-14"]):
        pas = ev.pasadas_de(c.filas, "union", ventanas)
        directo = ev.evaluar(pas, recs, C, B, "e-ii", P_SUP, SHA, ventanas, excluir_dias=dias)
        f, r = ex.quitar_dias(c.filas, recs, dias)
        pegado = ev.evaluar(ev.pasadas_de(f, "union", ventanas), r, C, B, "e-ii", P_SUP, SHA, ventanas)
        assert _resumen(pegado) == _resumen(directo), dias
    # y el día excluido sí cambia algo (la prueba puede fallar): sin el 26 se pierde una protegida
    f, r = ex.quitar_dias(c.filas, recs, ["2026-07-26"])
    assert _resumen(ev.evaluar(ev.pasadas_de(f, "union", ventanas), r, C, B, "e-ii", P_SUP, SHA, ventanas))[V375][3] == 1


def test_quitar_dias_no_toca_la_entrada():
    c = _escena()
    n_f, n_b = len(c.filas), len(c.rb)
    ex.quitar_dias(c.filas, {C: c.rc, B: c.rb}, ["2026-07-26"])
    assert len(c.filas) == n_f and len(c.rb) == n_b


def test_lo_que_sale_por_dia():
    c = _escena()
    out = ex.lo_que_sale(c.filas, ["2026-07-26"], c.VENT)
    assert out["2026-07-26"].get("VIIRS375 día protegida") == 1
    assert out["2026-07-26"].get("VIIRS375 día rutina") == 3      # 1 de la escena base y las 2 de Villarrica


def test_consulta_cmr_pagina_y_cuenta_dias(monkeypatch):
    # dos páginas: la primera llena (2000), la segunda con 1; el 11 y el 13 quedan sin gránulos
    pag1 = [{"time_start": "2026-03-10T05:00:00.000Z"}] * 1999 + [{"time_start": "2026-03-12T17:00:00.000Z"}]
    pag2 = [{"time_start": "2026-03-12T18:00:00.000Z"}]
    pedidas = []

    def falso(url, timeout=60):
        pedidas.append(url)
        pagina = pag1 if "page_num=1" in url else pag2
        return io.BytesIO(json.dumps({"feed": {"entry": pagina}}).encode("utf-8"))

    monkeypatch.setattr(dx.urllib.request, "urlopen", falso)
    vacios = dx.dias_sin_granulos("VNP02IMG", "2", "2026-03-10", "2026-03-13")
    assert vacios == {"2026-03-11", "2026-03-13"}                 # también el último día de la ventana
    assert len(pedidas) == 2 and "short_name=VNP02IMG" in pedidas[0] and "bounding_box=" in pedidas[0]
