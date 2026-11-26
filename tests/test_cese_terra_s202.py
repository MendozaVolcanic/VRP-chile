# -*- coding: utf-8 -*-
"""S202: cese de Terra (NASA, 2026-12-01) en la lista de ceses esperados y en la línea del tablero.

POR QUÉ. NASA anunció que Terra deja de tomar observaciones nuevas el 2026-12-01 (día 335) y que ese día LANCE
detiene todo el NRT de MODIS Terra (aviso «New Terra Observations Cease December 1, 2026», publicado el 2026-11-17 y
actualizado el 19-nov; blog de LANCE del 25-nov). La lista `scripts/ceses_esperados.json` sólo traía a Suomi NPP. Sin
Terra en ella: la vigilancia por plataforma abre una ALARMA en vez de un aviso informativo, la auditoría semanal
mezcla en la ventana de MODIS noches con dos satélites y noches con uno (una mirada menos por noche cambia el recall por
muestreo, no por el detector, como con Suomi NPP en S161), el NRT gasta búsquedas vacías que el log no distingue de «no
pasó», y los gráficos no marcan el día en que MODIS pierde la pasada de la mañana. NASA no da hora: por decisión de
Nicolás del 2026-11-26 («Sí, regístralo», a la propuesta de las 00:00 UTC del 1-dic) se toma el inicio del día; se
pierde a lo más la pasada nocturna de Terra de ese día, si existiera.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría antes del cambio? Sí: sin la entrada de Terra, las seis fallan (la
lista, el NRT, la auditoría y la vigilancia no la ven; el módulo del tablero no tiene lista de ceses). (2) ¿Podría pasar
sin mirar nada? Cada una tiene su control: Aqua sigue buscándose y vigilándose, el día anterior al cese Terra se busca,
y sin la entrada la vigilancia da ALARMA por Terra (el instrumento puede alarmar).
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
LISTA = RAIZ / "scripts" / "ceses_esperados.json"
MODULO = RAIZ / "frontend" / "cese_plataformas.js"
FUENTE = "https://www.earthdata.nasa.gov/data/alerts-outages/new-terra-observations-cease-december-1-2026"
CESE = "2026-12-01T00:00:00Z"


def _terra():
    ceses = json.loads(LISTA.read_text(encoding="utf-8"))["ceses"]
    t = [c for c in ceses if c["plataforma"] == "Terra"]
    assert len(t) == 1, "la lista de ceses no trae a Terra"
    return t[0]


def test_terra_en_la_lista_con_la_fecha_y_la_fuente_de_nasa():
    t = _terra()
    assert t["sensores"] == ["MODIS_TERRA"]
    assert t["desde_utc"] == CESE
    assert t["fuente"] == FUENTE


def test_el_nrt_deja_de_buscar_terra_desde_el_1_dic_y_sigue_con_aqua():
    fetch = pytest.importorskip("pipeline.fetch")
    assert fetch.cese_cumplido("MODIS_TERRA", datetime(2026, 11, 30)) is None
    assert fetch.cese_cumplido("MODIS_TERRA", datetime(2026, 12, 1)) is not None
    assert fetch.cese_cumplido("MODIS_AQUA", datetime(2026, 12, 5)) is None


def test_la_auditoria_semanal_juzga_modis_desde_el_1_dic():
    import scripts.auto_audit_weekly as aa
    ceses, error = aa.leer_ceses()
    assert error is None
    terra = [c for c in ceses if c["plataforma"] == "Terra"]
    assert terra and terra[0]["sensores"] == ["MODIS"] and terra[0]["primer_dia_sin"] == "2026-12-01"
    from datetime import date
    assert aa.juzga_desde(ceses, date(2026, 11, 30)).get("MODIS") is None
    assert aa.juzga_desde(ceses, date(2026, 12, 3)).get("MODIS") == "2026-12-01"


def _registros(hasta_terra):
    """Una pasada cada 6 h de NOAA-20, NOAA-21, Aqua y Terra (Terra sólo hasta `hasta_terra`)."""
    regs, t = [], datetime(2026, 11, 20, tzinfo=timezone.utc)
    while t < datetime(2026, 12, 5, 12, tzinfo=timezone.utc):
        for s in ("VIIRS_NOAA20", "VIIRS_NOAA20_750", "VIIRS_NOAA21", "VIIRS_NOAA21_750", "MODIS_AQUA"):
            regs.append((s, t))
        if t < hasta_terra:
            regs.append(("MODIS_TERRA", t))
        t += timedelta(hours=6)
    return regs


def test_la_vigilancia_informa_el_cese_de_terra_y_no_alarma():
    import scripts.vigilar_plataformas as vp
    ahora = datetime(2026, 12, 5, 12, tzinfo=timezone.utc)
    regs = _registros(datetime(2026, 12, 1, tzinfo=timezone.utc))
    v = vp.evaluar(regs, ahora, vp.cargar_ceses())
    assert "Terra" not in [a["plataforma"] for a in v["alarmas"]]
    assert "Terra" in [c["plataforma"] for c in v["ceses_confirmados"]]
    # Control: sin la entrada de Terra, la misma serie da ALARMA por Terra (el instrumento puede alarmar).
    sin_terra = [c for c in vp.cargar_ceses() if c["plataforma"] != "Terra"]
    v2 = vp.evaluar(regs, ahora, sin_terra)
    assert "Terra" in [a["plataforma"] for a in v2["alarmas"]]


HAY_NODE = shutil.which("node") is not None


@pytest.mark.skipif(not HAY_NODE, reason="sin node")
def test_el_tablero_marca_los_dos_ceses_con_la_fecha_de_la_lista():
    """frontend/cese_plataformas.js trae cada cese de la lista (misma fecha y fuente) y dibuja «sin Terra» en un
    gráfico que cruza el 1-dic; en uno que no lo cruza no dibuja nada de Terra."""
    ceses = json.loads(LISTA.read_text(encoding="utf-8"))["ceses"]
    js = r"""
    const M = require(process.argv[process.argv.length - 1]);
    function chart(min, max) {
      const trazos = [];
      const ctx = new Proxy({}, { get: (o, k) => (k in o ? o[k] : (...a) => trazos.push([k, ...a])),
                                  set: (o, k, v) => { o[k] = v; return true; } });
      return { trazos, ctx, chartArea: { top: 10, bottom: 110, left: 0, right: 200 },
        scales: { x: { type: "time", min, max, getPixelForValue: t => (t - min) / (max - min) * 200 } } };
    }
    const p = M.crearPlugin(M.CESES);
    const t = Date.parse("2026-12-01T00:00:00Z"), D = 86400000;
    const dic = chart(t - 5 * D, t + 5 * D), nov = chart(Date.parse("2026-11-02T13:00:00Z") - D, t - 2 * D);
    const r = [p.afterDatasetsDraw(dic), p.afterDatasetsDraw(nov)];
    const rot = c => c.trazos.filter(x => x[0] === "fillText").map(x => x[1]);
    process.stdout.write(JSON.stringify([M.CESES.map(c => [c.plataforma, c.utc, c.fuente]), r, rot(dic), rot(nov)]));
    """
    out = subprocess.run(["node", "-e", js, str(MODULO)], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    lista_js, r, rot_dic, rot_nov = json.loads(out.stdout)
    assert sorted(lista_js) == sorted([c["plataforma"], c["desde_utc"], c["fuente"]] for c in ceses)
    assert r == [True, True]
    assert rot_dic == ["sin Terra"]
    assert rot_nov == ["sin Suomi NPP"]
