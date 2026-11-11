"""S180: la magnitud «Núcleo F5'» del tablero no recorta los records de la vía «código MIROVA».

POR QUÉ. El Núcleo F5' (S95 a S97, `docs/F5_CALIBRATION_S95.md`) se armó para el detector K de VIIRS 375: K
sumaba un halo de píxeles apenas tibios sobre la nieve y la magnitud salía muchas veces sobre MIROVA
(Villarrica 19 veces, Tupungatito 11). El núcleo se queda con el píxel de más energía, los que están a
0,75 km de él y los que pasan de 295 K. La vía «código MIROVA» (VIIRS 375 desde #974, 2026-11-11) es el
detector de MIROVA y suma todos los píxeles alertados, igual que MIROVA: recortarla deshace justo lo que la
vía corrige. Hasta S180 no la recortaba sólo por casualidad: los píxeles de la vía no traen `vrp_mw`, el
recálculo daba 0 y el guard S96 («el núcleo nunca borra una detección») devolvía el cúmulo (Chillán
2026-11-11 06:54 UTC, NOAA-20: 26 píxeles, 31,889 MW, núcleo 0). Si el pipeline empezara a escribir la VRP
por píxel o `f5_core_vrp_mw` en la vía, el tablero habría pasado a recortarla sin aviso. Decisión de
Nicolás, 2026-11-11: «Sí, exímela».

QUÉ VIGILA. En las tres vistas vivas (index, mosaico, diario), con las funciones extraídas del HTML y
ejecutadas en node con `frontend/cambio_detector.js` cargado (quien lee la marca, A102):
1. un record de la vía con VRP por píxel y con `f5_core_vrp_mw` escritos muestra el cúmulo completo;
2. el MISMO record sin la marca (K) sigue mostrando el núcleo: el núcleo no se apagó para K;
3. un record de K con el aviso de la vía (`via_codigo_mirova: "sin_grilla"`, A118) tampoco se exenta;
4. `f5CoreMagnitude` devuelve null para la vía, porque la tabla de últimas detecciones de index la llama
   directo, sin pasar por `mirovaEqVrpCore`.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Sin la exención, el caso 1 da el núcleo (15 MW), no el cúmulo: lo
muestran los controles 2 y 3, que son el mismo record y tienen que dar el núcleo. (2) Si la extracción se
rompe, node lanza error y la prueba cae con mensaje.
"""
import json
import os
import shutil
import subprocess
import tempfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VISTAS = ["index.html", "mosaico.html", "diario.html"]

_JS = r"""
const fs = require('fs');
const path = require('path');
const vista = process.argv[2];
const src = fs.readFileSync(process.argv[3], 'utf8');
function extraer(nombre) {
  const i = src.search(new RegExp('function\\s+' + nombre + '\\s*\\('));
  if (i < 0) throw new Error('no encontre function ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerro ' + nombre);
}
function constante(nombre) {
  const m = src.match(new RegExp('const ' + nombre + '\\s*=\\s*([^;]+);'));
  if (!m) throw new Error('no encontre const ' + nombre);
  return m[0];
}
const CambioDetector = require(path.join(path.dirname(process.argv[3]), 'cambio_detector.js'));
let includeFarDistance = false;
const consts = ['F5_R_CORE_KM', 'F5_BT_EXT_K'].concat(vista === 'diario.html' ? ['INNER_RADIUS_KM'] : []);
eval(consts.map(constante).join('\n') + '\n'
     + ['_havKm', 'mirovaEqVrp', 'f5CoreMagnitude', 'mirovaEqVrpCore'].map(extraer).join('\n'));
const casos = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const arg = vista === 'diario.html' ? 'NevadosDeChillan' : 5;
console.log(JSON.stringify(casos.map(r => [mirovaEqVrpCore(r, arg), f5CoreMagnitude(r, 5)])));
"""


def _correr(vista, casos):
    tmp = tempfile.mkdtemp()
    try:
        runner, datos = os.path.join(tmp, "r.js"), os.path.join(tmp, "c.json")
        with open(runner, "w", encoding="utf-8") as fp:
            fp.write(_JS)
        with open(datos, "w", encoding="utf-8") as fp:
            json.dump(casos, fp)
        out = subprocess.run(["node", runner, vista, os.path.join(ROOT, "frontend", vista), datos],
                             capture_output=True, text=True, timeout=120)
        assert out.returncode == 0, f"node fallo en {vista}: {out.stderr[-800:]}"
        return json.loads(out.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Forma del caso Chillán 2026-11-11 06:54 UTC (NOAA-20, cúmulo de 31,889 MW junto al cráter), con VRP por
# píxel inventada para que el núcleo difiera del cúmulo: pico de 10 MW en el centroide, un vecino de 5 MW a
# 0,3 km (dentro del núcleo) y un píxel tibio de 6,889 MW a unos 2 km y 280 K (fuera, y con menos energía
# que el pico para que el ancla sea el centroide). Núcleo = 15 MW; el cúmulo queda en 31,889 MW.
LAT, LON = -36.8585, -71.3797
CHILLAN = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-11 06:54", "distance_class": "summit",
           "vrp_mw": 31.889,
           "primary_cluster": {"vrp_mw": 31.889, "centroid_lat": LAT, "centroid_lon": LON,
                               "centroid_dist_km": 0.56, "n_pixels": 3},
           "anomaly_pixels": [{"lat": LAT, "lon": LON, "bt_k": 330.0, "vrp_mw": 10.0},
                              {"lat": LAT + 0.0027, "lon": LON, "bt_k": 300.0, "vrp_mw": 5.0},
                              {"lat": LAT + 0.018, "lon": LON, "bt_k": 280.0, "vrp_mw": 6.889}]}


def _con(base, **kw):
    r = json.loads(json.dumps(base))
    r.update(kw)
    return r


node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


@node
@pytest.mark.parametrize("vista", VISTAS)
def test_el_nucleo_no_recorta_la_via_y_si_a_k(vista):
    casos = [_con(CHILLAN, via_codigo_mirova=True),                          # 0: vía, VRP por píxel
             _con(CHILLAN, via_codigo_mirova=True, f5_core_vrp_mw=15.0),     # 1: vía con el campo del pipeline
             _con(CHILLAN),                                                  # 2: el mismo record de K
             _con(CHILLAN, f5_core_vrp_mw=15.0),                             # 3: K con el campo del pipeline
             _con(CHILLAN, via_codigo_mirova="sin_grilla")]                  # 4: K con aviso de la vía (A118)
    res = _correr(vista, casos)
    for i in (2, 3, 4):
        assert res[i][0] == pytest.approx(15.0), f"{vista}: control {i} roto, K tendría que dar el núcleo: {res[i]}"
    for i in (0, 1):
        assert res[i][0] == pytest.approx(31.889), f"{vista}: el núcleo recorta la vía (caso {i}): {res[i]}"
        assert res[i][1] is None, f"{vista}: f5CoreMagnitude no devuelve null para la vía (caso {i}): {res[i]}"
