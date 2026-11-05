"""S173 S1: los filtros de artefacto termico del tablero no ocultan records de la via «codigo MIROVA».

POR QUE. Los filtros S90 (`isCirrusArtifact`: t_max_k bajo 273,15 K y magnitud sobre 10 MW) y S93
(`isDiffuseFieldArtifact`) son display-only y se calibraron contra el path D contextual de K sobre
cirrus frio: un cumulo cuyo pixel mas caliente esta bajo cero no podia tener fuente termica. Con la via
«codigo MIROVA» (MOD-D, #934, en produccion MODIS desde el 2026-11-02) esa premisa no vale: la via mira el
volcan en la grilla de 1 km de MIROVA y en pasadas oblicuas la celda mezcla el foco con nieve, asi que su
t_max queda bajo 0 grados con calor real. En la ablacion de S173 (Chillan, 27 pasadas) 7 records de la via
tienen t_max bajo 273,15 K, todos con cenit de 35 grados o mas, y en las 6 grillas frias que el verificador
cruzo MIROVA tiene magnitud (`experiments/_s173_cenit/ver_modis/v8_tmax_cirrus_salida.txt`, rama
loop/activo). El caso 2026-10-01 08:35 (cenit 50,45, t_max 269,57 K): la via dio 5,72 MW (MIROVA 5,18) y el
control X2 del verificador, con el doble (11,44 MW), cayo en el filtro y el tablero no lo publico. La via
no tiene path D: su detector es el de MIROVA, que es la referencia que el tablero replica.

QUE VIGILA. En las tres vistas vivas (index, mosaico, diario), con la funcion extraida del HTML y
ejecutada en node (A97) con el modulo `frontend/cambio_detector.js` cargado, que es quien lee la marca
(`esViaCodigoMirova`, un solo lugar, A102):
1. el caso X2 de Chillan con `via_codigo_mirova: true` no es artefacto (ni cirrus ni campo difuso);
2. el MISMO record sin la marca (K) sigue siendo artefacto cirrus: el filtro no se apago para K;
3. un record de K que corre con el aviso de la via (`via_codigo_mirova: "sin_grilla"`, A118) tampoco se
   exenta: es K, no la via;
4. un campo difuso de la via (S93) tampoco se oculta, y el mismo de K si.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Con la regla de antes (sin exencion) el caso 1 falla: lo comprueba
el control 2, que es el mismo record sin la marca y tiene que dar artefacto. (2) Si la extraccion se
rompiera, node lanza error y el test cae con mensaje, no pasa en verde.
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
// La marca de la via la lee el modulo compartido (A102), igual que en el navegador.
const CambioDetector = require(require('path').join(require('path').dirname(process.argv[3]), 'cambio_detector.js'));
const m = src.match(/const INNER_RADIUS_KM\s*=\s*([^;]+);/);
let includeFarDistance = false;
eval((m ? m[0] : '') + '\n' + ['mirovaEqVrp', 'isCirrusArtifact', 'isDiffuseFieldArtifact'].map(extraer).join('\n'));
const casos = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const arg = vista === 'diario.html' ? 'NevadosDeChillan' : 5;
console.log(JSON.stringify(casos.map(r => [isCirrusArtifact(r, arg) ? 1 : 0, isDiffuseFieldArtifact(r, arg) ? 1 : 0])));
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


# Chillan 2026-10-01 08:35, MODIS, cenit 50,45: campos del brazo X2 del verificador de S173
# (`v1_analisis_02_salida.txt` (c)); t_max de la grilla (`v8_tmax_cirrus_salida.txt`).
X2_CHILLAN = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-10-01 08:35", "distance_class": "summit",
              "t_max_k": 269.57, "vrp_mw": 11.442, "triggered_test1": False, "vrp_vent_mw": 0.0,
              "primary_cluster": {"vrp_mw": 11.442, "centroid_dist_km": 0.708, "n_pixels": 8}}
# Campo difuso S93 (forma del caso PCC 2026-05-05): t_max apenas sobre 0 grados, cientos de pixeles tibios.
DIFUSO = {"sensor": "MODIS_TERRA", "datetime_utc": "2026-05-05 03:00", "distance_class": "summit",
          "t_max_k": 274.95, "vrp_mw": 337.0, "triggered_test1": False, "vrp_vent_mw": 0.0,
          "primary_cluster": {"vrp_mw": 337.0, "centroid_dist_km": 1.0, "n_pixels": 670}}


def _con(base, **kw):
    r = json.loads(json.dumps(base))
    r.update(kw)
    return r


node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


@node
@pytest.mark.parametrize("vista", VISTAS)
def test_la_via_no_es_artefacto_y_k_si(vista):
    casos = [_con(X2_CHILLAN, via_codigo_mirova=True),          # 0: la via, caso Chillan
             _con(X2_CHILLAN),                                   # 1: el mismo record de K
             _con(X2_CHILLAN, via_codigo_mirova="sin_grilla"),   # 2: K con aviso de la via (A118)
             _con(DIFUSO, via_codigo_mirova=True),               # 3: campo difuso de la via
             _con(DIFUSO)]                                       # 4: campo difuso de K
    res = _correr(vista, casos)
    assert res[1][0] == 1, f"{vista}: control roto, el record de K tendria que ser cirrus"
    assert res[2][0] == 1, f"{vista}: un record de K con aviso de la via no se exenta (A118)"
    assert res[4][1] == 1, f"{vista}: control roto, el campo difuso de K tendria que ser artefacto"
    assert res[0] == [0, 0], f"{vista}: el caso X2 de Chillan de la via se oculta como artefacto: {res[0]}"
    assert res[3] == [0, 0], f"{vista}: un campo difuso de la via se oculta como artefacto: {res[3]}"
