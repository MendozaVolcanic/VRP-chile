"""Frente 7 de la auditoria Codex, ronda 2 (hoja de respuestas): tres defectos confirmados del tablero.

POR QUE.
- F7-301 y F7-V401. El panel «Metricas vs MIROVA» llamaba falso positivo a toda deteccion nuestra sin alerta de
  MIROVA a ±60 min. Pero el JSON de MIROVA del tablero solo traia alertas, asi que el panel no podia distinguir
  tres cosas distintas: MIROVA miro esa pasada y no vio nada (fila RUTINA de la tabla: eso SI es un FP nuestro),
  MIROVA vio calor fuera de su radio (fila FALSO_POSITIVO: el banco la separa como far_ref) y MIROVA no tiene
  ninguna fila de esa pasada (no la proceso o el scraper no la trajo: sin dato, no FP). Medido con el predicado
  del tablero (11 Tier A, 2026-03-01 a 2026-11-16): ver la descripcion del PR.
- F7-304. El generador guardaba la distancia de una alerta OCR anterior al 2026-06-13 como 0 (el OCR de ese tramo
  no media la distancia y escribia 0 fijo, hito de scripts/calidad_referencia_mirova.py) y el tooltip decia
  «MIROVA @ 0.00 km», que se lee como «en el crater». La ausencia tiene que llegar al tooltip como «sin distancia».
- F7-308. El aviso del banco decia que antes del 2026-06-13 decide «SOLO la tabla», pero el banco toma las
  alertas de la tabla y del OCR sin mirar la fecha (scripts/banco_paridad.py, etiquetar). Se corrige el TEXTO;
  la precedencia la decide Nicolas.

Las funciones del tablero se extraen de frontend/index.html y se ejecutan en node (A97). En computeMetrics se
sustituye el predicado de magnitud (mirovaEqVrpDisplay) por `vrp_mw`: aca se prueba el conteo, no el predicado.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si el defecto volviera, lo veria: cada caso tiene su control que exige el
comportamiento contrario en la situacion vecina (RUTINA da FP, sin fila no; OCR despues del 2026-06-13 con 0 sigue
en 0). (2) Si la extraccion se rompiera, node cae y el test falla con mensaje.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import calidad_referencia_mirova as cal  # noqa: E402
import rebuild_mirova_from_consolidado as rb  # noqa: E402

HTML = os.path.join(ROOT, "frontend", "index.html")
NODE = shutil.which("node")

_EXTRAER = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function extraer(nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) throw new Error('no encontre function ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerro ' + nombre);
}
const consts = (src.match(/^const MIROVA_\w+\s*=[^;]+;/gm) || []).join('\n');
"""

_JS_METRICAS = _EXTRAER + r"""
function isThermalArtifact() { return false; }
function mirovaEqVrpDisplay(r) { return r.vrp_mw || 0; }
eval(consts.replace(/^const /gm, 'var ') + '\n' + ['parseUtcMs', 'sensorGroup', 'ourSensorBucket',
  'mirovaSensorBucket', 'computeMetrics'].map(extraer).join('\n'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(([ours, mir, pasadas]) => {
  const b = computeMetrics(ours, mir, 5, false, pasadas).byBucket.VIIRS375;
  return { fp: b.fp, sin_ref: b.sin_ref || 0, fuera_radio: b.fuera_radio || 0, tp: b.tp };
})));
"""

_JS_DIST = _EXTRAER + r"""
eval(consts.replace(/^const /gm, 'var ') + '\n' + ['parseUtcMs', 'sensorGroup', 'ourSensorBucket',
  'mirovaSensorBucket', 'enrichWithMirovaConfirmation', 'textoDistanciaMirova'].map(extraer).join('\n'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(([rec, mir]) => {
  const r = Object.assign({}, rec); enrichWithMirovaConfirmation([r], mir);
  return [r._mirova_confirmed, r._mirova_dist_km, textoDistanciaMirova(r, 2)];
})));
"""


def _node(js, casos):
    if NODE is None:
        pytest.skip("node no esta instalado")
    with tempfile.TemporaryDirectory() as tmp:
        p_js, p_c = os.path.join(tmp, "x.js"), os.path.join(tmp, "c.json")
        Path(p_js).write_text(js, encoding="utf-8")
        Path(p_c).write_text(json.dumps(casos), encoding="utf-8")
        out = subprocess.run([NODE, p_js, HTML, p_c], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


# --------------------------------------------------------------------------------------------- F7-301 y F7-V401
OURS = [{"datetime_utc": "2026-10-20 05:00", "sensor": "VIIRS_SNPP", "vrp_mw": 2.0}]
PAS_RUTINA = {"rutina": {"VIIRS375": ["2026-10-20 05:01"]}, "fuera_radio": {}}
PAS_LEJOS = {"rutina": {}, "fuera_radio": {"VIIRS375": ["2026-10-20 05:00"]}}
PAS_OTRA = {"rutina": {"VIIRS375": ["2026-10-20 05:03"]}, "fuera_radio": {}}
PAS_OTRO_SENSOR = {"rutina": {"VIIRS": ["2026-10-20 05:00"]}, "fuera_radio": {}}
PAS_VACIAS = {"rutina": {}, "fuera_radio": {}}


def test_f7_301_metricas_separan_sin_dato_y_fuera_de_radio():
    casos = [
        [OURS, [], PAS_VACIAS],         # MIROVA no tiene fila de esta pasada: sin dato, no FP
        [OURS, [], PAS_RUTINA],         # control: MIROVA miro (RUTINA a 1 min) y no vio nada: FP
        [OURS, [], PAS_LEJOS],          # F7-V401: calor fuera del radio de MIROVA: aparte, no FP
        [OURS, [], PAS_OTRA],           # RUTINA a 3 min es otra pasada: sin dato
        [OURS, [], PAS_OTRO_SENSOR],    # RUTINA de VIIRS 750 no cuenta para VIIRS 375: sin dato
    ]
    got = _node(_JS_METRICAS, casos)
    assert got[0] == {"fp": 0, "sin_ref": 1, "fuera_radio": 0, "tp": 0}, got[0]
    assert got[1] == {"fp": 1, "sin_ref": 0, "fuera_radio": 0, "tp": 0}, got[1]
    assert got[2] == {"fp": 0, "sin_ref": 0, "fuera_radio": 1, "tp": 0}, got[2]
    assert got[3] == {"fp": 0, "sin_ref": 1, "fuera_radio": 0, "tp": 0}, got[3]
    assert got[4] == {"fp": 0, "sin_ref": 1, "fuera_radio": 0, "tp": 0}, got[4]


def test_f7_301_json_viejo_sin_pasadas_conserva_el_conteo_anterior():
    # Mientras el sync no regenera el JSON de MIROVA (sin `pasadas_tabla`), el panel no inventa «sin dato».
    got = _node(_JS_METRICAS, [[OURS, [], None]])
    assert got[0] == {"fp": 1, "sin_ref": 0, "fuera_radio": 0, "tp": 0}, got[0]


def _escribir_csv(path, filas, campos):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in filas:
            w.writerow({k: r.get(k, "") for k in campos})


CAMPOS_CONS = ["timestamp", "Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro",
               "Clasificacion Mirova"]
CAMPOS_OCR = CAMPOS_CONS + ["Metodo_Validacion"]


def _fila(fecha, sensor, vrp, dist, tipo, clase):
    return {"Fecha_Satelite_UTC": fecha, "Volcan": "Lascar", "Sensor": sensor, "VRP_MW": vrp,
            "Distancia_km": dist, "Tipo_Registro": tipo, "Clasificacion Mirova": clase}


def _rebuild(tmp_path, monkeypatch, cons, ocr=()):
    monkeypatch.setattr(rb, "REPO", tmp_path)
    p_cons, p_ocr = tmp_path / "cons.csv", tmp_path / "ocr.csv"
    _escribir_csv(p_cons, cons, CAMPOS_CONS)
    _escribir_csv(p_ocr, list(ocr), CAMPOS_OCR)
    rb.rebuild("Lascar", "Lascar", source=p_cons, ocr=p_ocr)
    return json.loads((tmp_path / "data" / "mirova" / "Lascar.json").read_text(encoding="utf-8"))


def test_f7_301_generador_publica_las_pasadas_sin_alerta_de_la_tabla(tmp_path, monkeypatch):
    d = _rebuild(tmp_path, monkeypatch, [
        _fila("2026-10-20 05:00:30", "VIIRS375", "0.0", "0.0", "RUTINA", "NULO"),
        _fila("2026-10-20 05:06:00", "VIIRS", "0.0", "0.0", "RUTINA", "NULO"),
        _fila("2026-10-21 05:00:00", "VIIRS375", "0.0", "12.3", "FALSO_POSITIVO", "NULO"),
        _fila("2026-10-22 05:00:00", "VIIRS375", "1.5", "1.1", "ALERTA_TERMICA", "Bajo"),
        # RUTINA con VRP > 0 (tipos de enero): no es «miro y no vio nada», igual que en el banco
        _fila("2026-01-12 05:00:00", "MODIS", "1.0", "0.0", "RUTINA", "NULO"),
    ])
    pt = d["pasadas_tabla"]
    assert pt["rutina"] == {"VIIRS375": ["2026-10-20 05:00"], "VIIRS": ["2026-10-20 05:06"]}
    assert pt["fuera_radio"] == {"VIIRS375": ["2026-10-21 05:00"]}
    assert [r["datetime_utc"] for r in d["records"]] == ["2026-10-22 05:00"]   # las alertas no cambian


# --------------------------------------------------------------------------------------------------- F7-304
def test_f7_304_distancia_ocr_no_medida_queda_ausente(tmp_path, monkeypatch):
    d = _rebuild(tmp_path, monkeypatch, [
        _fila("2026-05-02 05:00:00", "VIIRS375", "0.9", "0.0", "ALERTA_TERMICA", "Muy Bajo"),  # tabla: 0 medido
        _fila("2026-05-03 05:00:00", "VIIRS375", "0.9", "", "ALERTA_TERMICA", "Muy Bajo"),     # tabla vacia
    ], ocr=[
        _fila("2026-05-01 05:00:00", "VIIRS375", "1.2", "0.0", "ALERTA_TERMICA_OCR", "Bajo"),  # OCR sin medir
        _fila("2026-09-12 05:36:01", "VIIRS375", "0.07", "0.0", "ALERTA_TERMICA_OCR", "Muy Bajo"),  # medido 0
    ])
    dist = {r["datetime_utc"][:10]: r["distancia_km"] for r in d["records"]}
    assert dist["2026-05-01"] is None, "OCR anterior al 2026-06-13: el 0 no es medicion"
    assert dist["2026-09-12"] == 0.0, "control: OCR posterior con 0,00 km medido (estrella en el crater)"
    assert dist["2026-05-02"] == 0.0, "control: la tabla con 0 es medicion"
    assert dist["2026-05-03"] is None, "celda vacia: ausente, nunca 0"


def _alerta(dist):
    return {"datetime_utc": "2026-05-01 05:00", "sensor": "VIIRS375", "VRP_MW": 1.2, "distancia_km": dist,
            "clasificacion": "Bajo", "source": "ocr"}


def test_f7_304_tooltip_dice_sin_distancia():
    rec = {"datetime_utc": "2026-05-01 05:00", "sensor": "VIIRS_SNPP"}
    got = _node(_JS_DIST, [[rec, [_alerta(None)]], [rec, [_alerta(0.0)]], [rec, [_alerta(3.456)]], [rec, []]])
    assert got[0] == [True, None, "sin distancia"]
    assert got[1] == [True, 0, "0.00 km"]          # control: un 0 medido se muestra como 0
    assert got[2] == [True, 3.456, "3.46 km"]
    assert got[3] == [False, None, None]           # sin confirmacion no hay texto de distancia


def test_f7_304_las_dos_vistas_de_index_usan_el_texto_comun():
    src = Path(HTML).read_text(encoding="utf-8")
    assert "MIROVA @ ${r._mirova_dist_km.toFixed(2)}" not in src
    assert "_mirova_dist_km.toFixed(1)" not in src
    assert src.count("textoDistanciaMirova(") >= 3   # definicion, tooltip del grafico y tabla de pasadas


# --------------------------------------------------------------------------------------------------- F7-308
def test_f7_308_aviso_dice_que_el_ocr_tambien_decide_antes_de_junio():
    txt = cal.etiqueta_que_decide("2026-03-01")
    assert "SOLO la tabla" not in txt
    assert txt.startswith("tabla y OCR")
    assert "2026-06-13" in txt and "distancia" in txt
    assert cal.etiqueta_que_decide("2026-09-01") == "tabla y OCR"   # control: el tramo sano no cambia
