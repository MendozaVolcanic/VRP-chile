# -*- coding: utf-8 -*-
"""S194 (auditoría Codex ronda 2, C1-102 y C1-V202): marca de sólo display «cráter no medido».

POR QUÉ. Si el infrarrojo medio (MIR) llega sin dato sobre el cráter, la vía «código MIROVA» rellena el hueco con los
vecinos, más fríos: un foco aislado sale «sin anomalía» y uno con vecinos tibios publica sólo una parte de la potencia.
La vía ya lo anota en diag_codigo_mirova (#1060, #1077); el tablero no lo leía. Ahora lo avisa, junto con el barrido sin
posición sobre el cráter y la MIR saturada (potencia mínima). No se marcan el relleno bow-tie (el barrido vecino midió
ese suelo) ni el conteo sin separar de antes de #1077. Medición: experiments/_s194_mir_perdido/INFORME.md.

QUÉ FIJA, ejecutando frontend/crater_no_medido.js y funciones de index.html con node:
(1) craterNoMedido marca hueco de MIR, barrido sin posición y saturación, y NO marca el mismo record con esas claves en
    cero (control), ni el bow-tie, ni el conteo sin separar, ni el hueco de TIR, ni un record sin diagnóstico.
(2) Con el diagnóstico real de Nevados de Chillán (NOAA-20, 375 m, 2026-11-22 06:48; 25,806 MW, 1 píxel saturado) marca;
    con el de Láscar (NOAA-20, 2026-11-22 05:00; 6 píxeles, todos bow-tie) no.
(3) La marca no escribe en el record (congelado en modo estricto): no cambia valor, clase ni nivel.
(4) ultimaPasadaNoMedida elige la más reciente que pase el filtro, desde el corte, y salta la escena no medida.
(5) marcaCraterNoMedido y avisoCraterTarjeta de index.html: texto en la pasada marcada; null en su control; la tarjeta lo
    calla sólo si su detección es de otra pasada y más nueva.
(6) Las tres vistas cargan el módulo y lo usan en la tabla (dos ramas), el popup, las tarjetas y el conteo del diario.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? Cada prueba tiene su caso que no debe marcar y las
mutaciones a mano están contadas en experiments/_s194_mir_perdido/mutaciones_salida.txt. (2) ¿Y si la carga muriera?
`_node` exige returncode 0 y el módulo se carga con require: si falta el archivo, la prueba cae.
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

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="el módulo se prueba con node")


def _node(cuerpo, datos=None, previo=""):
    js = ("'use strict';\nconst C = require(" + json.dumps(str(MODULO)) + ");\n"
          "const DATOS = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" + previo + cuerpo)
    r = subprocess.run(["node", "-e", js], input=json.dumps(datos), capture_output=True, text=True, encoding="utf-8",
                       timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


D0 = {"motivo_vacio": None, "crater_sin_posicion": False, "px_mir_invalido_crater": 0, "px_saturados_crater": 0,
      "px_bowtie_crater": 0, "px_mir_hueco_crater": 0, "px_tir_hueco_crater": 0}
BASE = {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-22 05:06", "via_codigo_mirova": True, "vrp_mw": 0.0,
        "n_anomalous_pixels": 0, "anomaly_pixels": []}


def _rec(**diag):
    r = dict(BASE)
    r["diag_codigo_mirova"] = dict(D0, **diag)
    return r


# Diagnósticos reales de data/mirova_equivalent/ (main del 2026-11-22, 852279400), copiados para no depender del NRT.
CHILLAN_SAT = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-22 06:48", "via_codigo_mirova": True, "vrp_mw": 25.806,
               "distance_class": "summit", "n_anomalous_pixels": 18,
               "diag_codigo_mirova": dict(D0, roi="c13_crater", px_saturados_crater=1)}
LASCAR_BOWTIE = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-22 05:00", "via_codigo_mirova": True, "vrp_mw": 0,
                 "n_anomalous_pixels": 0,
                 "diag_codigo_mirova": dict(D0, roi="c13_crater", px_mir_invalido_crater=6, px_bowtie_crater=6)}


def test_marca_y_su_control():
    sin_separar = dict(BASE, diag_codigo_mirova={"motivo_vacio": None, "crater_sin_posicion": False,
                                                 "px_mir_invalido_crater": 4, "px_saturados_crater": 0})
    casos = [
        _rec(px_mir_invalido_crater=2, px_mir_hueco_crater=2),   # hueco de MIR: marca
        _rec(),                                                   # control: el mismo record sin la marca
        _rec(px_mir_invalido_crater=3, px_bowtie_crater=3),       # bow-tie: el barrido vecino midió ese suelo
        sin_separar,                                              # antes de #1077: bow-tie y hueco mezclados
        _rec(px_mir_invalido_crater=1, px_tir_hueco_crater=1),    # sólo la TIR: otro efecto
        _rec(crater_sin_posicion=True),                           # barrido sin posición sobre el cráter
        _rec(px_saturados_crater=2),                              # MIR saturada
        _rec(px_saturados_crater=None, px_bowtie_crater=None),    # MODIS: None es «no medido», no marca
        dict(BASE),                                               # sin diagnóstico (records anteriores a #1060)
        _rec(px_mir_hueco_crater=-1),                             # valor imposible: no marca
        _rec(px_mir_hueco_crater=1, px_saturados_crater=1, crater_sin_posicion=True),
    ]
    o = _node("process.stdout.write(JSON.stringify(DATOS.map(r => C.craterNoMedido(r))));", casos)
    assert o[0] == {"nMir": 2, "nSat": 0, "sinPosicion": False}
    assert o[1] is None and o[2] is None and o[3] is None and o[4] is None
    assert o[5] == {"nMir": 0, "nSat": 0, "sinPosicion": True}
    assert o[6] == {"nMir": 0, "nSat": 2, "sinPosicion": False}
    assert o[7] is None and o[8] is None and o[9] is None
    assert o[10] == {"nMir": 1, "nSat": 1, "sinPosicion": True}


def test_textos_para_el_operador():
    o = _node("""
const t = (m) => [C.textoCrater(m), C.tituloCrater(m)];
process.stdout.write(JSON.stringify([
  t({nMir: 1, nSat: 0, sinPosicion: false}), t({nMir: 3, nSat: 0, sinPosicion: false}),
  t({nMir: 0, nSat: 1, sinPosicion: false}), t({nMir: 0, nSat: 0, sinPosicion: true}),
  t({nMir: 2, nSat: 4, sinPosicion: true}), t(null)]));""")
    assert o[0][0] == "cráter no medido: MIR sin dato en 1 píxel"
    assert o[1][0] == "cráter no medido: MIR sin dato en 3 píxeles"
    assert o[2][0] == "MIR saturada en 1 píxel del cráter: la potencia puede ser mayor"
    assert o[3][0] == "cráter no medido: barrido sin posición sobre el cráter"
    assert o[4][0] == ("cráter no medido: MIR sin dato en 2 píxeles, barrido sin posición sobre el cráter; "
                       "MIR saturada en 4 píxeles del cráter: la potencia puede ser mayor")
    assert o[5] == ["", ""]
    assert "no es lo mismo que un cráter frío" in o[0][1] and "sólo avisa" in o[0][1]
    assert "es un mínimo" in o[2][1] and "frío" not in o[2][1]
    assert "sin latitud ni longitud" in o[3][1] and "infrarrojo medio" not in o[3][1]
    for par in o:
        for s in par:
            assert chr(0x2014) not in s and chr(0x2013) not in s   # sin guiones largos ni medios
            assert '"' not in s                                     # va dentro de un atributo title del popup


def test_records_reales():
    o = _node("""
process.stdout.write(JSON.stringify(DATOS.map(r => C.craterNoMedido(r))));""",
              [CHILLAN_SAT, dict(CHILLAN_SAT, diag_codigo_mirova=dict(CHILLAN_SAT["diag_codigo_mirova"],
                                                                      px_saturados_crater=0)), LASCAR_BOWTIE])
    assert o[0] == {"nMir": 0, "nSat": 1, "sinPosicion": False}
    assert o[1] is None
    assert o[2] is None


def test_no_escribe_en_el_record():
    o = _node("""
const congelar = (x) => { if (x && typeof x === 'object') { Object.values(x).forEach(congelar); Object.freeze(x); } return x; };
const r = congelar(DATOS);
const antes = JSON.stringify(r);
const m = C.craterNoMedido(r);
C.textoCrater(m); C.tituloCrater(m);
C.ultimaPasadaNoMedida([r], 0, null, (s) => Date.parse(s.replace(' ', 'T') + ':00Z'));
process.stdout.write(JSON.stringify([antes === JSON.stringify(r), !!m]));""",
              _rec(px_mir_invalido_crater=2, px_mir_hueco_crater=2, px_saturados_crater=1, crater_sin_posicion=True))
    assert o == [True, True]


def test_ultima_pasada_no_medida():
    hueco = {"px_mir_invalido_crater": 1, "px_mir_hueco_crater": 1}
    recs = [dict(_rec(**hueco), datetime_utc="2026-11-20 05:06"),
            dict(_rec(**hueco), datetime_utc="2026-11-21 05:30"),                       # la más reciente con marca
            dict(_rec(), datetime_utc="2026-11-21 06:10"),                              # más nueva pero sin marca
            dict(_rec(**hueco), datetime_utc="2026-11-21 07:00", filtrar=True),         # la vista la filtra
            dict(_rec(crater_sin_posicion=True, motivo_vacio="escena_invalida"),
                 datetime_utc="2026-11-21 08:00"),                                      # escena no medida: no es pasada
            dict(_rec(**hueco), datetime_utc="2026-11-18 05:00")]                       # antes del corte
    o = _node("""
const p = (s) => Date.parse(s.replace(' ', 'T') + ':00Z');
const a = C.ultimaPasadaNoMedida(DATOS, p('2026-11-19 00:00'), (r) => !r.filtrar, p);
const b = C.ultimaPasadaNoMedida(DATOS, p('2026-11-22 00:00'), null, p);
process.stdout.write(JSON.stringify([a && a.rec.datetime_utc, a && a.m.nMir, b]));""", recs)
    assert o == ["2026-11-21 05:30", 1, None]


def _fuente(src, nombre):
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index(") {", m.end()) + 2
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _previo_index():
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    return ("const CraterNoMedido = C;\n"
            "function el(tag, cls) { return {tag, className: cls || '', textContent: '', title: ''}; }\n"
            "function isSensorVisible(r) { return !r.oculto; }\n"
            "function parseUtcMs(s) { return Date.parse(s.replace(' ', 'T') + ':00Z'); }\n"
            + _fuente(src, "marcaCraterNoMedido") + "\n" + _fuente(src, "avisoCraterTarjeta") + "\n")


def test_marca_de_index_en_la_pasada_y_no_en_su_control():
    o = _node("""
const [a, b, c] = DATOS.map(r => marcaCraterNoMedido('marca-crater-no-medido', r));
process.stdout.write(JSON.stringify([a && a.textContent, a && a.title.length > 0, a && a.className, b, c]));""",
              [_rec(px_mir_invalido_crater=2, px_mir_hueco_crater=2), _rec(), LASCAR_BOWTIE], previo=_previo_index())
    assert o[0] == "⊘ cráter no medido: MIR sin dato en 2 píxeles" and o[1] is True
    assert o[2] == "marca-crater-no-medido"
    assert o[3] is None and o[4] is None


def test_aviso_de_la_tarjeta_de_index():
    # Fechas relativas a «ahora» (la tarjeta mira 48 h hacia atrás).
    o = _node("""
const hace = (h) => new Date(Date.now() - h * 3600000).toISOString().slice(0, 16).replace('T', ' ');
const marcado = Object.assign({}, DATOS.marcado, {datetime_utc: hace(5)});
const limpio = Object.assign({}, DATOS.limpio, {datetime_utc: hace(2)});
const viejo = Object.assign({}, DATOS.marcado, {datetime_utc: hace(60)});
const dia = Object.assign({}, DATOS.marcado, {datetime_utc: hace(1), _diurna: true});
const oculto = Object.assign({}, DATOS.marcado, {datetime_utc: hace(1), oculto: true});
const det = (r) => ({rec: r, ts: parseUtcMs(r.datetime_utc)});
const txt = (x) => x ? x.textContent : null;
process.stdout.write(JSON.stringify([
  txt(avisoCraterTarjeta('vc', [marcado, limpio], null)),                 // sin detección: avisa (el caso «sin anomalía»)
  txt(avisoCraterTarjeta('vc', [marcado, limpio], det(marcado))),         // la detección es la misma pasada: avisa
  txt(avisoCraterTarjeta('vc', [marcado, limpio], det(limpio))),          // detección de otra pasada más nueva: calla
  txt(avisoCraterTarjeta('vc', [limpio], null)),                          // control: nada marcado
  txt(avisoCraterTarjeta('vc', [viejo], null)),                           // fuera de 48 h
  txt(avisoCraterTarjeta('vc', [dia, oculto], null)),                     // de día o de un sensor oculto: no
  marcado.datetime_utc]));""",
              {"marcado": _rec(px_mir_invalido_crater=2, px_mir_hueco_crater=2), "limpio": _rec()},
              previo=_previo_index())
    assert o[0] == "⊘ Pasada del " + o[6] + " UTC (VIIRS_NOAA20_750): cráter no medido: MIR sin dato en 2 píxeles"
    assert o[1] == o[0]
    assert o[2] is None and o[3] is None and o[4] is None and o[5] is None


def test_las_tres_vistas_cargan_y_usan_el_modulo():
    for vista in ("index.html", "diario.html", "mosaico.html"):
        src = (FRONT / vista).read_text(encoding="utf-8")
        assert re.search(r'<script src="crater_no_medido\.js"></script>', src), vista
        assert "CraterNoMedido." in src, vista
    idx = (FRONT / "index.html").read_text(encoding="utf-8")
    assert idx.count('marcaCraterNoMedido("marca-crater-no-medido", r)') == 2   # las dos ramas de la tabla de pasadas
    assert "popupAgua + popupCumbre + popupCrater" in idx and "CraterNoMedido.craterNoMedido(r)" in idx
    assert 'avisoCraterTarjeta("vc-crater-no-medido", d.records, det)' in idx
    mos = (FRONT / "mosaico.html").read_text(encoding="utf-8")
    assert re.search(r"CraterNoMedido\.ultimaPasadaNoMedida\(records,\s*Date\.now\(\) - 48 \* 3600000, r => r\._diurna !== true,", mos)
    dia = (FRONT / "diario.html").read_text(encoding="utf-8")
    assert re.search(r"recs\.filter\(r => r\._diurna !== true && !\(r\.diag_codigo_mirova && r\.diag_codigo_mirova\.motivo_vacio\)"
                     r" && CraterNoMedido\.craterNoMedido\(r\)\)", dia)
    assert "stats.crater_no_medido" in dia
    css = (FRONT / "vista_volcan.css").read_text(encoding="utf-8")
    assert ".marca-crater-no-medido" in css and ".vc-crater-no-medido" in css
