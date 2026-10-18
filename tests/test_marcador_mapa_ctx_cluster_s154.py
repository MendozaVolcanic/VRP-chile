# -*- coding: utf-8 -*-
"""S154 (D-24, aprobado por Nicolás el 2026-10-18): el marcador primario del mapa de detalle es el cúmulo publicado.

POR QUÉ. El mapa de detalle de `frontend/index.html` dibuja por defecto sólo el primer punto de la lista. Para los records
anclados por la integral del Test 1 (`test1_roi`, `test1_nti_peak`) ese primer punto era `final_hotspot`, pero para los
anclados por el cúmulo contextual (`ctx_cluster`) era `anomaly_pixels[0]`, el píxel de más energía de TODA la escena, que
puede caer en un salar a 25 km aunque el cúmulo publicado esté en el cráter (A46). Con K (#850) todos los records son
`ctx_cluster`. Caso real, visto en el tablero publicado: Láscar 2026-10-10 05:06 VIIRS_NOAA20, rotulado «summit» y
«Confirmado por MIROVA», distancia 0,28 km en la tabla, dibujado a 24,7 km
(`experiments/_s154_marcador/lascar_20261010_0506_marcador_en_salar.jpg`).

QUÉ FIJA. (1) `pixelesDelMarcador(r, v)` pone `final_hotspot` primero para `ctx_cluster`, `test1_roi` y `test1_nti_peak`
y conserva los `anomaly_pixels` detrás (el toggle «Todos los pixels» sigue mostrando la evidencia). (2) Para el resto de
las fuentes no cambia nada. (3) El render del mapa usa esa función (frontera de palabra, A92). (4) Sobre los datos
reales de Láscar, ningún record `ctx_cluster` tiene su primer marcador lejos del cúmulo.
"""
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "frontend" / "index.html"

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
eval(extraer('pixelesDelMarcador'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
process.stdout.write(JSON.stringify(casos.map(([r, v]) => pixelesDelMarcador(r, v))));
"""


def correr(casos):
    with tempfile.TemporaryDirectory() as tmp:
        js, datos = Path(tmp) / "r.js", Path(tmp) / "c.json"
        js.write_text(_JS, encoding="utf-8")
        datos.write_text(json.dumps(casos), encoding="utf-8")
        o = subprocess.run(["node", str(js), str(HTML), str(datos)], capture_output=True, text=True, timeout=120)
        assert o.returncode == 0, o.stderr[-800:]
        return json.loads(o.stdout)


LEJOS = {"lat": -23.6, "lon": -67.5, "dist_km": 24.7, "vrp_mw": 0.4}
CERCA = {"lat": -23.37, "lon": -67.73, "dist_km": 0.3, "vrp_mw": 0.03}
VOLCAN = {"vent_lat": -23.3695, "vent_lon": -67.7319, "inner_radius_km": 5}


def rec(fuente, **kw):
    r = {"final_hotspot_source": fuente, "final_hotspot_lat": -23.371, "final_hotspot_lon": -67.733,
         "final_hotspot_dist_km": 0.28, "vrp_mw": 0.04, "t_max_k": 265.5, "anomaly_pixels": [LEJOS, CERCA]}
    r.update(kw)
    return r


def test_ctx_cluster_pone_el_cumulo_primero_y_conserva_los_pixeles():
    (px,) = correr([[rec("ctx_cluster"), VOLCAN]])
    assert (px[0]["lat"], px[0]["lon"], px[0]["dist_km"]) == (-23.371, -67.733, 0.28)
    assert px[0]["real_coord"] is True
    assert px[1:] == [LEJOS, CERCA]


def test_test1_sigue_igual():
    for fuente in ("test1_roi", "test1_nti_peak"):
        (px,) = correr([[rec(fuente), VOLCAN]])
        assert (px[0]["lat"], px[0]["lon"]) == (-23.371, -67.733) and px[1:] == [LEJOS, CERCA]


def test_otras_fuentes_no_cambian():
    # una fuente sin ancla honesta conserva el comportamiento anterior: el primer píxel de la lista
    (px,) = correr([[rec("eruption"), VOLCAN]])
    assert px == [LEJOS, CERCA]
    # sin píxeles ni ancla honesta, cae a final_hotspot como antes
    (px,) = correr([[rec("vent", anomaly_pixels=[]), VOLCAN]])
    assert len(px) == 1 and px[0]["vent_only"] is True


def test_ctx_cluster_sin_final_hotspot_cae_a_los_pixeles():
    (px,) = correr([[rec("ctx_cluster", final_hotspot_lat=None, final_hotspot_lon=None), VOLCAN]])
    assert px == [LEJOS, CERCA]


def test_el_render_del_mapa_usa_la_funcion():
    src = HTML.read_text(encoding="utf-8")
    # llamadas, no la definición («function pixelesDelMarcador(r, v)»)
    llamadas = re.findall(r"(?<!function )(?<![A-Za-z0-9_])pixelesDelMarcador\s*\(\s*r\s*,\s*v\s*\)", src)
    assert len(llamadas) == 1, llamadas
    # la cascada vieja ya no vive copiada en el render (A102)
    assert "const isHonestTest1" not in src


def _hv(a, b, c, d):
    p = math.radians
    return 2 * 6371 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))


def test_datos_reales_de_lascar_el_primer_marcador_es_el_cumulo():
    d = json.loads((ROOT / "data" / "mirova_equivalent" / "Lascar.json").read_text(encoding="utf-8"))
    rs = [r for r in d["records"] if r.get("final_hotspot_source") == "ctx_cluster" and r.get("anomaly_pixels")
          and r.get("final_hotspot_lat") is not None][-200:]
    # control positivo del instrumento: entre esos records hay píxeles 0 lejos del cúmulo (si no, la prueba no mide nada)
    lejos_antes = sum(_hv(r["anomaly_pixels"][0]["lat"], r["anomaly_pixels"][0]["lon"], r["final_hotspot_lat"],
                          r["final_hotspot_lon"]) > 2 for r in rs)
    assert lejos_antes > 0
    out = correr([[r, VOLCAN] for r in rs])
    lejos = [r["datetime_utc"] for r, px in zip(rs, out)
             if _hv(px[0]["lat"], px[0]["lon"], r["final_hotspot_lat"], r["final_hotspot_lon"]) > 0.01]
    assert lejos == []
