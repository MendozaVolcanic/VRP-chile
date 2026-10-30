# -*- coding: utf-8 -*-
"""S169: las seis variantes de la ROI de VIIRS 750 (una por brazo de V750-B) que `scripts/roi_v750b_a_grillas.py`
escribe en pipeline/grillas_mirova.yaml.

POR QUÉ. El día de la lectura de V750-B el cambio de la ROI tiene que ser uno solo y ya probado, y no puede tocar nada
más del YAML (las grillas están fijadas contra los GeoTIFF de MIROVA, A63). Cada prueba mide el efecto, no sólo el
texto (S126): el valor nuevo tiene que llegar a la caja que arma la vía, y en un volcán donde el cráter no está en el
centro de la grilla la caja del brazo tiene que ser distinta de la de hoy.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline import mirova_v750_codigo as MV  # noqa: E402

_spec = importlib.util.spec_from_file_location("roi_v750b_a_grillas", REPO / "scripts" / "roi_v750b_a_grillas.py")
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)

BRAZOS = ("B0", "B1", "B2", "B3", "B4", "B5")
ESPERADO = {"B0": {v: "def" for v in R.VOLCANES}, "B1": {v: "sens" for v in R.VOLCANES},
            "B2": {v: "crater" for v in R.VOLCANES}, "B3": {v: "inner" for v in R.VOLCANES},
            "B4": {v: ("sens" if v in ("PuyehueCordonCaulle", "Tupungatito") else "def") for v in R.VOLCANES},
            "B5": {v: "corona" for v in R.VOLCANES}}


def _texto():
    return R.YAML.read_text(encoding="utf-8")


def _volcanes_yaml():
    return {v["name"]: v for v in yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}


def test_hoy_el_yaml_es_b0():
    """La rama no cambia el YAML: hoy todos están en def, y la variante B0 es el archivo tal cual."""
    assert R.variante(_texto(), "B0") == _texto()
    assert {v: r["roi_v750"] for v, r in yaml.safe_load(_texto())["volcanes"].items()} == ESPERADO["B0"]


@pytest.mark.parametrize("brazo", BRAZOS)
def test_variante_cambia_solo_roi_v750(brazo):
    viejo = yaml.safe_load(_texto())["volcanes"]
    nuevo = yaml.safe_load(R.variante(_texto(), brazo))["volcanes"]
    assert set(nuevo) == set(viejo) == set(R.VOLCANES)
    for v in R.VOLCANES:
        assert nuevo[v]["roi_v750"] == ESPERADO[brazo][v], (brazo, v)
        assert nuevo[v]["roi_v750"] in MV.TIPOS_ROI, (brazo, v)
        assert {k: x for k, x in nuevo[v].items() if k != "roi_v750"} == \
               {k: x for k, x in viejo[v].items() if k != "roi_v750"}, (brazo, v)


@pytest.mark.parametrize("brazo", BRAZOS)
def test_variante_no_toca_otras_lineas(brazo):
    """Fuera de las 11 líneas de volcán, sólo pueden cambiar los dos comentarios que dicen qué ROI rige."""
    viejo, nuevo = _texto().splitlines(), R.variante(_texto(), brazo).splitlines()
    assert len(viejo) == len(nuevo)
    distintas = [(a, b) for a, b in zip(viejo, nuevo) if a != b]
    for a, b in distintas:
        assert a.startswith("  ") and "roi_v750:" in a or a.startswith("# roi_v750:") or a == "# caja_roi().", (a, b)
    if brazo != "B0":
        assert any('Hasta la lectura de V750-B, "def" en todos' in b for _a, b in distintas)
        assert any(f"brazo {brazo}" in b for _a, b in distintas)


@pytest.mark.parametrize("brazo", BRAZOS)
def test_el_valor_llega_a_la_caja_de_la_via(brazo, tmp_path, monkeypatch):
    """grilla_del_volcan lee la ROI de la variante y caja_roi arma una caja válida con el cráter y el radio del
    volcán (los mismos argumentos que pasa mirova_v750_codigo para VIIRS 750)."""
    ruta = tmp_path / "grillas_mirova.yaml"
    ruta.write_text(R.variante(_texto(), brazo), encoding="utf-8")
    monkeypatch.setattr(MV, "_GRILLAS_YAML", ruta)
    MV._referencias.cache_clear()
    vy = _volcanes_yaml()
    try:
        for v in R.VOLCANES:
            g = MV.grilla_del_volcan(v)
            assert g["roi"] == ESPERADO[brazo][v], (brazo, v)
            cfg = MV.FAMILIAS["VIIRS750"]
            celda = MV.celda_de(g, vy[v]["vent_lat"], vy[v]["vent_lon"]) if "vent_lat" in vy[v] else \
                MV.celda_de(g, vy[v]["lat"], vy[v]["lon"])
            box = MV.caja_roi(g["roi"], n=g["n"], celda_crater=celda, inner_km=float(vy[v]["inner_radius_km"]),
                              lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
            assert box.shape == (g["n"], g["n"]) and (box == 2).any(), (brazo, v)
    finally:
        MV._referencias.cache_clear()


def test_el_cambio_se_ve_en_la_caja_de_tupungatito(tmp_path, monkeypatch):
    """Control de efecto: en Tupungatito el cráter está a ~4 km del centro de la grilla, así que la caja de B2 (en el
    cráter) y la de B4 (sensible entera) no pueden ser la de hoy (def)."""
    vy = _volcanes_yaml()["Tupungatito"]
    cajas = {}
    for brazo in ("B0", "B2", "B4"):
        ruta = tmp_path / f"{brazo}.yaml"
        ruta.write_text(R.variante(_texto(), brazo), encoding="utf-8")
        monkeypatch.setattr(MV, "_GRILLAS_YAML", ruta)
        MV._referencias.cache_clear()
        g = MV.grilla_del_volcan("Tupungatito")
        cajas[brazo] = MV.caja_roi(g["roi"], n=g["n"], celda_crater=MV.celda_de(g, vy["vent_lat"], vy["vent_lon"]),
                                   inner_km=float(vy["inner_radius_km"]), paso_m=g["paso"])
    MV._referencias.cache_clear()
    assert not np.array_equal(cajas["B2"], cajas["B0"])
    assert not np.array_equal(cajas["B4"], cajas["B0"])
    assert (cajas["B4"] == 2).sum() > (cajas["B0"] == 2).sum()


def test_brazo_desconocido_y_archivo_ajeno_se_niegan():
    with pytest.raises(ValueError):
        R.roi_por_volcan("B6")
    with pytest.raises(ValueError):
        R.variante(_texto().replace("  Lascar:", "  LascarX:"), "B1")
