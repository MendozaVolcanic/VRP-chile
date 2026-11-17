# -*- coding: utf-8 -*-
"""S190 (hallazgo H01 de la auditoría de Codex): el tablero no borra una erupción grande que el almacén conservó.

POR QUÉ. `pipeline/store.py::_apply_sanity_cap` discrimina por CAUSA y no por magnitud: sobre el tope de cordura
de 50.000 MW, si la temperatura de brillo es creíble (t_max_k bajo store.techo_bt_k: 634 K en VIIRS 750, 500 K en el resto) conserva la VRP y marca
`vrp_exceeds_sanity_cap: true`, porque 50 GW está dentro de lo físicamente posible (el récord documentado por MIROVA
ronda los 70 GW). Si la temperatura es imposible (saturación) anula la VRP. Pero las funciones del tablero
(`mirovaEqVrp` y `mirovaEqVrpCore` en index, diario y mosaico) y `pipeline/audit_metrics.py::mirova_eq_vrp`
devolvían 0 sobre 50.000 MW sin leer la marca: la erupción más grande que el almacén guarda a propósito se habría
visto como una noche tranquila. Hoy no hay records afectados (máximo publicado 451 MW): es latente.

QUÉ VIGILA. Con las funciones extraídas del HTML y ejecutadas en node (patrón de
`tests/test_f5_no_recorta_via_s180.py`), en las tres vistas y en el camino de display (`mirovaEqVrpCore`, porque
`USE_F5_CORE = true`) y en el de detección (`mirovaEqVrp`):
1. record marcado con BT creíble y 60 GW: se muestra (cúmulo y fallback sin cúmulo);
2. record K de VIIRS 375 marcado cuyo núcleo F5' pasa de 50 GW: se muestra el núcleo;
3. controles que siguen en 0: sin marca sobre el tope (fósil), basura (BT 566 K, sin marca), marca que no es el
   booleano `true` (texto «true»), y marcado pero lejos del cráter sin «incluir lejanas»;
4. un record normal (30 MW) no cambia, y el borde 40 GW sin marca se muestra igual que antes.
Y lo mismo para `audit_metrics.mirova_eq_vrp` (regla R1 y R7: sintéticas antes de tocarla), que debe dar lo mismo
que las tres vistas en cada caso.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Antes del arreglo los casos 1 y 2 dan 0 (rojo guardado en la descripción del
PR); los controles 3 tienen que seguir en 0 después, así que un arreglo que quite el tope sin leer la marca también
cae. (2) Si la extracción del HTML se rompe, node lanza error y la prueba cae con mensaje.
"""
import json
import os
import shutil
import subprocess
import tempfile

import pytest

from pipeline.audit_metrics import mirova_eq_vrp

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
const arg = vista === 'diario.html' ? 'Lascar' : 5;
console.log(JSON.stringify(casos.map(r => [mirovaEqVrp(r, arg), mirovaEqVrpCore(r, arg)])));
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


LAT, LON = -23.3700, -67.7300


def _rec(vrp, t_max_k=480.0, marca=True, sensor="VIIRS_NOAA20_750", dist=0.6, **kw):
    """Record como lo deja `store._apply_sanity_cap` (marca y BT) con un cúmulo en el cráter de Láscar."""
    r = {"sensor": sensor, "datetime_utc": "2026-11-10 05:00", "distance_class": "summit",
         "via_codigo_mirova": True, "vrp_mw": vrp, "t_max_k": t_max_k,
         "primary_cluster": {"vrp_mw": vrp, "centroid_lat": LAT, "centroid_lon": LON,
                             "centroid_dist_km": dist, "n_pixels": 225}}
    if marca is not None:
        r["vrp_exceeds_sanity_cap"] = marca
    r.update(kw)
    return r


def _legacy(vrp, marca=True):
    """Record sin `primary_cluster` (fallback de índice y mosaico)."""
    r = {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-10 05:00", "vrp_mw": vrp, "t_max_k": 480.0}
    if marca is not None:
        r["vrp_exceeds_sanity_cap"] = marca
    return r


# Caso, valor esperado en detección (mirovaEqVrp), valor esperado en display (mirovaEqVrpCore).
CASOS = [
    ("marcado_60gw", _rec(60000.0), 60000.0, 60000.0),
    # K de VIIRS 375 (sin la vía) marcado, con núcleo F5' persistido por el pipeline sobre 50 GW.
    ("marcado_nucleo_55gw", _rec(60000.0, sensor="VIIRS_NOAA20", via_codigo_mirova=None,
                                 f5_core_vrp_mw=55000.0), 60000.0, 55000.0),
    ("normal_30mw", _rec(30.0, t_max_k=330.0, marca=None), 30.0, 30.0),
    ("sin_marca_40gw", _rec(40000.0, marca=None), 40000.0, 40000.0),
    ("fosil_sin_marca_60gw", _rec(60000.0, marca=None), 0.0, 0.0),
    ("basura_bt_566", _rec(60000.0, t_max_k=566.0, marca=None), 0.0, 0.0),
    ("marca_texto", _rec(60000.0, marca="true"), 0.0, 0.0),
    ("marcado_lejos", _rec(60000.0, dist=20.0), 0.0, 0.0),
    # K de VIIRS 375 sin marca con núcleo sobre el tope: sigue en 0 aunque el cúmulo sea válido.
    ("nucleo_sin_marca_55gw", _rec(40000.0, sensor="VIIRS_NOAA20", marca=None, via_codigo_mirova=None,
                                   f5_core_vrp_mw=55000.0), 40000.0, 0.0),
]
for _n, _r, *_ in CASOS:
    if _r.get("via_codigo_mirova") is None:
        _r.pop("via_codigo_mirova", None)

LEGACY = [("legacy_marcado_60gw", _legacy(60000.0), 60000.0, 60000.0)]
LEGACY_SIN_MARCA = [("legacy_fosil_60gw", _legacy(60000.0, marca=None), 0.0, 0.0)]


def _casos_vista(vista):
    # diario no capea el fallback sin cúmulo (divergencia previa, S126 punto 2 y 3): ahí sólo va el marcado.
    return CASOS + LEGACY + ([] if vista == "diario.html" else LEGACY_SIN_MARCA)


node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


@node
@pytest.mark.parametrize("vista", VISTAS)
def test_tablero_muestra_la_erupcion_marcada_y_sigue_anulando_la_basura(vista):
    casos = _casos_vista(vista)
    res = _correr(vista, [c[1] for c in casos])
    errores = []
    for (nombre, _r, det, disp), (got_det, got_disp) in zip(casos, res):
        if got_det != pytest.approx(det):
            errores.append(f"{nombre}: mirovaEqVrp dio {got_det}, esperado {det}")
        if got_disp != pytest.approx(disp):
            errores.append(f"{nombre}: mirovaEqVrpCore dio {got_disp}, esperado {disp}")
    assert not errores, f"{vista}: " + "; ".join(errores)


@pytest.mark.parametrize("nombre,r,det,_disp", CASOS + LEGACY + LEGACY_SIN_MARCA,
                         ids=[c[0] for c in CASOS + LEGACY + LEGACY_SIN_MARCA])
def test_audit_metrics_lee_la_marca_igual_que_el_tablero(nombre, r, det, _disp):
    assert mirova_eq_vrp(r, "Lascar") == pytest.approx(det), nombre


@node
@pytest.mark.parametrize("vista", ["index.html", "mosaico.html"])
def test_audit_metrics_coincide_con_el_tablero_caso_a_caso(vista):
    casos = CASOS + LEGACY + LEGACY_SIN_MARCA
    res = _correr(vista, [c[1] for c in casos])
    for (nombre, r, *_), (got_det, _) in zip(casos, res):
        assert mirova_eq_vrp(r, "Lascar") == pytest.approx(got_det), f"{vista} {nombre}"
