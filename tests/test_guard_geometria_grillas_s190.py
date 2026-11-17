# -*- coding: utf-8 -*-
"""S190 (auditoría de Codex, AD03): la grilla fija de cada volcán, su punto de referencia y las cajas ROI.

POR QUÉ. La vía «código MIROVA» (pipeline/mirova_v750_codigo.py) remuestrea cada pasada a una grilla UTM fija por
volcán (pipeline/grillas_mirova.yaml: X0, Y0, centro_lat, centro_lon). El verificador V4 de S190
(D:\\vrp-trabajo\\temporales\\s190_codex\\verif\\V4\\VEREDICTO.md) encontró dos fallas silenciosas:

1. El volcán se reconoce leyendo volcanoes.yaml en vivo (volcan_por_coordenadas), pero X0, Y0 está congelado en
   grillas_mirova.yaml. Si alguien corrige una coordenada en volcanoes.yaml y no la grilla, la vía sigue reconociendo
   el volcán y lo mira con la grilla vieja, sin avisar: el cráter queda corrido dentro de la caja sensible.
2. Si el cráter (el ancla que ubica las cajas: get_detection_anchor, que run_pipeline pasa como vent_lat, vent_lon)
   cae fuera de la grilla o a menos de media caja del borde, caja_roi("crater") se queda sin ninguna celda sensible y
   caja_v375 recorta el cuadro de 13 x 13 al borde. Ninguna de las dos lanza error: la vía corre ciega.

Qué fija cada bloque:
  (a) Los 34 fuera del NRT (sin TIF de MIROVA): X0, Y0 es el UTM del lat/lon de volcanoes.yaml y centro_lat/lon es
      ese mismo lat/lon, con la regla del generador (experiments/_s172_sombra34/generar_grillas_34.py, entrada()).
  (b) Los 11 Tier A: MIROVA usa su propio punto (A5: el valor oficial de MIROVA se usa tal cual), así que NO se exige
      igualdad. Se fija la distancia declarada entre UTM(volcanoes.yaml) y X0, Y0: 233, 1.885 y 2.787 m en Lascar,
      PlanchonPeteroa y Tupungatito (cabecera de grillas_mirova.yaml) y a lo más 1,5 m en los otros 8 (redondeo del
      TIF; la misma cota del control del generador). Si alguien mueve un Tier A en volcanoes.yaml, la distancia cambia
      y la prueba lo dice. La clase de distancia de los Tier A se mide desde vent_lat, vent_lon, no desde X0, Y0; eso
      lo cubre el bloque (c).
  (c) Los 45 y los tres sensores: el ancla de detección cae dentro de la grilla y la caja que arma
      calcular_vrp_granulo (caja_roi con la ROI del volcán en VIIRS 750 y MODIS, caja_v375 en VIIRS 375) tiene su
      región sensible entera, sin recorte. Se llama a las funciones reales del port, con los mismos argumentos.

Tolerancias (medidas el 2026-11-17 sobre main 736f3734e y sobre los yaml del commit 19ff4c3c9 de la sesión de
coordenadas, que corrige 7 de los 34):
  - Los 34: |dx| y |dy| hasta 0,06 m por eje. El generador redondea X0, Y0 a 0,1 m, así que el error de redondeo es a
    lo más 0,05 m por eje; lo medido es 0,048 m (main) y 0,050 m (19ff4c3c9). El centímetro de margen cubre
    diferencias de versión de PROJ en la proyección. centro_lat/lon: hasta 5e-6 grados (redondeo a 5 decimales; MacaCay
    en 19ff4c3c9 trae -73.169326 y la grilla -73.16933).
  - Los 3 Tier A con punto propio: la distancia declarada, en metros enteros, más o menos 1 m (0,5 m de redondeo del
    número declarado y 0,5 m de margen). Medido: 232,95; 1.884,81; 2.786,89 m.
  - Los 8 Tier A con el punto del yaml: hasta 1,5 m. Medido: 0,93 a 1,02 m.

Cómo correr los controles sin tocar el repo: GUARDA_GEOMETRIA_GRILLAS_YAML y GUARDA_GEOMETRIA_VOLCANES_YAML apuntan
a otros archivos (por ejemplo los yaml de una rama o una copia mutada en un temporal). Sin esas variables se usan los
del repo. Las dos preguntas del instrumento: (1) mide la grilla y la caja que usa la vía porque llama a las mismas
funciones con los mismos argumentos; (2) puede fallar: con una coordenada de volcanoes.yaml mutada y con un cráter
fuera de la grilla da rojo por aserción (registro en la descripción del PR).
"""
import math
import os
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "_s172_sombra34"))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
import generar_grillas_34 as G  # noqa: E402

NRT = ROOT / ".github" / "workflows" / "nrt.yml"
GRILLAS = Path(os.environ.get("GUARDA_GEOMETRIA_GRILLAS_YAML") or ROOT / "pipeline" / "grillas_mirova.yaml")
VOLCANES = Path(os.environ.get("GUARDA_GEOMETRIA_VOLCANES_YAML") or ROOT / "volcanoes.yaml")

TOL_34_EJE_M = 0.06
TOL_34_GRADOS = 5e-6
# Cabecera de pipeline/grillas_mirova.yaml: «a 233, 1.885 y 2.787 m del yaml»
DECLARADA_TIER_A_M = {"Lascar": 233.0, "PlanchonPeteroa": 1885.0, "Tupungatito": 2787.0}
TOL_DECLARADA_M = 1.0
TOL_TIER_A_PUNTO_DEL_YAML_M = 1.5

FAMILIAS = ("VIIRS750", "MODIS", "VIIRS375")


def _cargar():
    grillas = yaml.safe_load(GRILLAS.read_text(encoding="utf-8"))["volcanes"]
    volcanes = yaml.safe_load(VOLCANES.read_text(encoding="utf-8"))["volcanoes"]
    return grillas, volcanes


def _tier_a():
    d = yaml.safe_load(NRT.read_text(encoding="utf-8"))
    return list(d["jobs"]["process"]["strategy"]["matrix"]["volcano"])


@pytest.fixture
def datos(monkeypatch):
    """Los yaml que se prueban, puestos detrás de las funciones del port (que leen el repo y guardan caché)."""
    grillas, volcanes = _cargar()
    monkeypatch.setattr(MV, "_referencias", lambda: grillas)
    tupla = [(v["name"], float(v["lat"]), float(v["lon"])) for v in volcanes]
    monkeypatch.setattr(MV, "_volcanes_yaml", lambda: tupla)
    return grillas, {v["name"]: v for v in volcanes}


def _dist_utm_x0y0(v, r):
    x, y = G.punto_utm(v["lat"], v["lon"], int(r["epsg"]))
    return x - float(r["x0"]), y - float(r["y0"])


def test_universo_45_11_y_34(datos):
    grillas, vol = datos
    tier_a = _tier_a()
    assert len(tier_a) == 11 and set(tier_a) <= set(grillas)
    assert set(grillas) == set(vol) and len(vol) == 45
    for nombre, v in vol.items():
        assert MV.volcan_por_coordenadas(v["lat"], v["lon"]) == nombre, nombre


# --------------------------------------------------------------------------------- (a) los 34: punto = volcanoes.yaml
def test_los_34_tienen_x0_y0_igual_al_utm_de_volcanoes_yaml(datos):
    grillas, vol = datos
    tier_a = set(_tier_a())
    malos = []
    n = 0
    for nombre, r in grillas.items():
        if nombre in tier_a:
            continue
        n += 1
        v = vol[nombre]
        dx, dy = _dist_utm_x0y0(v, r)
        if int(r["epsg"]) != G.zona_epsg(v["lon"]):
            malos.append((nombre, "epsg", int(r["epsg"]), G.zona_epsg(v["lon"])))
        if abs(dx) > TOL_34_EJE_M or abs(dy) > TOL_34_EJE_M:
            malos.append((nombre, "x0y0_m", round(dx, 3), round(dy, 3)))
        if (abs(float(r["centro_lat"]) - float(v["lat"])) > TOL_34_GRADOS
                or abs(float(r["centro_lon"]) - float(v["lon"])) > TOL_34_GRADOS):
            malos.append((nombre, "centro", r["centro_lat"], r["centro_lon"], v["lat"], v["lon"]))
    assert n == 34
    assert malos == [], ("grillas_mirova.yaml no sigue a volcanoes.yaml (regenerar con "
                         "experiments/_s172_sombra34/generar_grillas_34.py::entrada)", malos)


# --------------------------------------------------------------------------------- (b) los 11: distancia declarada
def test_la_cabecera_declara_las_tres_distancias():
    texto = (ROOT / "pipeline" / "grillas_mirova.yaml").read_text(encoding="utf-8")
    assert "Lascar, PlanchonPeteroa y Tupungatito es otro punto" in texto
    assert "a 233, 1.885 y 2.787 m del yaml" in texto


def test_los_11_tier_a_quedan_a_la_distancia_declarada(datos):
    grillas, vol = datos
    malos = []
    for nombre in _tier_a():
        dx, dy = _dist_utm_x0y0(vol[nombre], grillas[nombre])
        d = math.hypot(dx, dy)
        if nombre in DECLARADA_TIER_A_M:
            if abs(d - DECLARADA_TIER_A_M[nombre]) > TOL_DECLARADA_M:
                malos.append((nombre, round(d, 2), "declarada", DECLARADA_TIER_A_M[nombre]))
        elif d > TOL_TIER_A_PUNTO_DEL_YAML_M:
            malos.append((nombre, round(d, 2), "declarada <=", TOL_TIER_A_PUNTO_DEL_YAML_M))
    assert malos == [], ("un Tier A se alejó del punto de MIROVA que declara grillas_mirova.yaml (A5: el punto de "
                         "MIROVA no se cambia; si se movió volcanoes.yaml, revisar el reconocimiento y la cabecera)",
                         malos)


# --------------------------------------------------------------------------------- (c) los 45: ancla y cajas enteras
def _caja_de_la_via(familia, g, vent_lat, vent_lon, inner_km):
    """La caja que arma calcular_vrp_granulo (mirova_v750_codigo.py), con los mismos argumentos."""
    cfg = MV.FAMILIAS[familia]
    if cfg.get("roi1_half_m") is not None:
        return MV.caja_v375(g, vent_lat, vent_lon, lado_sensible=cfg["lado_sensible"], half_roi1_m=cfg["roi1_half_m"])
    celda = MV.celda_de(g, vent_lat, vent_lon)
    return MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=celda, inner_km=inner_km,
                       lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])


def _sensibles_esperadas(familia, roi):
    cfg = MV.FAMILIAS[familia]
    if familia == "VIIRS375":
        return cfg["lado_sensible"] ** 2
    if roi in ("def", "crater"):
        return cfg["lado_sensible"] ** 2
    if roi == "sens":
        return cfg["lado_anillo"] ** 2
    pytest.fail(f"ROI {roi!r} sin regla en esta guarda: agregar su tamaño esperado antes de usarla")


@pytest.mark.parametrize("familia", FAMILIAS)
def test_ancla_dentro_de_la_grilla_y_caja_entera(datos, familia):
    grillas, vol = datos
    cfg = MV.FAMILIAS[familia]
    malos = []
    for nombre, v in vol.items():
        g = MV.grilla_del_volcan(nombre, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
        assert g is not None, nombre
        vent_lat, vent_lon = get_detection_anchor(v)
        fila, col = MV.celda_de(g, vent_lat, vent_lon)
        if not (0 <= fila < g["n"] and 0 <= col < g["n"]):
            malos.append((nombre, "ancla fuera de la grilla", (fila, col), g["n"]))
            continue
        box = _caja_de_la_via(familia, g, vent_lat, vent_lon, v.get("inner_radius_km"))
        esperadas = _sensibles_esperadas(familia, g.get("roi", "def"))
        sens = box == 2
        filas_s, cols_s = sens.any(axis=1).nonzero()[0], sens.any(axis=0).nonzero()[0]
        lado = int(round(math.sqrt(esperadas)))
        entera = (int(sens.sum()) == esperadas and len(filas_s) == lado and len(cols_s) == lado)
        if not entera:
            roi = "C13" if familia == "VIIRS375" else g.get("roi", "def")
            malos.append((nombre, "caja sensible recortada", roi, int(sens.sum()), esperadas))
    assert malos == [], (f"{familia}: la vía correría con la caja sensible fuera de lugar", malos)
