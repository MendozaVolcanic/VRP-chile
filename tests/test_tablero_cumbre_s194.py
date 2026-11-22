# -*- coding: utf-8 -*-
"""S194: marca de sólo display «también hay calor en la cumbre» en las pasadas que el tablero ubica lejos.

POR QUÉ. En una pasada puede haber un píxel tibio sobre el cráter y, a varios km, un cúmulo más radiante (salar o roca
tibia del altiplano, un borde de nube). La regla de posición «radiante» (D8') pone el record en ese cúmulo: la pasada
queda lejana y el operador no ve que también hubo calor en la cumbre. Así quedaban fuera de vista 12 alertas protegidas
de MIROVA vistas sólo por su OCR (Codex F12-V301). Mover la posición se rechazó (experiments/_s193_radiante_variante/
INFORME.md); la marca sólo avisa. Medición: experiments/_s194_marcador_cumbre/INFORME.md (218 de 707 pasadas lejanas
nocturnas del 2026-03-01 al 2026-11-18 la llevan, las 12 de Codex entre ellas).

QUÉ FIJA, ejecutando frontend/cumbre.js y funciones de las vistas con node:
(1) calorEnCumbre marca una pasada lejana de la vía con un alertado dentro del radio y NO marca el mismo record sin ese
    píxel (control), ni uno de la cumbre, ni uno de otra vía, ni sin radio; el borde (dist = radio) marca.
(2) Con los píxeles reales de una de las 12 (Isluga, Suomi NPP, 2026-04-07 06:12): 1 píxel a 0,88 km; sin él, nada.
(3) La marca no escribe en el record (record congelado en modo estricto): no cambia posición, clase ni potencia.
(4) ultimaLejanaConCumbre elige la más reciente que pase el filtro de la vista y desde el corte.
(5) Las tres vistas cargan el módulo y lo usan; marcaCumbre de index.html da el elemento con el texto en la pasada
    marcada y null en su control y en una pasada de la cumbre.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? Cada prueba tiene su caso que no debe marcar y las
mutaciones a mano están contadas en experiments/_s194_marcador_cumbre/INFORME.md. (2) ¿Y si la carga muriera? `_node`
exige returncode 0 y el módulo se carga con require: si falta el archivo, la prueba cae.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"
MODULO = FRONT / "cumbre.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="el módulo se prueba con node")


def _node(cuerpo, datos=None, previo=""):
    js = ("'use strict';\nconst C = require(" + json.dumps(str(MODULO)) + ");\n"
          "const DATOS = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" + previo + cuerpo)
    r = subprocess.run(["node", "-e", js], input=json.dumps(datos), capture_output=True, text=True, encoding="utf-8",
                       timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


LEJOS = [{"lat": -19.0, "lon": -68.7, "dist_km": 15.2, "bt_k": 330.0},
         {"lat": -19.0, "lon": -68.71, "dist_km": 15.6, "bt_k": 320.0}]
CERCA = {"lat": -19.15, "lon": -68.83, "dist_km": 0.7, "bt_k": 300.0}
BASE = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-20 05:06", "via_codigo_mirova": True, "vrp_mw": 2.0,
        "n_anomalous_pixels": 3, "distance_class": "far", "final_hotspot_dist_km": 15.4,
        "primary_cluster": {"vrp_mw": 2.0, "n_pixels": 2, "centroid_dist_km": 15.4}}


def _rec(**kw):
    r = dict(BASE, anomaly_pixels=[CERCA] + LEJOS)
    r.update(kw)
    return r


def test_marca_y_su_control():
    casos = [
        [_rec(), 5.0],                                                  # marca
        [_rec(anomaly_pixels=LEJOS, n_anomalous_pixels=2), 5.0],        # control: sin el píxel en la cumbre
        [_rec(distance_class="summit"), 5.0],                           # la cumbre ya la muestra el tablero
        [_rec(via_codigo_mirova=False), 5.0],                           # otra vía: lista y origen no garantizados
        [_rec(), None],                                                 # sin radio (los 34)
        [_rec(), 0.7],                                                  # borde: dist = radio marca
        [_rec(), 0.69],                                                 # justo fuera del radio
        [_rec(anomaly_pixels=[CERCA, dict(CERCA, dist_km=0.3, bt_k=290.0)] + LEJOS), 5.0],
    ]
    o = _node("process.stdout.write(JSON.stringify(DATOS.map(([r, i]) => C.calorEnCumbre(r, i))));", casos)
    assert o[0] == {"n": 1, "dMinKm": 0.7, "btMaxK": 300.0}
    assert o[1] is None and o[2] is None and o[3] is None and o[4] is None
    assert o[5] == {"n": 1, "dMinKm": 0.7, "btMaxK": 300.0}
    assert o[6] is None
    assert o[7] == {"n": 2, "dMinKm": 0.3, "btMaxK": 300.0}


def test_textos_para_el_operador():
    o = _node("""
const uno = {n: 1, dMinKm: 0.88, btMaxK: 272.2}, dos = {n: 4, dMinKm: 0.14, btMaxK: 301};
process.stdout.write(JSON.stringify([C.textoCumbre(uno), C.textoCumbre(dos), C.textoCumbre(null),
  C.tituloCumbre(uno, DATOS, 5)]));""", _rec(final_hotspot_dist_km=17.186))
    assert o[0] == "también hay calor en la cumbre (1 píxel a 0,9 km)"
    assert o[1] == "también hay calor en la cumbre (4 píxeles, el más cercano a 0,1 km)"
    assert o[2] == ""
    assert "17 km del cráter" in o[3] and "5,0 km" in o[3] and "no la cambia" in o[3]
    for t in o:
        assert chr(0x2014) not in t and chr(0x2013) not in t   # sin guiones largos ni medios


def test_record_real_de_las_12_de_codex():
    # Isluga, Suomi NPP, 2026-04-07 06:12 (experiments/_s193_radiante_variante/INFORME.md §3): MIROVA 4,12 MW por OCR
    # en la cumbre; la vía publica 4,125 MW con el cúmulo más radiante a 17,186 km. Píxeles de data/mirova_equivalent/
    # Isluga.json (main del 2026-11-21), copiados para no depender de un reproceso.
    pix = [{"dist_km": d, "bt_k": b} for d, b in ((17.35, 312.04), (17.17, 306.62), (17.21, 292.11),
                                                  (17.02, 298.85), (0.88, 272.2))]
    r = _rec(sensor="VIIRS_SNPP", datetime_utc="2026-04-07 06:12", vrp_mw=4.125, n_anomalous_pixels=5,
             final_hotspot_dist_km=17.186, anomaly_pixels=pix)
    sin = dict(r, anomaly_pixels=pix[:4], n_anomalous_pixels=4)
    o = _node("process.stdout.write(JSON.stringify([C.calorEnCumbre(DATOS[0], 5), C.calorEnCumbre(DATOS[1], 5)]));",
              [r, sin])
    assert o[0] == {"n": 1, "dMinKm": 0.88, "btMaxK": 272.2}
    assert o[1] is None


def test_no_escribe_en_el_record():
    # Congelado a fondo: en modo estricto cualquier escritura lanza y la prueba cae.
    o = _node("""
const congelar = (x) => { if (x && typeof x === 'object') { Object.values(x).forEach(congelar); Object.freeze(x); } return x; };
const r = congelar(DATOS);
const antes = JSON.stringify(r);
const m = C.calorEnCumbre(r, 5);
C.textoCumbre(m); C.tituloCumbre(m, r, 5);
C.ultimaLejanaConCumbre([r], 5, 0, null, (s) => Date.parse(s.replace(' ', 'T') + ':00Z'));
process.stdout.write(JSON.stringify([antes === JSON.stringify(r), !!m]));""", _rec())
    assert o == [True, True]


def test_ultima_lejana_con_cumbre():
    recs = [_rec(datetime_utc="2026-11-20 05:06"),
            _rec(datetime_utc="2026-11-21 05:30"),                                  # la más reciente con marca
            _rec(datetime_utc="2026-11-21 06:10", anomaly_pixels=LEJOS),            # más nueva pero sin marca
            _rec(datetime_utc="2026-11-21 07:00", vrp_mw=0.0, filtrar=True),        # la vista la filtra
            _rec(datetime_utc="2026-11-18 05:00")]                                  # antes del corte
    o = _node("""
const p = (s) => Date.parse(s.replace(' ', 'T') + ':00Z');
const desde = p('2026-11-19 00:00');
const a = C.ultimaLejanaConCumbre(DATOS, 5, desde, (r) => !r.filtrar, p);
const b = C.ultimaLejanaConCumbre(DATOS, 5, p('2026-11-22 00:00'), null, p);
process.stdout.write(JSON.stringify([a && a.rec.datetime_utc, a && a.m.n, b]));""", recs)
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


def test_marca_de_index_en_la_pasada_y_no_en_su_control():
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    previo = ("const CumbreTablero = C;\n"
              "function el(tag, cls) { return {tag, className: cls || '', textContent: '', title: ''}; }\n"
              + _fuente(src, "marcaCumbre") + "\n")
    o = _node("""
const v = {name: 'Isluga', inner_radius_km: 5};
const [a, b, c] = DATOS.map(r => marcaCumbre('marca-cumbre', v, r));
const sinRadio = marcaCumbre('marca-cumbre', {name: 'Ollague'}, DATOS[0]);
process.stdout.write(JSON.stringify([a && a.textContent, a && a.title.length > 0, b, c, sinRadio]));""",
              [_rec(), _rec(anomaly_pixels=LEJOS), _rec(distance_class="summit")], previo=previo)
    assert o[0].endswith("también hay calor en la cumbre (1 píxel a 0,7 km)") and o[1] is True
    assert o[2] is None and o[3] is None and o[4] is None


def test_las_tres_vistas_cargan_y_usan_el_modulo():
    for vista in ("index.html", "diario.html", "mosaico.html"):
        src = (FRONT / vista).read_text(encoding="utf-8")
        assert re.search(r'<script src="cumbre\.js"></script>', src), vista
        assert "CumbreTablero." in src, vista
    idx = (FRONT / "index.html").read_text(encoding="utf-8")
    assert idx.count('marcaCumbre("marca-cumbre", v, r)') == 2   # las dos ramas de la tabla de pasadas
    assert "popupCumbre" in idx and "CumbreTablero.ultimaLejanaConCumbre(" in idx
    assert "CumbreTablero.ultimaLejanaConCumbre(" in (FRONT / "mosaico.html").read_text(encoding="utf-8")
    assert "CumbreTablero.calorEnCumbre(" in (FRONT / "diario.html").read_text(encoding="utf-8")
    # Las tarjetas y el conteo del diario son de la noche, como sus cifras desde #1086 (de día puede ser reflejo solar)
    assert re.search(r"r => r\._diurna !== true && isValidDetection\(r\) && isSensorVisible", idx)
    assert re.search(r"r => r\._diurna !== true && isValidDetection\(r\), parseUtcMs",
                     (FRONT / "mosaico.html").read_text(encoding="utf-8"))
    assert re.search(r"recs\.filter\(r => r\._diurna !== true && isValidDetection\(r\) && CumbreTablero\.calorEnCumbre",
                     (FRONT / "diario.html").read_text(encoding="utf-8"))
