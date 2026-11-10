# -*- coding: utf-8 -*-
"""S175 (V33A-01): con «Todos los pixels» el mapa de detalle dibuja todos los records aunque un píxel no traiga energía.

POR QUÉ. La vía MODIS «código MIROVA» guarda sus píxeles anómalos sin `vrp_mw` por píxel, porque MIROVA reporta la suma de
los píxeles alertados y no la energía de cada uno (D32). El mapa de detalle de `frontend/index.html`, al desplegar todos
los píxeles, calculaba el radio y el popup con esa energía: `px.vrp_mw.toFixed` lanzaba TypeError dentro del
`hotspots.forEach`, que no tiene try/catch, y el mapa dejaba de dibujar los records siguientes sin avisar. En Nevados de
Chillán se perdían los días más recientes. El operador veía menos datos y nada le decía que faltaban.

QUÉ FIJA, ejecutando en node el bloque real del render (no una copia): (1) los records posteriores al píxel sin energía
se siguen dibujando; (2) ese píxel tiene radio finito y su popup dice que no trae el dato, sin 0 inventado ni NaN; (3) un
píxel con energía, también un 0 que viene en el dato, se muestra como siempre; (4) «Solo principal» no cambia; (5) sobre
los records reales de Chillán no se pierde ninguno.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "frontend" / "index.html"
SIN_DATO = "sin dato de VRP por pixel"

_JS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function cerrarLlave(i) {
  let d = 0;
  for (let k = src.indexOf('{', i); k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return k; }
  }
  throw new Error('llave sin cerrar');
}
function extraer(nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) throw new Error('no encontre function ' + nombre);
  return src.slice(i, cerrarLlave(i) + 1);
}
function extraerBloqueDelMapa() {
  const marca = 'hotspots.forEach((r, i) => {';
  const i = src.indexOf(marca);
  if (i < 0 || src.indexOf(marca, i + 1) >= 0) throw new Error('la marca del bloque debe aparecer una sola vez');
  const bloque = src.slice(i, cerrarLlave(i) + 1) + ');';
  if (!bloque.includes('renderPixels.forEach') || !bloque.includes('bindPopup')) throw new Error('bloque equivocado');
  return bloque;
}
eval(extraer('esAnclaHonesta'));
eval(extraer('pixelesDelMarcador'));
const correrBloque = new Function('hotspots', 'v', 'onlyPrimaryPixel', 'includeFarDistance', 'colorMap', 'allPts',
  'markersByKey', 'map', 'makeHotspotMarker', 'pixelesDelMarcador', extraerBloqueDelMapa());

const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
process.stdout.write(JSON.stringify(casos.map(c => {
  const marcadores = [];
  const markersByKey = new Map();
  const makeHotspotMarker = (lat, lon, estilo, sensor) => ({
    addTo() { return this; },
    bindPopup(html) {
      marcadores.push({ lat, lon, sensor, html, radio: estilo.radius, radio_finito: Number.isFinite(estilo.radius) });
      return this;
    },
  });
  let error = null;
  // La excepción se captura para que la prueba falle por aserción y muestre qué alcanzó a dibujarse.
  try {
    correrBloque(c.hotspots, c.v, c.onlyPrimaryPixel, true, {}, [], markersByKey, {}, makeHotspotMarker, pixelesDelMarcador);
  } catch (e) { error = String(e); }
  return { error, marcadores, claves: [...markersByKey.keys()] };
})));
"""

VOLCAN = {"lat": -36.863, "lon": -71.377, "inner_radius_km": 5}


def correr(hotspots, solo_principal=False):
    caso = {"hotspots": hotspots, "v": VOLCAN, "onlyPrimaryPixel": solo_principal}
    with tempfile.TemporaryDirectory() as tmp:
        js, datos = Path(tmp) / "r.js", Path(tmp) / "c.json"
        js.write_text(_JS, encoding="utf-8")
        datos.write_text(json.dumps([caso]), encoding="utf-8")
        o = subprocess.run(["node", str(js), str(HTML), str(datos)], capture_output=True, text=True, encoding="utf-8",
                           timeout=120)
        assert o.returncode == 0, o.stderr[-800:]
        return json.loads(o.stdout)[0]


def pixel(i, **extra):
    return {"lat": -36.86 - i * 0.01, "lon": -71.38, "dist_km": 0.5 + i, "bt_k": 340.0, **extra}


def pixel_via(i):
    # Las claves reales de la vía: pipeline/mirova_v750_codigo.py (sin vrp_mw).
    return pixel(i, fila=i, col=i)


def record(fecha, pixeles, fuente="ctx_cluster", sensor="VIIRS_NOAA20", **extra):
    return {"datetime_utc": fecha, "sensor": sensor, "final_hotspot_source": fuente, "final_hotspot_lat": -36.861,
            "final_hotspot_lon": -71.378, "final_hotspot_dist_km": 0.4, "vrp_mw": 12.8, "t_max_k": 345.0,
            "distance_class": "summit", "anomaly_pixels": pixeles, **extra}


def record_via(fecha, n=3):
    return record(fecha, [pixel_via(i) for i in range(n)], fuente="codigo_mirova", sensor="MODIS_AQUA",
                  via_codigo_mirova=True)


def clave(r):
    return f"{r['datetime_utc']}|{r['sensor']}"


def este_pixel(marcador):
    m = re.search(r"<b>Este pixel:</b> ([^<]*)<br>", marcador["html"])
    return m.group(1) if m else None


def secuencia_con_via_al_medio():
    return [record("2026-11-01 05:00", [pixel(0, vrp_mw=1.5)]),
            record_via("2026-11-02 07:30"),
            record("2026-11-03 05:00", [pixel(0, vrp_mw=2.5)]),
            record_via("2026-11-04 08:45"),
            record("2026-11-05 05:00", [pixel(0, vrp_mw=3.5)])]


def test_los_records_posteriores_al_pixel_sin_vrp_se_dibujan():
    hotspots = secuencia_con_via_al_medio()
    salida = correr(hotspots)
    assert salida["error"] is None
    assert salida["claves"] == [clave(r) for r in hotspots]


@pytest.mark.parametrize("sin_energia", [{}, {"vrp_mw": None}], ids=["clave_ausente", "valor_null"])
def test_el_pixel_sin_vrp_dice_que_no_trae_el_dato(sin_energia):
    r = record("2026-11-02 07:30", [pixel(0, **sin_energia), pixel(1, **sin_energia)], fuente="codigo_mirova",
               sensor="MODIS_AQUA")
    salida = correr([r])
    assert salida["error"] is None
    # El primero es el ancla del record, que sí trae energía; detrás van los dos píxeles sin ella.
    assert [este_pixel(m) for m in salida["marcadores"]][1:] == [f"{SIN_DATO} (pixel #2)", f"{SIN_DATO} (pixel #3)"]


def test_el_pixel_sin_vrp_no_produce_nan_ni_un_cero_inventado():
    salida = correr([record_via("2026-11-02 07:30")])
    assert salida["error"] is None
    assert len(salida["marcadores"]) == 4
    for m in salida["marcadores"]:
        assert m["radio_finito"], m
        assert "NaN" not in m["html"] and "undefined" not in m["html"], m["html"]
    for m in salida["marcadores"][1:]:
        assert not re.search(r"<b>Este pixel:</b>\s*0[.,0]*\s*MW", m["html"]), m["html"]


@pytest.mark.parametrize("energia, texto, radio", [
    (0.1234, "0.1234 MW (pixel #2)", 4),
    (40.0, "40.0000 MW (pixel #2)", 4 + 1.6020599913279623 * 5),
    (0, "0.0000 MW (pixel #2)", 4),  # un 0 que viene en el dato es un dato, no «sin dato»
])
def test_el_pixel_con_vrp_se_muestra_como_siempre(energia, texto, radio):
    salida = correr([record("2026-11-02 07:30", [pixel(0, vrp_mw=energia)])])
    assert salida["error"] is None
    marcador = salida["marcadores"][1]
    assert este_pixel(marcador) == texto
    assert marcador["radio"] == pytest.approx(radio)


def test_solo_principal_sigue_con_un_marcador_por_record():
    hotspots = secuencia_con_via_al_medio()
    salida = correr(hotspots, solo_principal=True)
    assert salida["error"] is None
    assert salida["claves"] == [clave(r) for r in hotspots]
    assert len(salida["marcadores"]) == len(hotspots)


def test_datos_reales_de_chillan_no_se_pierde_ningun_record():
    d = json.loads((ROOT / "data" / "mirova_equivalent" / "NevadosDeChillan.json").read_text(encoding="utf-8"))
    registros = sorted(d["records"], key=lambda r: r["datetime_utc"])
    indices = [i for i, r in enumerate(registros)
               if r.get("via_codigo_mirova") and any(p.get("vrp_mw") is None for p in (r.get("anomaly_pixels") or []))]
    if not indices:
        pytest.skip("ningún record real de Chillán trae hoy un píxel sin vrp_mw: el caso lo cubren las pruebas de arriba")
    # Desde un poco antes del primer píxel sin energía: ahí se cortaba el dibujo.
    hotspots = registros[max(0, indices[0] - 20):]
    salida = correr(hotspots)
    assert salida["error"] is None
    # La vara es «Solo principal» sobre los mismos records: ese camino nunca lee la energía de un píxel sin ancla, y un
    # record sin ninguna posición tampoco se dibuja ahí. Debe llegar hasta el último record posterior al píxel sin energía.
    principal = correr(hotspots, solo_principal=True)
    assert principal["error"] is None
    assert clave(registros[indices[-1]]) in principal["claves"]
    assert salida["claves"] == principal["claves"]
    assert all(m["radio_finito"] for m in salida["marcadores"])
