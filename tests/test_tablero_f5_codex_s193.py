# -*- coding: utf-8 -*-
"""Hallazgos del frente 5 de la auditoría Codex ronda 2 en el tablero (S193): minigráfico de mosaico y comparación.

POR QUÉ. Son cosas que el operador lee mal sin que nada falle:
  * F5-102: el minigráfico de mosaico dibujaba igual un día sin ninguna pasada medida y un día que se miró sin ver calor
    (barra en cero, «sin detecciones»). El primero no dice nada del volcán; el segundo dice que estaba tranquilo.
  * F5-V202: el primer día del minigráfico salía en cero aunque esa noche hubo detección, porque el día empieza a
    medianoche UTC y los records se cortaban en «ahora menos 30 días» (las pasadas nocturnas caen entre 00 y 09 UTC).
  * F5-106: comparacion.html rotulaba «ratio mediano geométrico» a una media geométrica (Láscar 1,24 contra mediana 1,00).

Las funciones se ejecutan con node desde la página, nunca portadas. El recuadro de index (F5-V301) se prueba en
tests/test_tablero_evolucion_como_mirova_s184.py y la firma del predicado (F5-112, F5-V302) en
tests/test_comparacion_via_k_s183.py.
"""
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MOSAICO = RAIZ / "frontend" / "mosaico.html"
COMPARACION = RAIZ / "frontend" / "comparacion.html"
PERIODO_JS = RAIZ / "frontend" / "periodo.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}`."""
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré la función " + nombre)
    i = src.index("{", m.end())
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _ms(txt):
    return int(datetime.strptime(txt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)


def _node(tmp_path, js):
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout)


# ── Mosaico: minigráfico ────────────────────────────────────────────────────────────────────────────────────────────

AHORA = "2026-11-17 10:00"   # después de la hora de las pasadas nocturnas: el caso en que el primer día se vaciaba


def _sparkline(tmp_path, records, ahora=AHORA, src=None):
    """Ejecuta buildSparklineData de mosaico con el reloj en `ahora` y PERIODO = 30 días. eqVrpDisplay se reemplaza
    por el campo `v` del record: lo que se prueba es el armado por día, no el predicado (ese lo vigilan los guards)."""
    src = src if src is not None else MOSAICO.read_text(encoding="utf-8")
    partes = [_fuente(src, "buildSparklineData"), _fuente(src, "parseUtcMs"), _fuente(src, "fmtVRP"),
              _fuente(src, "esValorCensurado"), "const PATH_D_CAP_MW = 5.0;"]
    if "function etiquetaDiaSparkline(" in src:
        partes.append(_fuente(src, "etiquetaDiaSparkline"))
    js = ("const Periodo = require(%s);\n" % json.dumps(str(PERIODO_JS))
          + "const PERIODO = { dias: 30 };\n"
          + "function eqVrpDisplay(r) { return r.v || 0; }\n"
          + "\n".join(partes) + "\n"
          + "Date.now = () => %d;\n" % _ms(ahora)
          + "const DATOS = %s;\n" % json.dumps(records)
          + "const d = buildSparklineData(DATOS, 5);\n"
          + "const etq = typeof etiquetaDiaSparkline === 'function'"
          + " ? d.values.map((v, i) => etiquetaDiaSparkline(v, d.observado ? d.observado[i] : null)) : null;\n"
          + "console.log(JSON.stringify({ dias: d.labels.map(x => x.toISOString().slice(0, 10)), values: d.values,"
          + " observado: d.observado || null, etq }));\n")
    return _node(tmp_path, js)


def _dia(o, fecha):
    i = o["dias"].index(fecha)
    return {"v": o["values"][i], "obs": (o["observado"] or [None] * (i + 1))[i],
            "etq": (o["etq"] or [None] * (i + 1))[i]}


def test_f5_v202_el_primer_dia_va_entero(tmp_path):
    """Reloj 2026-11-17 10:00 UTC: el primer día del gráfico es el 2026-10-18 y su pasada de las 05:00 (antes de «ahora
    menos 30 días», 10:00) tiene que contar. Antes el día salía en cero."""
    o = _sparkline(tmp_path, [{"datetime_utc": "2026-10-18 05:00", "v": 3.0},
                              {"datetime_utc": "2026-11-17 05:00", "v": 1.0}])
    assert o["dias"][0] == "2026-10-18", o["dias"][:2]
    assert _dia(o, "2026-10-18")["v"] == 3.0, o
    assert _dia(o, "2026-11-17")["v"] == 1.0, o
    # lo anterior a la medianoche del primer día sigue fuera
    o2 = _sparkline(tmp_path, [{"datetime_utc": "2026-10-17 23:00", "v": 9.0}])
    assert 9.0 not in o2["values"], o2


def test_f5_102_dia_sin_pasada_distinto_de_dia_sin_deteccion(tmp_path):
    recs = [{"datetime_utc": "2026-11-10 05:00", "v": 0},                      # se miró, nada
            {"datetime_utc": "2026-11-11 05:00", "v": 2.5},                    # se miró, calor
            {"datetime_utc": "2026-11-13 05:00", "v": 0,                       # escena sin datos: no es pasada medida
             "diag_codigo_mirova": {"motivo_vacio": "escena_invalida"}}]
    o = _sparkline(tmp_path, recs)
    medido, calor = _dia(o, "2026-11-10"), _dia(o, "2026-11-11")
    sin_pasada, escena_vacia = _dia(o, "2026-11-12"), _dia(o, "2026-11-13")
    assert (medido["v"], medido["obs"]) == (0, True), medido
    assert (calor["v"], calor["obs"]) == (2.5, True), calor
    assert (sin_pasada["v"], sin_pasada["obs"]) == (None, False), sin_pasada
    assert (escena_vacia["v"], escena_vacia["obs"]) == (None, False), escena_vacia
    assert medido["etq"] == "pasadas medidas, sin detecciones", medido
    assert sin_pasada["etq"] == "sin pasadas medidas", sin_pasada
    assert calor["etq"].startswith("VRP: "), calor


def test_f5_102_el_grafico_dibuja_los_dias_sin_pasada():
    """La raya gris de «sin pasadas medidas» es una segunda serie del gráfico, con valor sólo donde values es null, y
    el máximo del eje ignora los null (Math.max con un null da 0 y con NaN da NaN)."""
    src = MOSAICO.read_text(encoding="utf-8")
    f = _fuente(src, "renderSparkline")
    assert "sparkData.values.map(v => (v == null ? rayaSinPasada : null))" in f
    assert "data: sinPasada" in f
    assert "Math.max(0, ...sparkData.values.filter(v => v != null))" in f
    assert "etiquetaDiaSparkline(sparkData.values[ctx.dataIndex], sparkData.observado[ctx.dataIndex])" in f


def test_control_el_instrumento_ve_el_corte_viejo(tmp_path):
    """Control (A110): sobre una copia con el corte en «ahora menos 30 días» el primer día vuelve a salir en cero. Si
    no, la prueba de F5-V202 no vería la regresión."""
    src = MOSAICO.read_text(encoding="utf-8")
    viejo = "if (!Number.isFinite(t) || t < dayStart || t > now) continue;"
    assert src.count(viejo) == 1
    o = _sparkline(tmp_path, [{"datetime_utc": "2026-10-18 05:00", "v": 3.0}],
                   src=src.replace(viejo, "if (!Number.isFinite(t) || t < t0 || t > now) continue;"))
    assert _dia(o, "2026-10-18")["v"] != 3.0, o


# ── Comparación: cociente mediano ──────────────────────────────────────────────────────────────────────────────────

def test_f5_106_comparacion_muestra_la_mediana_del_cociente(tmp_path):
    src = COMPARACION.read_text(encoding="utf-8")
    f = _fuente(src, "renderScatter")
    assert "const medRatio = median(cocientes);" in f, "el cociente mostrado tiene que ser la mediana"
    rotulo = f[f.index('el("scatter-stat").innerHTML'):]
    rotulo = rotulo[:rotulo.index(";")]
    assert not re.search(r"\bgeom[eé]tric", rotulo), "el rótulo no puede decir geométrico: el número es una mediana"
    assert "ratio mediano nuestro/MIROVA" in rotulo
    # la mediana de la página, ejecutada: tres días con cocientes 0,5, 0,5 y 8 dan 0,5 (la media geométrica daría 1,26)
    o = _node(tmp_path, _fuente(src, "median") + "\nconsole.log(JSON.stringify(median([0.5, 8, 0.5])));\n")
    assert o == 0.5
