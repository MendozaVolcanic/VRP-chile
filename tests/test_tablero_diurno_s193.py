# -*- coding: utf-8 -*-
"""S193: el tablero deja de suponer que toda pasada nuestra es nocturna (antes de encender el día en MODIS).

POR QUÉ. El A/B diurno sobre la vía (issue #813, PR #1084) terminó con la decisión de Nicolás de encender la rama diurna
sólo en MODIS (`enable_daytime_modis`), en un PR de perfil que se mergea DESPUÉS de éste. Desde ahí el NRT escribe records
MODIS diurnos en el mismo JSON que los nocturnos. El tablero los leía mal en dos sentidos: (1) la frescura del monitoreo
(30 h, 72 h y el modelo bimodal del hueco entre pasadas de proximaPasadaEsperada) está calibrada sobre el ritmo
nocturno, y una pasada de día en medio del hueco hacía ver «al día» un volcán cuyas pasadas nocturnas no llegan, o partía
el hueco y hacía gritar «pasada vencida» cada tarde; (2) las series diarias sumaban en silencio una lectura que puede ser
reflejo solar a la serie nocturna.

QUÉ FIJA, ejecutando en node el código real: (a) frontend/diurno.js calcula la elevación solar igual que
pipeline/store.py::_solar_elevation (la compuerta que decide si un record diurno se publica), sobre una grilla de lugares
y fechas; (b) los 5 records MODIS crepusculares de main (cenit solar del gránulo bajo 90°, guardados por store como
nocturnos) siguen siendo nocturnos, y los diurnos del A/B son diurnos; (c) las tres vistas cargan el módulo y marcan los
records; (d) la frescura (index, diario, mosaico) y la próxima pasada ignoran lo diurno; (e) la última detección de la
tarjeta es nocturna salvo que se pida la diurna; (f) los soles propios sólo llevan pasadas diurnas; (g) diario cuenta lo
diurno aparte; (h) las coordenadas de las vistas son las de volcanoes.yaml.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? Cada prueba de comportamiento trae su control: los
mismos records SIN la marca `_diurna` dan otro resultado, así que una función que no mirara la marca no pasaría.
(2) ¿Y si la extracción muriera? `_fuente` lanza si no encuentra la función y node falla con mensaje si no corre.
"""
import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"
MODULO = FRONT / "diurno.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}`. Copia de la de test_tablero_f5_rotulos_s192.py."""
    m = re.search(r"(?<![A-Za-z0-9_])(?:async\s+)?function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index(") {", m.end()) + 2
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _correr(tmp_path, js):
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _node(tmp_path, pagina, nombres, cuerpo, previo=""):
    src = (FRONT / pagina).read_text(encoding="utf-8")
    return _correr(tmp_path, previo + "\n" + "\n".join(_fuente(src, n) for n in nombres) + "\n" + cuerpo)


def _modulo(tmp_path, cuerpo):
    return _correr(tmp_path, "const D = require(" + json.dumps(str(MODULO)) + ");\n" + cuerpo)


# ── (a) y (b): la definición ────────────────────────────────────────────────────────────────────────────────────────

def test_la_elevacion_es_la_de_store(tmp_path):
    from pipeline.store import _solar_elevation
    lugares = [(-18.0, -69.3), (-23.369, -67.732), (-36.863, -71.377), (-42.833, -72.646), (-55.0, -70.0)]
    t0 = datetime(2026, 1, 1, 0, 0)
    fechas = [t0 + timedelta(minutes=37 * k) for k in range(0, 365 * 24 * 60 // 37, 9)]   # todo el año, horas variadas
    casos = [(lat, lon, f.strftime("%Y-%m-%d %H:%M")) for lat, lon in lugares for f in fechas]
    js = "const C = " + json.dumps(casos) + ";\nprocess.stdout.write(JSON.stringify(C.map(c => D.elevacionSolar(c[0], c[1], c[2]))));"
    out = _modulo(tmp_path, js)
    assert len(out) == len(casos) > 2000
    for (lat, lon, f), e_js in zip(casos, out):
        e_py = _solar_elevation(lat, lon, datetime.strptime(f, "%Y-%m-%d %H:%M"))
        assert abs(e_js - e_py) < 1e-9, (lat, lon, f, e_js, e_py)
    assert any(e > 0 for e in out) and any(e < 0 for e in out)   # la grilla cruza el horizonte


def test_crepusculares_de_main_son_noche_y_las_del_ab_son_dia(tmp_path):
    # Los 5 records MODIS de data/mirova_equivalent (main, 2026-11-21) con solar_zenith_deg bajo 90 que store guardó como
    # nocturnos: con el cenit del record se habrían marcado de día. Y 3 pasadas diurnas del A/B (W7, Nevados de Chillán).
    casos = [
        ("2026-06-09 12:20", -42.833, -72.646, False), ("2026-07-17 21:30", -42.833, -72.646, False),
        ("2026-07-25 21:40", -38.692, -71.729, False), ("2026-07-25 21:40", -39.42, -71.93, False),
        ("2026-07-25 21:40", -40.59, -72.117, False),
        ("2026-10-16 12:45", -36.863, -71.377, True), ("2026-10-17 20:50", -36.863, -71.377, True),
        ("2026-10-15 13:40", -36.863, -71.377, True),
        ("2026-10-16 05:10", -36.863, -71.377, False),   # control: una pasada nocturna corriente
    ]
    js = "const C = " + json.dumps(casos) + ";\nprocess.stdout.write(JSON.stringify(C.map(c => D.esDiurna(c[0], c[1], c[2]))));"
    assert _modulo(tmp_path, js) == [c[3] for c in casos]


def test_fecha_ilegible_o_sin_coordenadas_es_noche(tmp_path):
    js = """process.stdout.write(JSON.stringify([D.esDiurna("2026-10-16T12:45", -36.8, -71.3), D.esDiurna("2026-10-16 12:45:00", -36.8, -71.3),
  D.esDiurna(null, -36.8, -71.3), D.esDiurna("2026-10-16 12:45", undefined, -71.3), D.esDiurna("2026-02-30 12:45", -36.8, -71.3),
  D.esDiurna("2026-10-16 12:45", -36.8, -71.3)]));"""
    assert _modulo(tmp_path, js) == [False, False, False, False, False, True]


def test_marcar_y_puntos_diarios(tmp_path):
    js = """
const R = [{ datetime_utc: "2026-10-16 12:45", sensor: "MODIS_TERRA", v: 15.7 },
           { datetime_utc: "2026-10-16 20:10", sensor: "MODIS_AQUA", v: 3.0 },
           { datetime_utc: "2026-10-16 05:10", sensor: "MODIS_AQUA", v: 40.0 },
           { datetime_utc: "2026-10-17 20:50", sensor: "MODIS_AQUA", v: 14.1 }];
const n = D.marcar(R, -36.863, -71.377);
const info = r => ({ clave: "MODIS", color: "#ff8c00", label: "MODIS" });
const p = D.puntosDiarios(R, r => r.v, info);
const sinMarca = D.puntosDiarios(R.map(r => Object.assign({}, r, { _diurna: undefined })), r => r.v, info);
process.stdout.write(JSON.stringify({ n, marcas: R.map(r => r._diurna), p: p.map(x => [x.x, x.y, x.dia, x.propia]), sinMarca: sinMarca.length,
  ds: D.dataset(p).mirovaDia === true }));
"""
    out = _modulo(tmp_path, js)
    assert out["n"] == 3 and out["marcas"] == [True, True, False, True], out
    # el máximo DIURNO de cada día (15,7 y no el 40 nocturno), un punto por día y sensor
    assert out["p"] == [["2026-10-16", 15.7, True, True], ["2026-10-17", 14.1, True, True]], out
    assert out["sinMarca"] == 0 and out["ds"], out


# ── (c) y (h): las tres vistas ──────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pagina", ["index.html", "diario.html", "mosaico.html"])
def test_las_tres_vistas_cargan_el_modulo_y_marcan(pagina):
    src = (FRONT / pagina).read_text(encoding="utf-8")
    assert '<script src="diurno.js"></script>' in src
    assert src.index('<script src="diurno.js">') < src.index("DiurnoTablero.marcar(")
    assert "DiurnoTablero.marcar(" in src


def _coords(texto, patron):
    return {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(patron, texto)}


def test_las_coordenadas_de_las_vistas_son_las_de_volcanoes_yaml():
    y = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    vs = y["volcanoes"] if isinstance(y, dict) else y
    ref = {v["name"]: (v["lat"], v["lon"]) for v in vs}
    pat = r'name:\s*"(\w+)",[^\n]*?lat:\s*(-?[\d.]+),\s*lon:\s*(-?[\d.]+)'
    vistas = {p: _coords((FRONT / p).read_text(encoding="utf-8"), pat) for p in ("index.html", "diario.html", "mosaico.html")}
    assert len(vistas["index.html"]) >= 45 and len(vistas["diario.html"]) == 11 and len(vistas["mosaico.html"]) == 11, \
        {k: len(v) for k, v in vistas.items()}
    for pagina, cs in vistas.items():
        for nombre, (lat, lon) in cs.items():
            assert nombre in ref, (pagina, nombre)
            # 0,02° mueve la elevación solar en menos de 0,1°; Villarrica difiere 0,01° de longitud en index y mosaico
            assert abs(lat - ref[nombre][0]) <= 0.02 and abs(lon - ref[nombre][1]) <= 0.02, (pagina, nombre, lat, lon)


# ── (d): la frescura es nocturna ────────────────────────────────────────────────────────────────────────────────────

def _r(t, dia=None, **k):
    r = {"datetime_utc": t, "sensor": "MODIS_AQUA", "vrp_mw": 0}
    if dia is not None:
        r["_diurna"] = dia
    r.update(k)
    return r


def test_index_la_ultima_pasada_y_la_proxima_son_nocturnas(tmp_path):
    """Racimos nocturnos de 3 pasadas a 2 h durante 12 noches y una pasada de día a las 16 UTC: la diurna no es «última
    pasada» ni parte el hueco. Control: sin la marca, sí."""
    regs = []
    for dia in range(1, 13):
        for h in (4, 6, 8):
            regs.append(_r("2026-10-%02d %02d:00" % (dia, h), False))
        regs.append(_r("2026-10-%02d 16:00" % dia, True))
    cuerpo = """
const DATOS = %s;
const sinMarca = DATOS.map(r => Object.assign({}, r, { _diurna: undefined }));
const k = p => [p.prox, p.medianaH, p.toleranciaH];
process.stdout.write(JSON.stringify({ ultima: lastEventTime(DATOS), ultimaSin: lastEventTime(sinMarca), dia: ultimaPasadaDiurna(DATOS),
  prox: k(proximaPasadaEsperada(DATOS)), proxSoloNoche: k(proximaPasadaEsperada(DATOS.filter(r => !r._diurna))),
  proxSin: k(proximaPasadaEsperada(sinMarca)) }));
""" % json.dumps(regs)
    out = _node(tmp_path, "index.html", ["parseUtcMs", "escenaSinDato", "lastEventTime", "ultimaPasadaDiurna",
                                         "proximaPasadaEsperada"], cuerpo)
    assert out["ultima"] == "2026-10-12 08:00" and out["dia"] == "2026-10-12 16:00", out
    assert out["prox"] == out["proxSoloNoche"], out
    assert out["ultimaSin"] == "2026-10-12 16:00" and out["proxSin"] != out["prox"], out   # control


@pytest.mark.parametrize("pagina", ["diario.html", "mosaico.html"])
def test_diario_y_mosaico_la_frescura_es_nocturna(tmp_path, pagina):
    cuerpo = """
const iso = h => new Date(Date.now() - h * 3600000).toISOString().slice(0, 16).replace("T", " ");
const a = monitoringFreshness([{ datetime_utc: iso(50), _diurna: false }, { datetime_utc: iso(2), _diurna: true }]);
const b = monitoringFreshness([{ datetime_utc: iso(50) }, { datetime_utc: iso(2) }]);
process.stdout.write(JSON.stringify({ a: a.cls, b: b.cls }));
"""
    out = _node(tmp_path, pagina, ["parseUtcMs", "monitoringFreshness"], cuerpo)
    assert out == {"a": "mon-lagging", "b": "mon-fresh"}, out   # b: control sin marca


def test_mosaico_ultima_pasada_y_ultima_detencion_por_turno(tmp_path):
    previo = """
const isSummitDetection = r => true;
const isValidDetection = r => true;
const eqVrpDisplay = r => r.vrp_mw || 0;
"""
    cuerpo = """
const iso = h => new Date(Date.now() - h * 3600000).toISOString().slice(0, 16).replace("T", " ");
const R = [{ datetime_utc: iso(10), vrp_mw: 2, sensor: "MODIS_AQUA", _diurna: false },
           { datetime_utc: iso(3), vrp_mw: 90, sensor: "MODIS_TERRA", _diurna: true }];
const sin = R.map(r => Object.assign({}, r, { _diurna: undefined }));
process.stdout.write(JSON.stringify({ noche: latestVRP(R, 5).max, dia: latestVRP(R, 5, true).max, sin: latestVRP(sin, 5).max,
  ult: lastEventTime(R) === R[0].datetime_utc, ultDia: ultimaPasadaDiurna(R) === R[1].datetime_utc }));
"""
    out = _node(tmp_path, "mosaico.html", ["parseUtcMs", "latestVRP", "lastEventTime", "ultimaPasadaDiurna"], cuerpo, previo)
    assert out == {"noche": 2, "dia": 90, "sin": 90, "ult": True, "ultDia": True}, out


# ── (e): la tarjeta de index ────────────────────────────────────────────────────────────────────────────────────────

def test_index_latest_detection_por_turno(tmp_path):
    previo = """
const isSummitDetection = r => true;
const isValidDetection = r => true;
const isSensorVisible = r => true;
const isThermalArtifact = r => false;
const mirovaEqVrpDisplay = r => r.vrp_mw || 0;
const esAnclaHonesta = s => false;
"""
    cuerpo = """
const iso = h => new Date(Date.now() - h * 3600000).toISOString().slice(0, 16).replace("T", " ");
const R = [{ datetime_utc: iso(10), vrp_mw: 2, sensor: "MODIS_AQUA", _diurna: false },
           { datetime_utc: iso(3), vrp_mw: 90, sensor: "MODIS_TERRA", _diurna: true }];
const sin = R.map(r => Object.assign({}, r, { _diurna: undefined }));
process.stdout.write(JSON.stringify({ noche: latestDetection(R, false, 5).vrp, dia: latestDetection(R, false, 5, true).vrp,
  sin: latestDetection(sin, false, 5).vrp, soloDia: latestDetection([R[1]], false, 5) }));
"""
    out = _node(tmp_path, "index.html", ["parseUtcMs", "latestDetection"], cuerpo, previo)
    assert out == {"noche": 2, "dia": 90, "sin": 90, "soloDia": None}, out


def test_index_las_cifras_y_barras_del_periodo_son_nocturnas():
    """Los llamadores: las barras, las cifras, la VRE y la comparación leen filteredNoche; la tabla, todas las pasadas."""
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    det = _fuente(src, "renderDetail")
    assert "const filteredNoche = filtered.filter(r => r._diurna !== true);" in det
    assert "const allVrp = filteredNoche.map(eqVrp)" in det
    assert "for (const r of filteredNoche) {" in det                       # caja VRE
    assert "const modis = filteredNoche.filter(" in det                    # barras
    assert "const sorted = [...filteredNoche]" in det                      # curva VRE
    assert "const ours = filteredNoche.filter(" in det                     # comparación
    assert det.count("DiurnoTablero.dataset(diaPropios)") == 2             # soles propios en VRP y en comparación
    assert det.count("agregarMarcaDiurna(td, r)") == 2                     # las dos clases de fila de la tabla
    cards = _fuente(src, "buildCards")
    assert "latestDetection(d.records, includeFarDistance, innerKm, true)" in cards


# ── (g): diario ─────────────────────────────────────────────────────────────────────────────────────────────────────

def test_diario_cuenta_lo_diurno_aparte(tmp_path):
    previo = """
const applyS38Filter = x => x;
const enPeriodo = () => true;
const eqVrpDisplay = r => r.vrp_mw || 0;
"""
    cuerpo = """
const json = { records: [{ datetime_utc: "2026-11-10 05:00", vrp_mw: 2, _diurna: false },
                         { datetime_utc: "2026-11-10 14:00", vrp_mw: 30, _diurna: true },
                         { datetime_utc: "2026-11-11 05:00", vrp_mw: 0, _diurna: false }] };
const s = computeStats(json, [], "X");
const sin = computeStats({ records: json.records.map(r => Object.assign({}, r, { _diurna: undefined })) }, [], "X");
process.stdout.write(JSON.stringify({ us: s.n_det_us, dia: s.n_det_dia, max: s.max_us, sinUs: sin.n_det_us, sinMax: sin.max_us,
  falla: computeStats(null, [], "X").n_det_dia }));
"""
    out = _node(tmp_path, "diario.html", ["parseUtcMs", "computeStats"], cuerpo, previo)
    assert out == {"us": 1, "dia": 1, "max": 2, "sinUs": 2, "sinMax": 30, "falla": None}, out


# ── textos ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_la_ayuda_dice_modis_de_dia_y_viirs_de_noche():
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    i = src.index("<li><b>El día.</b>")
    li = src[i:src.index("</li>", i)]
    assert "VIIRS se procesa sólo de noche" in li and "MODIS se procesa también de día" in li, li
    assert "sólo se\n        procesan pasadas nocturnas" not in li.replace("\r\n", "\n")
