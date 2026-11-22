# -*- coding: utf-8 -*-
"""S193 (pedido de Nicolás, 2026-11-21: «tenemos gente revisando las anomalías, sería bueno mejorar los mapas»):
el tablero marca la pasada cuyo píxel más caliente cae sobre agua y dibuja los lagos en el mapa.

POR QUÉ. De noche un lago queda más tibio que la roca y la nieve que lo rodean, y el detector (como el de MIROVA, que
no tiene máscara de agua) puede alertarlo: Coppola 2016a (documentacion/sp426_5.txt, l. 689 a 694) habla de falsas
detecciones de menos de 5 MW en orillas, que el operador quita mirando el mapa. La sesión S193 «lagos»
(experiments/_s193_lagos/INFORME.md) midió 124 de 14.391 pasadas de la vía con el pico sobre agua, 35 en Laguna del
Maule y 21 en Carrán-Los Venados. Sobre la imagen satelital nocturna el revisor no distinguía un lago de un cráter.
La marca sólo informa: no cambia ninguna detección ni ningún valor publicado, porque una erupción también puede
empezar en un lago (Laguna del Maule, maares de Carrán).

QUÉ FIJA, ejecutando frontend/agua.js en node:
(1) fraccionAgua recorta polígonos (con islas) contra la celda y da la fracción exacta; fuera de la ventana de la capa
    o sin capa da null, no 0 (un «0 % de agua» inventado diría «tierra» donde no se midió).
(2) pixelPico elige el de mayor temperatura de brillo, como medir_agua.py (no el primero de la lista).
(3) aguaDePasada marca «sobre agua» desde 50 % de la celda, con su control (49 % no marca).
(4) Con las capas reales: el píxel de Laguna del Maule del 2026-11-20 05:42 (NOAA-20), que el informe pone sobre el
    lago, sale sobre agua; un píxel en el cráter de Láscar sale en tierra (control: la función puede dar ≠ 0 y = 0).
(5) El lado de la celda es el de sensorFootprintKm de index.html para los 8 sensores (A102: no derivar).
(6) Hay una capa por volcán activo, liviana, con su fuente; las tres vistas cargan el módulo y lo usan.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? Cada prueba tiene su caso que no debe marcar. (2) ¿Y
si la carga muriera? `_node` exige returncode 0 y el módulo se carga con require: si falta el archivo, la prueba cae.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"
MODULO = FRONT / "agua.js"
CAPAS = FRONT / "agua"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="el módulo se prueba con node")


def _node(cuerpo, datos=None):
    # Los datos van por la entrada estándar: una capa real no cabe en la línea de comandos de Windows.
    js = ("const A = require(" + json.dumps(str(MODULO)) + ");\n"
          "const DATOS = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" + cuerpo)
    r = subprocess.run(["node", "-e", js], input=json.dumps(datos), capture_output=True, text=True, encoding="utf-8",
                       timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _capa_cuadrada(isla=False):
    """Lago cuadrado de 0,02° de lado centrado en (-36, -70), ventana de 30 km."""
    ext = [[-70.01, -36.01], [-69.99, -36.01], [-69.99, -35.99], [-70.01, -35.99], [-70.01, -36.01]]
    anillos = [ext]
    if isla:
        anillos.append([[-70.002, -36.002], [-69.998, -36.002], [-69.998, -35.998], [-70.002, -35.998],
                        [-70.002, -36.002]])
    return {"type": "FeatureCollection", "properties": {"lat": -36.0, "lon": -70.0, "media_ventana_km": 30},
            "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": anillos}}]}


def test_fraccion_recorta_poligono_e_isla(tmp_path):
    datos = {"capa": _capa_cuadrada(), "isla": _capa_cuadrada(isla=True)}
    cuerpo = """
const c = DATOS.capa, i = DATOS.isla;
const lado = 0.375, half = 0.375 / 2 / 111.32 / Math.cos(-36 * Math.PI / 180);
const out = {
  dentro: A.fraccionAgua(c, -36.0, -70.0, lado),
  lejos: A.fraccionAgua(c, -36.1, -70.1, lado),
  // celda centrada justo en el borde este del lago: la mitad oeste es agua
  borde: A.fraccionAgua(c, -36.0, -69.99, lado),
  isla: A.fraccionAgua(i, -36.0, -70.0, lado),
  fuera_ventana: A.fraccionAgua(c, -37.0, -70.0, lado),
  sin_capa: A.fraccionAgua(null, -36.0, -70.0, lado),
};
process.stdout.write(JSON.stringify(out));
"""
    o = _node(cuerpo, datos)
    assert o["dentro"] == pytest.approx(1.0, abs=1e-9)
    assert o["lejos"] == 0
    assert o["borde"] == pytest.approx(0.5, abs=1e-6)
    # isla de 0,004° de lado dentro de una celda de ~0,0034° × 0,0042°: le quita casi toda el agua
    assert 0 <= o["isla"] < 0.2, o
    assert o["fuera_ventana"] is None
    assert o["sin_capa"] is None


def test_pixel_pico_es_el_de_mayor_temperatura():
    r = {"anomaly_pixels": [{"lat": -36, "lon": -70, "bt_k": 280}, {"lat": -36.1, "lon": -70.1, "bt_k": 300},
                            {"lat": -36.2, "lon": -70.2}]}
    sin_bt = {"anomaly_pixels": [{"lat": -36.3, "lon": -70.3}, {"lat": -36.4, "lon": -70.4}]}
    o = _node("process.stdout.write(JSON.stringify([A.pixelPico(DATOS[0]), A.pixelPico(DATOS[1]), A.pixelPico(DATOS[2]),"
              " A.pixelPico(null)]));", [r, sin_bt, {"anomaly_pixels": []}])
    assert o[0]["bt_k"] == 300
    assert o[1]["lat"] == -36.3
    assert o[2] is None and o[3] is None


def test_sobre_agua_desde_la_mitad_de_la_celda():
    # La celda de 375 m centrada en el borde este del lago es 50 % agua; corrida hacia el este, menos.
    capa = _capa_cuadrada()
    r50 = {"sensor": "VIIRS_NOAA20", "t_bg_k": 270, "anomaly_pixels": [{"lat": -36.0, "lon": -69.99, "bt_k": 281}]}
    r49 = {"sensor": "VIIRS_NOAA20", "t_bg_k": 270, "anomaly_pixels": [{"lat": -36.0, "lon": -69.98995, "bt_k": 281}]}
    vacio = {"sensor": "VIIRS_NOAA20", "anomaly_pixels": []}
    cuerpo = """
const [c, a, b, v] = DATOS;
const ma = A.aguaDePasada(a, c), mb = A.aguaDePasada(b, c);
process.stdout.write(JSON.stringify({a: ma, b: mb, vacio: A.aguaDePasada(v, c), sin_capa: A.aguaDePasada(a, null),
  texto: A.textoAgua(ma), umbral: A.UMBRAL_CELDA}));
"""
    o = _node(cuerpo, [capa, r50, r49, vacio])
    assert o["umbral"] == 0.5
    assert o["a"]["sobreAgua"] is True and o["a"]["fraccion"] >= 0.5
    assert o["b"]["sobreAgua"] is False and 0.4 < o["b"]["fraccion"] < 0.5
    assert o["a"]["dT"] == pytest.approx(11.0)
    assert o["a"]["nAgua"] == 1 and o["a"]["n"] == 1
    assert o["vacio"] is None and o["sin_capa"] is None
    assert "agua" in o["texto"] and "%" in o["texto"]


def _capa_real(nombre):
    return json.loads((CAPAS / f"{nombre}.geojson").read_text(encoding="utf-8"))


def test_capas_reales_maule_sobre_agua_y_lascar_en_tierra():
    # Pixel de experiments/_s193_lagos/INFORME.md §1 (sombra del 2026-11-20, NOAA-20 05:42, 0,12 MW, «sobre el lago»)
    maule = {"sensor": "VIIRS_NOAA20", "t_bg_k": 266.86,
             "anomaly_pixels": [{"lat": -36.03513, "lon": -70.52457, "dist_km": 3.19, "bt_k": 275.02}]}
    # Cráter de Láscar (vent de index.html): roca, sin agua
    lascar = {"sensor": "VIIRS_NOAA20", "t_bg_k": 270,
              "anomaly_pixels": [{"lat": -23.36293, "lon": -67.731416, "bt_k": 330}]}
    cuerpo = """
const [cm, rm, cl, rl] = DATOS;
process.stdout.write(JSON.stringify([A.aguaDePasada(rm, cm), A.aguaDePasada(rl, cl)]));
"""
    m, l = _node(cuerpo, [_capa_real("LagunaDelMaule"), maule, _capa_real("Lascar"), lascar])
    assert m["sobreAgua"] is True and m["fraccion"] > 0.9, m
    assert l["sobreAgua"] is False and l["fraccion"] == 0, l


def _fuente(src, nombre):
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index(") {", m.end()) + 2
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def test_lado_de_celda_igual_al_de_index():
    sensores = ["MODIS_TERRA", "MODIS_AQUA", "VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21",
                "VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"]
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    cuerpo = _fuente(src, "sensorFootprintKm") + """
process.stdout.write(JSON.stringify(DATOS.map(s => [sensorFootprintKm(s), A.ladoCeldaKm(s)])));
"""
    for idx, agua in _node(cuerpo, sensores):
        assert idx == agua


def _volcanes_activos():
    vy = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    vs = vy["volcanoes"] if isinstance(vy, dict) else vy
    return [v["name"] for v in vs if v.get("active", True) is not False]


def test_una_capa_liviana_por_volcan_activo():
    total = 0
    for nombre in _volcanes_activos():
        f = CAPAS / f"{nombre}.geojson"
        assert f.exists(), nombre
        total += f.stat().st_size
        gj = json.loads(f.read_text(encoding="utf-8"))
        p = gj["properties"]
        assert "JRC" in p["fuente"] and p["umbral_ocurrencia_pct"] == 50
        assert p["media_ventana_km"] >= 26   # grilla de la vía de 51 km más media celda de 1 km
        assert gj["type"] == "FeatureCollection"
    assert total < 3 * 1024 * 1024, total


def test_las_tres_vistas_cargan_y_usan_el_modulo():
    for vista in ("index.html", "diario.html", "mosaico.html"):
        src = (FRONT / vista).read_text(encoding="utf-8")
        assert re.search(r'<script src="agua\.js"></script>', src), vista
        assert "AguaTablero.aguaDePasada(" in src, vista
    idx = (FRONT / "index.html").read_text(encoding="utf-8")
    assert "AguaTablero.cargarCapa(" in idx and "L.geoJSON(" in idx
