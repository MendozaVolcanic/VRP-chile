# -*- coding: utf-8 -*-
"""S172 (mini auditoría MA172-102): el tablero reconoce `codigo_mirova` como ancla honesta, en un solo lugar (A102).

POR QUÉ. La vía «código MIROVA» suma todos los píxeles alertados de la grilla, también los lejanos, y escribe en
`final_hotspot` el centroide del cúmulo más radiante (`pipeline/mirova_v750_codigo.py`, `final_hotspot_source:
"codigo_mirova"`). `frontend/index.html` sólo usaba el ancla del record para `ctx_cluster`, `test1_roi` y
`test1_nti_peak`, en siete listas copiadas; con la vía caía a `anomaly_pixels[0]`, el primer alertado en orden de
barrido. En los records reales de Chillán de la sombra el cúmulo está a 0,567 km y el marcador quedaba a 2,233 km, y
con un segundo foco a 15 km el marcador rojo de «cráter» se dibujaba ahí. Ahora la lista vive en `esAnclaHonesta` y
las siete copias la llaman.
"""
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "frontend" / "index.html"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="se prueba con node")

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
eval(extraer('esAnclaHonesta'));
eval(extraer('pixelesDelMarcador'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
process.stdout.write(JSON.stringify(casos.map(([r, v]) => [esAnclaHonesta(r.final_hotspot_source), pixelesDelMarcador(r, v)])));
"""

LEJOS = {"lat": -36.73, "lon": -71.37, "dist_km": 16.15, "vrp_mw": 0.4}
CERCA = {"lat": -36.86, "lon": -71.37, "dist_km": 0.4, "vrp_mw": 1.0}


def correr(casos):
    with tempfile.TemporaryDirectory() as tmp:
        js, datos = Path(tmp) / "r.js", Path(tmp) / "c.json"
        js.write_text(_JS, encoding="utf-8")
        datos.write_text(json.dumps(casos), encoding="utf-8")
        o = subprocess.run(["node", str(js), str(HTML), str(datos)], capture_output=True, text=True, timeout=120)
        assert o.returncode == 0, o.stderr[-800:]
        return json.loads(o.stdout)


def rec(fuente):
    return {"final_hotspot_source": fuente, "final_hotspot_lat": -36.864, "final_hotspot_lon": -71.377,
            "final_hotspot_dist_km": 0.567, "vrp_mw": 2.0, "t_max_k": 300.0, "anomaly_pixels": [LEJOS, CERCA]}


def test_el_marcador_de_un_record_de_la_via_es_el_cumulo():
    ((honesta, px),) = correr([[rec("codigo_mirova"), {}]])
    assert honesta is True
    assert (px[0]["lat"], px[0]["lon"], px[0]["dist_km"]) == (-36.864, -71.377, 0.567)
    assert px[1:] == [LEJOS, CERCA]          # la evidencia sigue detrás («Todos los pixels»)


def test_las_fuentes_de_k_siguen_y_las_demas_no_cambian():
    res = correr([[rec(f), {}] for f in ("ctx_cluster", "test1_roi", "test1_nti_peak", "eruption", "vent")])
    assert [h for h, _ in res] == [True, True, True, False, False]
    assert res[3][1] == [LEJOS, CERCA]


def test_un_solo_lugar_las_siete_copias_llaman_a_la_funcion():
    src = HTML.read_text(encoding="utf-8")
    assert len(re.findall(r"function esAnclaHonesta\(", src)) == 1
    # ninguna lista literal de fuentes queda copiada fuera de la función (A102)
    cuerpo = src.replace(re.search(r"function esAnclaHonesta\([^\n]*", src).group(0), "")
    assert not re.search(r'\[\s*"(ctx_cluster|test1_roi|test1_nti_peak)"\s*,', cuerpo)
    llamadas = re.findall(r"(?<!function )(?<![A-Za-z0-9_])esAnclaHonesta\(", src)
    assert len(llamadas) == 7, len(llamadas)
