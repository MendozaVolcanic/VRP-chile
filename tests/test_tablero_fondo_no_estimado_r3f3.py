# -*- coding: utf-8 -*-
"""Auditoría Codex ronda 3, R3F3-V101 (S199): el tablero avisa cuando la potencia de una pasada suma alertados sin fondo.

POR QUÉ. La potencia de una pasada es la suma, sobre los píxeles alertados, del exceso de radiancia sobre el fondo, que se
estima interpolando los vecinos no alertados. Si un alertado queda junto a un hueco de datos, el halo que se saca
alrededor de los alertados se come los vecinos útiles y su fondo no se puede estimar. En VIIRS la vía sigue al .m de
MIROVA y lo suma con fondo 0: la potencia de ese píxel es su radiancia entera, posiblemente inflada (D36, «Fondo no
estimable»). El record lo cuenta en diag_codigo_mirova.alertados_sin_fondo, pero el tablero no lo leía: el geólogo de
turno veía una potencia que podía estar sobreestimada sin aviso. Los records anteriores a S192 no traen la clave; en ellos
L_bk = 0 con alertados (L_bk suma los fondos que existen, np.nansum) dice que NINGÚN alertado tuvo fondo.

QUÉ FIJA, ejecutando frontend/crater_no_medido.js y funciones reales de las tres vistas con node:
(1) fondoNoEstimado marca la clave > 0 y el caso heredado (sin clave, vía, L_bk = 0 con alertados), y no marca sus
    controles (clave en 0, L_bk > 0, record K, escena no medida, sin diagnóstico, valor imposible).
(2) Textos para el operador, sin guiones largos ni comillas dobles (van en un atributo title).
(3) Record real: Láscar VIIRS_SNPP 2025-08-23 05:24 (3 alertados, L_bk 0, 0,703 MW) marca 3 de 3.
(4) La marca no escribe en el record.
(5) index: marcaFondoNoEstimado en la pasada y null en su control; la evolución lleva la marca al recuadro de la última
    pasada; la tabla (dos ramas), el popup, la tarjeta y el tooltip la usan.
(6) mosaico: el tooltip del día con la pasada marcada lo dice y el control no; la tarjeta la usa.
(7) diario: cuenta las pasadas marcadas del período.
(8) Sobre los datos publicados de hoy, el módulo y experiments/_s199_r3f3_v101/medir_sin_fondo.py marcan los mismos
    records (igualdad record por record).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código de antes? Las funciones nuevas no existían: cada prueba cae
con el módulo y las vistas de origin/main; cada caso trae su control. (2) ¿Y si la carga muriera? `_node` exige returncode
0, cada función se extrae del texto real de la vista y (8) exige que haya marcados en los datos (si no, la igualdad
sería vacía).
"""
import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"
MODULO = FRONT / "crater_no_medido.js"
SCRIPT = RAIZ / "experiments" / "_s199_r3f3_v101" / "medir_sin_fondo.py"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="las vistas se prueban con node")


def _fuente(src, nombre):
    m = re.search(r"\nfunction " + re.escape(nombre) + r"\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index("{", src.index(")", m.end()))
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
                       timeout=300)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


D0 = {"motivo_vacio": None, "crater_sin_posicion": False, "px_mir_invalido_crater": 0, "px_saturados_crater": 0,
      "px_bowtie_crater": 0, "px_mir_hueco_crater": 0, "px_tir_hueco_crater": 0, "L_hot": 1.2, "L_bk": 0.9,
      "alertados_sin_fondo": 0}


def _rec(dt="2026-11-22 05:06", y=0.0, npix=5, **diag):
    return {"sensor": "VIIRS_NOAA20", "datetime_utc": dt, "via_codigo_mirova": True, "vrp_mw": y, "_y": y,
            "n_anomalous_pixels": npix, "anomaly_pixels": [], "t_bg_k": 250.0, "diag_codigo_mirova": dict(D0, **diag)}


def _heredado(l_bk, npix=3, via=True):
    r = _rec(npix=npix, L_bk=l_bk)
    del r["diag_codigo_mirova"]["alertados_sin_fondo"]
    r["via_codigo_mirova"] = via
    return r


# Diagnóstico real de data/mirova_equivalent/Lascar.json (origin/main 58c8e93da, 2026-11-24), copiado para no depender del NRT.
LASCAR_SIN_FONDO = {"sensor": "VIIRS_SNPP", "datetime_utc": "2025-08-23 05:24", "via_codigo_mirova": True, "vrp_mw": 0.703,
                    "distance_class": "summit", "t_bg_k": 0.0, "n_anomalous_pixels": 3,
                    "diag_codigo_mirova": {"motivo_vacio": None, "n_abs": 0, "n_p1": 2, "n_p2": 1,
                                           "L_hot": 0.27773925789810827, "L_bk": 0.0, "roi": "def"}}


def test_marca_y_sus_controles():
    casos = [
        _rec(alertados_sin_fondo=2),                               # 0: 2 de 5 sin fondo
        _rec(),                                                    # 1: control, la clave en 0
        _rec(npix=0, alertados_sin_fondo=None),                    # 2: sin alertados
        _rec(npix=0, alertados_sin_fondo=1, motivo_vacio="fondo_no_estimado"),   # 3: MODIS no medida: ya se rotula aparte
        _heredado(0.0),                                            # 4: anterior a S192, L_bk 0 con alertados: todos
        _heredado(0.12),                                           # 5: control heredado con fondo
        _heredado(0.0, via=False),                                 # 6: no es de la vía
        _heredado(0.0, npix=0),                                    # 7: sin alertados
        {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-22 05:06", "n_anomalous_pixels": 3},   # 8: sin diagnóstico
        _rec(alertados_sin_fondo=-1),                              # 9: valor imposible
        dict(_rec(alertados_sin_fondo=3), n_anomalous_pixels=None),   # 10: sin el total
    ]
    o = _node("process.stdout.write(JSON.stringify(DATOS.map(r => C.fondoNoEstimado(r))));", casos)
    assert o[0] == {"n": 2, "total": 5, "inferido": False}
    assert o[1] is None and o[2] is None and o[3] is None
    assert o[4] == {"n": 3, "total": 3, "inferido": True}
    assert o[5] is None and o[6] is None and o[7] is None and o[8] is None and o[9] is None
    assert o[10] == {"n": 3, "total": None, "inferido": False}


def test_textos_para_el_operador():
    o = _node("""
const t = (f) => [C.textoFondo(f), C.tituloFondo(f)];
process.stdout.write(JSON.stringify([t({n: 2, total: 5, inferido: false}), t({n: 1, total: 1, inferido: false}),
  t({n: 3, total: 3, inferido: true}), t({n: 3, total: null, inferido: false}), t(null)]));""")
    assert o[0][0] == "fondo no estimado en 2 de 5 alertados: la potencia puede estar sobreestimada"
    assert o[1][0] == "fondo no estimado en 1 de 1 alertado: la potencia puede estar sobreestimada"
    assert o[2][0] == "fondo no estimado en 3 de 3 alertados: la potencia puede estar sobreestimada"
    assert o[3][0] == "fondo no estimado en 3 alertados: la potencia puede estar sobreestimada"
    assert o[4] == ["", ""]
    assert "radiancia entera" in o[0][1] and "sólo avisa" in o[0][1]
    assert "L_bk" not in o[0][1] and "anterior" in o[2][1] and "anterior" not in o[0][1]
    for par in o:
        for s in par:
            assert chr(0x2014) not in s and chr(0x2013) not in s   # sin guiones largos ni medios
            assert '"' not in s                                     # va dentro de un atributo title del popup


def test_record_real_y_no_escribe():
    o = _node("""
const congelar = (x) => { if (x && typeof x === 'object') { Object.values(x).forEach(congelar); Object.freeze(x); } return x; };
const r = congelar(DATOS);
const antes = JSON.stringify(r);
const f = C.fondoNoEstimado(r);
C.textoFondo(f); C.tituloFondo(f);
process.stdout.write(JSON.stringify([f, antes === JSON.stringify(r)]));""", LASCAR_SIN_FONDO)
    assert o == [{"n": 3, "total": 3, "inferido": True}, True]


def _previo_index():
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    stubs = ("function el(tag, cls) { return {tag, className: cls || '', textContent: '', title: ''}; }\n"
             "function isThermalArtifact() { return false; }\n"
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
    return stubs + "\n".join([_const(src, "EVOL_MISMA_PASADA_MS"), _const(src, "EVOL_PRIORIDAD_ESTADO")]) + "\n" + "\n".join(
        _fuente(src, f) for f in ("todasPasadasEvol", "vrpPublicadoEvol", "ultimaPasadaEvol", "textoUltimaPasadaEvol",
                                  "marcaFondoNoEstimado")) + "\n"


def test_index_marca_y_evolucion():
    o = _node("""
const [a, b] = [DATOS.marcado, DATOS.limpio].map(r => marcaFondoNoEstimado('marca-crater-no-medido', r));
const rec = (rs) => { const p = todasPasadasEvol(rs, 5); return {fne: p.map(x => x.fne || null),
  recuadro: textoUltimaPasadaEvol(ultimaPasadaEvol(p, false), Date.now(), false, null).texto}; };
process.stdout.write(JSON.stringify({a: a && [a.textContent, a.className, a.title.length > 0], b,
  ev: rec([DATOS.marcado]), evControl: rec([DATOS.limpio])}));""",
              {"marcado": _rec(y=4.0, alertados_sin_fondo=2), "limpio": _rec(y=4.0)}, previo=_previo_index())
    assert o["a"] == ["⊘ fondo no estimado en 2 de 5 alertados: la potencia puede estar sobreestimada",
                      "marca-crater-no-medido", True]
    assert o["b"] is None
    assert o["ev"]["fne"] == [{"n": 2, "total": 5, "inferido": False}]
    assert "Bajo, 4.00 MW · ⊘ fondo no estimado en 2 de 5 alertados" in o["ev"]["recuadro"]
    assert o["evControl"]["fne"] == [None] and "⊘" not in o["evControl"]["recuadro"]


def test_index_usa_la_marca_en_todos_los_lugares():
    idx = (FRONT / "index.html").read_text(encoding="utf-8")
    assert idx.count('marcaFondoNoEstimado("marca-crater-no-medido", r)') == 2   # las dos ramas de la tabla de pasadas
    assert "popupCrater + popupFondo" in idx and "CraterNoMedido.fondoNoEstimado(r)" in idx
    assert 'marcaFondoNoEstimado("vc-crater-no-medido", det.rec)' in idx          # tarjeta: la detección que muestra
    assert "CraterNoMedido.textoFondo(p.fne)" in idx                               # tooltip de la evolución


def _previo_mosaico():
    src = (FRONT / "mosaico.html").read_text(encoding="utf-8")
    return ("const Periodo = {intervalo: () => [Date.parse(DATOS.t0), Date.parse(DATOS.t1)]};\nconst PERIODO = null;\n"
            "function eqVrpDisplay(r) { return r._y || 0; }\nfunction fmtVRP(v) { return String(v); }\n"
            + _fuente(src, "buildSparklineData") + "\n" + _fuente(src, "etiquetaDiaSparkline") + "\n")


def test_mosaico():
    o = _node("""
const s = buildSparklineData(DATOS.recs, 5);
const i = (d) => s.labels.findIndex(x => x.toISOString().slice(0, 10) === d);
const et = (d) => etiquetaDiaSparkline(s.values[i(d)], s.observado[i(d)], s.noMedido[i(d)], s.sat[i(d)], s.sinFondo[i(d)]);
process.stdout.write(JSON.stringify([et('2026-11-20'), et('2026-11-21')]));""",
              {"t0": "2026-11-20T00:00:00Z", "t1": "2026-11-21T12:00:00Z",
               "recs": [_rec(dt="2026-11-20 05:00", y=3.5, alertados_sin_fondo=1), _rec(dt="2026-11-21 05:00", y=3.5)]},
              previo=_previo_mosaico())
    assert o[0] == "VRP: 3.5 MW · ⊘ fondo no estimado en una pasada: la potencia puede estar sobreestimada"
    assert o[1] == "VRP: 3.5 MW"
    mos = (FRONT / "mosaico.html").read_text(encoding="utf-8")
    assert "CraterNoMedido.fondoNoEstimado(latestRec)" in mos and "CraterNoMedido.textoFondo(" in mos


def test_diario():
    dia = (FRONT / "diario.html").read_text(encoding="utf-8")
    assert re.search(r"fondo_no_estimado: jsonData && typeof CraterNoMedido !== \"undefined\"\s*\? recs\.filter\(r => "
                     r"r\._diurna !== true && CraterNoMedido\.fondoNoEstimado\(r\)\)\.length : null", dia)
    assert "stats.fondo_no_estimado" in dia


def _script():
    spec = importlib.util.spec_from_file_location("medir_sin_fondo", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_igual_al_script_sobre_los_datos_publicados():
    mod = _script()
    rutas = [str(p) for p, _ in mod.fuentes(RAIZ)]
    esperado = []
    for ruta in rutas:
        for i, r in enumerate(json.loads(Path(ruta).read_text(encoding="utf-8")).get("records", [])):
            n = mod.criterio(r)
            if n:
                esperado.append([ruta, i, n])
    o = _node("""
const fs = require('fs'); const out = [];
for (const ruta of DATOS) (JSON.parse(fs.readFileSync(ruta, 'utf8')).records || []).forEach((r, i) => {
  const f = C.fondoNoEstimado(r); if (f) out.push([ruta, i, f.n]); });
process.stdout.write(JSON.stringify(out));""", rutas)
    assert esperado, "sin records marcados en los datos: la igualdad sería vacía"
    assert o == esperado
