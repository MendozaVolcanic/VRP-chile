"""S190: fija los centros corregidos con la ficha RNVV de SERNAGEOMIN (experiments/_s190_coordenadas/auditar_centros.py).

POR QUÉ. El centro decide dónde se apoya la grilla UTM de MIROVA (y su caja ROI) y desde dónde se mide la distancia
cumbre/lejos. Siete de los 34 tenían el centro a más de 1 km del de la ficha RNVV, con el GVP de acuerdo con la RNVV
(Mentolat 3,3 km al norte del volcán, MacaCay en el mar al oeste de Macá). Esta prueba cuida que las tres vistas
(volcanoes.yaml, grillas_mirova.yaml y el tablero) lleven el centro nuevo y que la grilla salga de él con la regla de
S172, para que un reemplazo desde otra fuente no los devuelva en silencio (A63).
"""
import math
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "experiments" / "_s172_sombra34"))
from generar_grillas_34 import entrada  # noqa: E402

# nombre: (lat, lon) de la ficha RNVV (WEBRNVV/fichas_nuevas_json/_lista.json; MacaCay = Volcán Macá)
CENTROS_S190 = {
    "Callaqui": (-37.93, -71.45),
    "AntillancaCasablanca": (-40.78, -72.16),
    "Michinmahuida": (-42.80, -72.45),
    "CorcovadoYanteles": (-43.19, -72.79),
    "Mentolat": (-44.70, -73.08),
    "MacaCay": (-45.10501, -73.169326),
    "SanPedro": (-21.89, -68.39),
}
# centros viejos: ninguno debe volver
VIEJOS = {
    "Callaqui": (-37.92, -71.45), "AntillancaCasablanca": (-40.77, -72.15), "Michinmahuida": (-42.79, -72.44),
    "CorcovadoYanteles": (-43.183, -72.80), "Mentolat": (-44.67, -73.08), "MacaCay": (-45.10, -73.20),
    "SanPedro": (-21.88, -68.40),
}
GVP_ID = {"MacaCay": 358056, "Tolhuaca": 357093, "AntillancaCasablanca": 357153}


def _volcanes():
    return {v["name"]: v for v in yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}


def _grillas():
    return yaml.safe_load((REPO / "pipeline" / "grillas_mirova.yaml").read_text(encoding="utf-8"))["volcanes"]


def _km(a, b):
    r = math.pi / 180
    x = (math.sin((b[0] - a[0]) * r / 2) ** 2
         + math.cos(a[0] * r) * math.cos(b[0] * r) * math.sin((b[1] - a[1]) * r / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(x))


@pytest.mark.parametrize("nombre", sorted(CENTROS_S190))
def test_yaml_lleva_el_centro_rnvv(nombre):
    v = _volcanes()[nombre]
    assert (float(v["lat"]), float(v["lon"])) == pytest.approx(CENTROS_S190[nombre], abs=1e-6)


@pytest.mark.parametrize("nombre", sorted(CENTROS_S190))
def test_el_centro_viejo_quedo_a_mas_de_1_km(nombre):
    """Control de que la prueba de arriba mira algo: el centro viejo está a más de 1 km del nuevo."""
    assert _km(VIEJOS[nombre], CENTROS_S190[nombre]) > 1.0


@pytest.mark.parametrize("nombre", sorted(CENTROS_S190))
def test_grilla_sale_del_centro_nuevo(nombre):
    g = _grillas()[nombre]
    e = entrada(_volcanes()[nombre])
    assert int(g["epsg"]) == e["epsg"]
    assert float(g["x0"]) == pytest.approx(e["x0"], abs=0.11)
    assert float(g["y0"]) == pytest.approx(e["y0"], abs=0.11)
    assert (float(g["centro_lat"]), float(g["centro_lon"])) == pytest.approx(CENTROS_S190[nombre], abs=1e-5)


@pytest.mark.parametrize("nombre", sorted(CENTROS_S190))
def test_tablero_lleva_el_centro_nuevo(nombre):
    h = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'\{ name: "%s",[^\n]*?lat: (-[\d.]+), lon: (-[\d.]+),' % nombre, h)
    assert m, nombre
    assert (float(m.group(1)), float(m.group(2))) == pytest.approx(CENTROS_S190[nombre], abs=1e-6)


@pytest.mark.parametrize("nombre", sorted(GVP_ID))
def test_gvp_id_corregido(nombre):
    assert int(_volcanes()[nombre]["gvp_id"]) == GVP_ID[nombre]
