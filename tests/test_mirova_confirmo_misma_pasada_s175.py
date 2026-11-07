"""S175 decision 7 (F2-204, V2-04): la marca «MIROVA confirmo» del tablero mira la MISMA pasada y aplica D-9.

POR QUE. La columna MIROVA de la tabla dice «MIROVA publico alerta termica en esta pasada», el popup dice
«Confirmado por MIROVA» y el anillo verde del mapa lo repite. Hasta S175 la funcion aceptaba cualquier alerta
del mismo sensor a ±60 min (otra pasada de la noche, otro satelite) y alertas de 0,04 MW que el banner de MIROVA
llama NONE (D-9, #811). Medido en experiments/_s175_confirmo_pasada/medir_salida.txt: 856 de 2.738 publicaciones
marcadas perdian la marca con la vara del banco (756 VIIRS 375, 100 VIIRS 750, 0 MODIS). Nicolas aprobo alinear
la logica al texto el 2026-11-07.

QUE VIGILA, con la funcion real extraida de frontend/index.html y ejecutada en node (A97):
1. otra pasada de la misma noche (40 min) no confirma; la misma pasada (1 y 2 min) si; 3 min no;
2. D-9 en VIIRS 375: 0,04 y 0,05 MW solas no confirman; 0,04 con una alerta mayor a ±120 s si;
3. D-9 solo en VIIRS 375: 0,04 MW en MODIS y VIIRS 750 confirma;
4. RUTINA de la misma pasada no confirma;
5. las constantes del JS son las de scripts/clase_mirova.py (VENTANA_S, UMBRAL_MINIMA_MW, SENSORES_MINIMA);
6. diario.html y mosaico.html no llenan la marca (S92: si algun dia la llenan, que sea con esta funcion).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si la regla vieja volviera, lo veria: el control corre la MISMA funcion
con la ventana en 60 min y sin D-9 y exige que los casos 1 (40 min) y 2 (0,04 MW) den confirmado. (2) Si la
extraccion se rompiera, node cae con error y el test falla con mensaje.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import clase_mirova  # noqa: E402

HTML = os.path.join(ROOT, "frontend", "index.html")

_JS = r"""
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
const regla = process.argv[4];
const ajuste = regla === 'vieja' ? 'MIROVA_PASADA_MS = 3600000; MIROVA_MINIMA_BUCKETS = [];' : '';
eval(consts.replace(/^const /gm, 'var ') + '\n' + ajuste + '\n' + ['parseUtcMs', 'sensorGroup', 'ourSensorBucket',
  'mirovaSensorBucket', 'enrichWithMirovaConfirmation'].map(extraer).join('\n'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(([rec, mir]) => {
  const r = Object.assign({}, rec); enrichWithMirovaConfirmation([r], mir); return r._mirova_confirmed ? 1 : 0; })));
"""


def _alerta(hhmm, vrp, sensor="VIIRS375", cls="Bajo"):
    return {"datetime_utc": "2026-10-20 " + hhmm, "sensor": sensor, "VRP_MW": vrp, "distancia_km": 1.0,
            "clasificacion": cls, "source": "consolidado"}


REC_V375 = {"datetime_utc": "2026-10-20 05:00", "sensor": "VIIRS_SNPP"}
CASOS = {
    "otra_pasada_40min": ([REC_V375, [_alerta("05:40", 1.2)]], 0),
    "misma_pasada_1min": ([REC_V375, [_alerta("05:01", 1.2)]], 1),
    "borde_2min": ([REC_V375, [_alerta("05:02", 1.2)]], 1),
    "fuera_3min": ([REC_V375, [_alerta("05:03", 1.2)]], 0),
    "d9_004": ([REC_V375, [_alerta("05:00", 0.04)]], 0),
    "d9_005_exacto": ([REC_V375, [_alerta("05:00", 0.05)]], 0),
    "d9_minima_con_mayor_cerca": ([REC_V375, [_alerta("05:00", 0.04), _alerta("05:01", 0.8)]], 1),
    "d9_no_aplica_modis": ([{"datetime_utc": "2026-10-20 05:00", "sensor": "MODIS_AQUA"},
                            [_alerta("05:00", 0.04, sensor="MODIS")]], 1),
    "d9_no_aplica_v750": ([{"datetime_utc": "2026-10-20 05:00", "sensor": "VIIRS_SNPP_750"},
                           [_alerta("05:00", 0.04, sensor="VIIRS")]], 1),
    "rutina_misma_pasada": ([REC_V375, [_alerta("05:00", 0.0, cls="RUTINA")]], 0),
    "otro_sensor": ([REC_V375, [_alerta("05:00", 2.0, sensor="MODIS")]], 0),
}


def _correr(regla):
    tmp = tempfile.mkdtemp()
    try:
        runner, datos = os.path.join(tmp, "r.js"), os.path.join(tmp, "c.json")
        with open(runner, "w", encoding="utf-8") as fp:
            fp.write(_JS)
        with open(datos, "w", encoding="utf-8") as fp:
            json.dump([c for c, _ in CASOS.values()], fp)
        out = subprocess.run(["node", runner, HTML, datos, regla], capture_output=True, text=True, timeout=120)
        assert out.returncode == 0, f"node fallo: {out.stderr[-800:]}"
        return dict(zip(CASOS, json.loads(out.stdout)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_marca_misma_pasada_con_d9():
    got = _correr("nueva")
    esperado = {k: e for k, (_, e) in CASOS.items()}
    assert got == esperado


def test_control_regla_vieja_confirmaba_lo_que_hoy_no():
    got = _correr("vieja")
    assert got["otra_pasada_40min"] == 1 and got["d9_004"] == 1 and got["d9_005_exacto"] == 1


def test_constantes_iguales_a_clase_mirova():
    src = open(HTML, encoding="utf-8").read()
    pasada = re.search(r"^const MIROVA_PASADA_MS\s*=\s*(\d+)\s*\*\s*1000;", src, re.M)
    minima = re.search(r"^const MIROVA_MINIMA_MW\s*=\s*([\d.]+);", src, re.M)
    buckets = re.search(r"^const MIROVA_MINIMA_BUCKETS\s*=\s*\[([^\]]*)\];", src, re.M)
    assert pasada and minima and buckets
    assert int(pasada.group(1)) == clase_mirova.VENTANA_S
    assert float(minima.group(1)) == clase_mirova.UMBRAL_MINIMA_MW
    assert tuple(re.findall(r'"(\w+)"', buckets.group(1))) == tuple(clase_mirova.SENSORES_MINIMA)


def test_diario_y_mosaico_no_llenan_la_marca():
    for vista in ("diario.html", "mosaico.html"):
        src = open(os.path.join(ROOT, "frontend", vista), encoding="utf-8").read()
        assert not re.search(r"_mirova_confirmed\s*=[^=]", src), vista
