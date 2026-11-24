# -*- coding: utf-8 -*-
"""Auditoría Codex ronda 3, R3F5-101 y R3F5-V101 (S198): la marca «cráter no medido» llega a los gráficos, y un fondo de
0 K se muestra como «sin fondo».

POR QUÉ. La marca de S194 (#1095) llegaba a la tabla, el popup, las tarjetas de 48 h y el conteo del diario, pero no a los
gráficos: la evolución de index dibujaba la pasada con el cráter no medido como «se midió, nada» y su recuadro decía «sin
anomalía»; el minigráfico de mosaico contaba ese día como observado; el gráfico del diario no la mostraba; la protegida
saturada de Chillán (2026-11-22 06:48, 25,81 MW contra 29,65 de MIROVA) salía como potencia sin aviso. Pasadas las 48 h,
el operador no podía distinguir «no se pudo medir el cráter» de «el cráter está frío». Aparte, 13 records de los Tier A
traen t_bg_k = 0 (fondo no estimado) y la tabla de index lo mostraba como -273,1 °C.

QUÉ FIJA, ejecutando con node frontend/crater_no_medido.js y funciones reales extraídas de las tres vistas:
(1) esNoMedido, marcasGrafico y fondoK, cada uno con su control.
(2) index: todasPasadasEvol pone «no_medido» (fila de arriba, «no se pudo medir») a la pasada marcada sin palito, y su
    control queda «nada»; el recuadro de la última pasada lo dice y no dice «sin anomalía»; la pasada publicada con la MIR
    saturada lleva raya naranja y «la potencia puede ser mayor».
(3) mosaico: el día cuya única pasada no midió el cráter no es «observado» y su tooltip lo dice; el control sí es observado.
(4) diario: marcasCnmDiario marca el día de la pasada nocturna marcada y no el de la diurna ni el de la escena vacía.
(5) index: fondoMedidoK devuelve null con 0 K (la tabla escribe «sin fondo») y el fondo real con un valor físico.
(6) Las tres vistas enganchan CraterNoMedido.plugin a sus gráficos.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código de antes? Cada caso tiene un control y el estado que se
exige («no_medido», el texto del tooltip) no existía antes de este cambio. (2) ¿Y si la carga muriera? `_node` exige
returncode 0 y cada función se extrae del texto real: si no está, la prueba cae. Medición sobre los datos reales (las 38
marcas): experiments/_s198_r3f5_evolucion/.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"
MODULO = FRONT / "crater_no_medido.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="las vistas se prueban con node")


def _fuente(src, nombre):
    m = re.search(r"\nfunction " + re.escape(nombre) + r"\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index("{", m.end())
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start() + 1:j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _const(src, nombre):
    m = re.search(r"\nconst " + re.escape(nombre) + r"\s*=", src)
    if not m:
        raise AssertionError("no encontré const " + nombre)
    prof = 0
    for j in range(m.end(), len(src)):
        c = src[j]
        prof += {"{": 1, "}": -1, "(": 1, ")": -1, "[": 1, "]": -1}.get(c, 0)
        if c == ";" and prof == 0:
            return src[m.start() + 1:j + 1]
    raise AssertionError("const sin cerrar " + nombre)


def _node(cuerpo, datos=None, previo=""):
    js = ("'use strict';\nconst C = require(" + json.dumps(str(MODULO)) + ");\nconst CraterNoMedido = C;\n"
          "const DATOS = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n"
          "function parseUtcMs(s) { return Date.parse(s.replace(' ', 'T') + ':00Z'); }\n" + previo + cuerpo)
    r = subprocess.run(["node", "-e", js], input=json.dumps(datos), capture_output=True, text=True, encoding="utf-8",
                       timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


D0 = {"motivo_vacio": None, "crater_sin_posicion": False, "px_mir_invalido_crater": 0, "px_saturados_crater": 0,
      "px_bowtie_crater": 0, "px_mir_hueco_crater": 0, "px_tir_hueco_crater": 0}


def _rec(dt="2026-11-22 05:06", y=0.0, **diag):
    return {"sensor": "VIIRS_NOAA20", "datetime_utc": dt, "via_codigo_mirova": True, "vrp_mw": y, "_y": y,
            "n_anomalous_pixels": 0, "anomaly_pixels": [], "t_bg_k": 250.0, "diag_codigo_mirova": dict(D0, **diag)}


def test_modulo_y_sus_controles():
    o = _node("""
const [hueco, sinPos, sat, limpio, vacio] = DATOS.recs;
process.stdout.write(JSON.stringify({
  nm: [hueco, sinPos, sat, limpio].map(r => C.esNoMedido(C.craterNoMedido(r))),
  marcas: C.marcasGrafico(DATOS.recs, null, parseUtcMs).map(m => [m.noMedido, m.sat]),
  fondo: [0, 250.3, null, NaN, -3].map(k => C.fondoK({t_bg_k: k})),
  plugin: typeof C.plugin.afterDatasetsDraw}));""",
              {"recs": [_rec(px_mir_hueco_crater=2), _rec(crater_sin_posicion=True), _rec(px_saturados_crater=1),
                        _rec(), _rec(px_mir_hueco_crater=3, motivo_vacio="escena_invalida")]})
    assert o["nm"] == [True, True, False, False]
    assert o["marcas"] == [[True, False], [True, False], [False, True]]   # ni el limpio ni la escena vacía
    assert o["fondo"] == [None, 250.3, None, None, None]
    assert o["plugin"] == "function"


def _previo_index():
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    stubs = ("function isThermalArtifact() { return false; }\n"
             "function mirovaEqVrpDisplay(r) { return r._y || 0; }\n"
             "function escenaSinDato(r) { return r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio ? 'escena sin datos' : null; }\n"
             "function isValidDetection() { return false; }\n"
             "function distanciaDePasada() { return 1; }\n"
             "function sensorGroup() { return 'VIIRS375'; }\n"
             "function getLevel(v) { return v > 0 ? {key: 'low', label: 'Bajo'} : {key: 'nd', label: 'Sin dato'}; }\n"
             "const ETIQUETA_SENSOR = {VIIRS375: 'VIIRS 375 m'};\n"
             "function textoCenitEvol() { return ''; }\nfunction esOblicuaEvol() { return false; }\n"
             "function haceEvol() { return 'hace 1 h'; }\nfunction mwEvol(x) { return x.toFixed(2); }\n"
             "const EVOL_EXTREMO_MW = 10000;\n")
    return stubs + "\n".join([_const(src, "EVOL_MISMA_PASADA_MS"), _const(src, "EVOL_PRIORIDAD_ESTADO"),
                              _const(src, "EVOL_COLOR_MARCA"), _const(src, "EVOL_FILA_MARCA")]) + "\n" + "\n".join(
        _fuente(src, f) for f in ("todasPasadasEvol", "vrpPublicadoEvol", "ultimaPasadaEvol", "textoUltimaPasadaEvol",
                                  "marcasEvol", "fondoMedidoK")) + "\n"


def test_evolucion_de_index():
    o = _node("""
const caso = (rs) => { const p = todasPasadasEvol(rs, 5); const u = ultimaPasadaEvol(p, false);
  return {estados: p.map(x => x.estado), marcas: marcasEvol(p).map(m => [m.estado, EVOL_FILA_MARCA[m.estado]]),
          recuadro: textoUltimaPasadaEvol(u, Date.now(), false, null).texto}; };
process.stdout.write(JSON.stringify({hueco: caso([DATOS.hueco]), limpio: caso([DATOS.limpio]),
  sat: caso([DATOS.sat]), mismaPasada: caso([DATOS.limpio750, DATOS.hueco])}));""",
              {"hueco": _rec(px_mir_hueco_crater=2), "limpio": _rec(),
               "sat": _rec(y=25.806, px_saturados_crater=1),
               "limpio750": dict(_rec(dt="2026-11-22 05:04"), sensor="VIIRS_NOAA20_750")}, previo=_previo_index())
    assert o["hueco"]["estados"] == ["no_medido"]
    assert o["hueco"]["marcas"] == [["no_medido", 0]]                      # fila de arriba: no se pudo medir
    assert "cráter no medido: MIR sin dato en 2 píxeles" in o["hueco"]["recuadro"]
    assert "sin anomalía" not in o["hueco"]["recuadro"]
    assert o["limpio"]["estados"] == ["nada"] and o["limpio"]["marcas"] == [["nada", 1]]   # control
    assert "sin anomalía" in o["limpio"]["recuadro"] and "⊘" not in o["limpio"]["recuadro"]
    assert o["sat"]["estados"] == ["crater"] and o["sat"]["marcas"] == [["no_medido", 0]]
    assert "la potencia puede ser mayor" in o["sat"]["recuadro"]
    # la misma pasada vista por 750 (nada) y 375 (cráter no medido): el recuadro dice lo que no se midió
    assert "cráter no medido" in o["mismaPasada"]["recuadro"]


def test_fondo_cero_en_index():
    o = _node("process.stdout.write(JSON.stringify([fondoMedidoK({t_bg_k: 0}), fondoMedidoK({t_bg_k: 251.2}), "
              "fondoMedidoK({})]));", None, previo=_previo_index())
    assert o == [None, 251.2, None]
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    assert 'tbg != null ? k2c(tbg) : (r.t_bg_k === 0 ? "sin fondo" : "—")' in src
    assert 'tBg: (typeof r.t_bg_k === "number" && r.t_bg_k > 0) ? r.t_bg_k : null, sinFondo: r.t_bg_k === 0' in src
    assert "k2c(tbg)," not in src   # la forma de antes, que escribía -273,1 °C


def _previo_mosaico():
    src = (FRONT / "mosaico.html").read_text(encoding="utf-8")
    return ("const Periodo = {intervalo: () => [Date.parse(DATOS.t0), Date.parse(DATOS.t1)]};\nconst PERIODO = null;\n"
            "function eqVrpDisplay(r) { return r._y || 0; }\nfunction fmtVRP(v) { return String(v); }\n"
            + _fuente(src, "buildSparklineData") + "\n" + _fuente(src, "etiquetaDiaSparkline") + "\n")


def test_minigrafico_de_mosaico():
    o = _node("""
const s = buildSparklineData(DATOS.recs, 5);
const i = (d) => s.labels.findIndex(x => x.toISOString().slice(0, 10) === d);
const et = (d) => etiquetaDiaSparkline(s.values[i(d)], s.observado[i(d)], s.noMedido[i(d)], s.sat[i(d)]);
process.stdout.write(JSON.stringify({obs: [s.observado[i('2026-11-20')], s.observado[i('2026-11-21')]],
  et: [et('2026-11-20'), et('2026-11-21'), et('2026-11-22')]}));""",
              {"t0": "2026-11-20T00:00:00Z", "t1": "2026-11-22T12:00:00Z",
               "recs": [_rec(dt="2026-11-20 05:00", px_mir_hueco_crater=2), _rec(dt="2026-11-21 05:00"),
                        _rec(dt="2026-11-22 05:00", y=25.8, px_saturados_crater=1)]},
              previo=_previo_mosaico())
    assert o["obs"] == [False, True]                                        # marcado no es observado; control sí
    assert o["et"][0].startswith("⊘ cráter no medido")
    assert o["et"][1] == "pasadas medidas, sin detecciones"
    assert "la potencia puede ser mayor" in o["et"][2]


def test_marcas_del_diario():
    src = (FRONT / "diario.html").read_text(encoding="utf-8")
    previo = "function enPeriodo() { return true; }\n" + _fuente(src, "marcasCnmDiario") + "\n"
    o = _node("process.stdout.write(JSON.stringify(marcasCnmDiario({records: DATOS})));",
              [_rec(dt="2026-11-20 05:00", px_mir_hueco_crater=2), dict(_rec(dt="2026-11-21 15:00", px_mir_hueco_crater=2), _diurna=True),
               _rec(dt="2026-11-22 05:00", px_mir_hueco_crater=2, motivo_vacio="escena_invalida"), _rec(dt="2026-11-23 05:00"),
               _rec(dt="2026-11-24 05:00", px_saturados_crater=1)], previo=previo)
    assert o == [{"x": "2026-11-20", "noMedido": True, "sat": False}, {"x": "2026-11-24", "noMedido": False, "sat": True}]


def test_las_tres_vistas_enganchan_el_plugin():
    idx = (FRONT / "index.html").read_text(encoding="utf-8")
    assert '"no_medido"' in idx and "no_medido: 0" in idx
    assert "CraterNoMedido.textoCrater(p.cnm)" in idx                       # tooltip y recuadro
    mos = (FRONT / "mosaico.html").read_text(encoding="utf-8")
    assert "[CraterNoMedido.plugin]" in mos and "craterNoMedido: { marcas: marcasCnm }" in mos
    dia = (FRONT / "diario.html").read_text(encoding="utf-8")
    assert "[CraterNoMedido.plugin]" in dia and "chartConfig(datasets, marcasCnm)" in dia
