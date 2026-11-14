# -*- coding: utf-8 -*-
"""S169: las seis variantes de la ROI de VIIRS 750 (una por brazo de V750-B) que `scripts/roi_v750b_a_grillas.py`
escribe en pipeline/grillas_mirova.yaml.

POR QUÉ. El día de la lectura de V750-B el cambio de la ROI tiene que ser uno solo y ya probado, y no puede tocar nada
más del YAML (las grillas están fijadas contra los GeoTIFF de MIROVA, A63). Cada prueba mide el efecto, no sólo el
texto (S126): el valor nuevo tiene que llegar a la caja que arma la vía, y en un volcán donde el cráter no está en el
centro de la grilla la caja del brazo tiene que ser distinta de la de hoy.

S173: desde #932 el YAML trae además los 34 volcanes de la sombra (todos en "def") y desde el PR de la ROI rige B4
(confirmado por Nicolás el 2026-11-03). El script sólo toca los 11 Tier A; las pruebas comparan esos 11 y exigen que
las líneas de los otros 34 queden idénticas con cualquier brazo.

S182: rige B4c (B4 con la caja del cráter en Cordón Caulle; decisión de Nicolás del 2026-11-13, «Yaml y reproceso
PCC», sobre la lectura descriptiva de experiments/_s182_pcc_crater/). Las pruebas de B4 siguen para el brazo B4.
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

BRAZOS = ("B0", "B1", "B2", "B3", "B4", "B4c", "B5")
ESPERADO = {"B0": {v: "def" for v in R.VOLCANES}, "B1": {v: "sens" for v in R.VOLCANES},
            "B2": {v: "crater" for v in R.VOLCANES}, "B3": {v: "inner" for v in R.VOLCANES},
            "B4": {v: ("sens" if v in ("PuyehueCordonCaulle", "Tupungatito") else "def") for v in R.VOLCANES},
            "B4c": {v: ("crater" if v == "PuyehueCordonCaulle" else "sens" if v == "Tupungatito" else "def")
                    for v in R.VOLCANES},
            "B5": {v: "corona" for v in R.VOLCANES}}


def _texto():
    return R.YAML.read_text(encoding="utf-8")


def _otros(volcanes):
    """Los volcanes del YAML que no son de los 11 Tier A (los 34 de la sombra, #932)."""
    return sorted(set(volcanes) - set(R.VOLCANES))


def _volcanes_yaml():
    return {v["name"]: v for v in yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}


def test_hoy_rige_b4c():
    """S182: rige B4c (B4 de V750-B con crater en Cordón Caulle, decisión de Nicolás del 2026-11-13): la variante B4c
    es el archivo tal cual, los 11 tienen los valores de B4c, la nota del comentario dice B4c y los 34 de la sombra
    siguen en def. (S173: antes regía B4.)"""
    assert R.variante(_texto(), "B4c") == _texto()
    vol = yaml.safe_load(_texto())["volcanes"]
    assert {v: vol[v]["roi_v750"] for v in R.VOLCANES} == ESPERADO["B4c"]
    assert "Puesto por la lectura de V750-B: brazo B4c (scripts/roi_v750b_a_grillas.py)." in _texto()
    otros = _otros(vol)
    assert len(otros) == 34 and all(vol[v]["roi_v750"] == "def" for v in otros)


@pytest.mark.parametrize("brazo", BRAZOS)
def test_los_34_de_la_sombra_no_cambian(brazo):
    """S173: con cualquier brazo, la línea de cada uno de los 34 volcanes que no son Tier A queda byte a byte igual
    (el script no los conoce: la ROI de V750-B se midió sólo en los 11)."""
    viejo, nuevo = _texto().splitlines(), R.variante(_texto(), brazo).splitlines()
    otros = _otros(yaml.safe_load(_texto())["volcanes"])
    lineas = lambda t: {v: [x for x in t if x.startswith(f"  {v}:")] for v in otros}
    a, b = lineas(viejo), lineas(nuevo)
    assert all(len(a[v]) == 1 for v in otros)
    assert a == b


@pytest.mark.parametrize("brazo", BRAZOS)
def test_variante_cambia_solo_roi_v750(brazo):
    viejo = yaml.safe_load(_texto())["volcanes"]
    nuevo = yaml.safe_load(R.variante(_texto(), brazo))["volcanes"]
    assert set(nuevo) == set(viejo) and set(R.VOLCANES) <= set(viejo)
    for v in _otros(viejo):
        assert nuevo[v] == viejo[v], (brazo, v)
    for v in R.VOLCANES:
        assert nuevo[v]["roi_v750"] == ESPERADO[brazo][v], (brazo, v)
        assert nuevo[v]["roi_v750"] in MV.TIPOS_ROI, (brazo, v)
        assert {k: x for k, x in nuevo[v].items() if k != "roi_v750"} == \
               {k: x for k, x in viejo[v].items() if k != "roi_v750"}, (brazo, v)


@pytest.mark.parametrize("brazo", BRAZOS)
def test_variante_no_toca_otras_lineas(brazo):
    """Fuera de las 11 líneas de volcán Tier A, sólo pueden cambiar los dos comentarios que dicen qué ROI rige. S173:
    como hoy rige B4, el resultado se mira en el texto nuevo (comentario y nota del brazo puesto), no en el diff."""
    viejo, nuevo = _texto().splitlines(), R.variante(_texto(), brazo).splitlines()
    assert len(viejo) == len(nuevo)
    distintas = [(a, b) for a, b in zip(viejo, nuevo) if a != b]
    for a, b in distintas:
        assert any(a.startswith(f"  {v}:") for v in R.VOLCANES) or a.startswith("# roi_v750:") \
            or a.startswith("# caja_roi()."), (a, b)
    texto = "\n".join(nuevo)
    assert texto.count('Hasta la lectura de V750-B, "def" en todos') == 1
    assert texto.count(f"brazo {brazo} (scripts/roi_v750b_a_grillas.py).") == 1


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


def _copia_del_yaml(tmp_path, monkeypatch):
    """main() escribe en R.YAML; las pruebas lo apuntan a una copia del archivo de hoy."""
    ruta = tmp_path / "grillas_mirova.yaml"
    ruta.write_text(_texto(), encoding="utf-8")
    monkeypatch.setattr(R, "YAML", ruta)
    return ruta


def _roi_del_archivo(ruta):
    """roi_v750 de los 11 Tier A (los 34 de la sombra los vigila test_los_34_de_la_sombra_no_cambian)."""
    vol = yaml.safe_load(ruta.read_text(encoding="utf-8"))["volcanes"]
    return {v: vol[v]["roi_v750"] for v in R.VOLCANES}


@pytest.mark.parametrize("brazo", BRAZOS)
def test_main_escribe_el_brazo_pedido(brazo, tmp_path, monkeypatch):
    """P1-13 del verificador S169: el paso que escribe la ROI el día de la lectura. --escribir deja en el archivo
    exactamente la variante del brazo pedido (no la vieja, no la de otro brazo)."""
    ruta = _copia_del_yaml(tmp_path, monkeypatch)
    assert R.main(["--brazo", brazo, "--escribir"]) == 0
    assert ruta.read_text(encoding="utf-8") == R.variante(_texto(), brazo)
    assert _roi_del_archivo(ruta) == ESPERADO[brazo]


def test_main_sin_escribir_no_toca_el_archivo_y_muestra_el_cambio(tmp_path, monkeypatch, capsys):
    ruta = _copia_del_yaml(tmp_path, monkeypatch)
    # S182: rige B4c, así que el diff se mira pidiendo B0 (Cordón Caulle vuelve de crater y Tupungatito de sens a def)
    assert R.main(["--brazo", "B0"]) == 0
    assert ruta.read_text(encoding="utf-8") == _texto()
    salida = capsys.readouterr().out
    assert salida.count("roi_v750: sens}") == 1 and salida.count("roi_v750: crater}") == 1
    assert "+  Tupungatito:" in salida and "+  PuyehueCordonCaulle:" in salida


def test_main_rechaza_un_brazo_que_no_existe(tmp_path, monkeypatch):
    ruta = _copia_del_yaml(tmp_path, monkeypatch)
    with pytest.raises(SystemExit) as e:
        R.main(["--brazo", "B6", "--escribir"])
    assert e.value.code == 2
    assert ruta.read_text(encoding="utf-8") == _texto()


@pytest.mark.parametrize("primero,despues", [("B1", "B4"), ("B2", "B0"), ("B4", "B4"), ("B4", "B4c")])
def test_aplicar_dos_veces_deja_solo_el_segundo(primero, despues, tmp_path, monkeypatch):
    """VF1-02 del verificador S169: probar un brazo y después aplicar el elegido en el mismo árbol deja valores Y
    comentario del segundo; volver a B0 deja def en todos con la nota de B0."""
    ruta = _copia_del_yaml(tmp_path, monkeypatch)
    R.main(["--brazo", primero, "--escribir"])
    R.main(["--brazo", despues, "--escribir"])
    texto = ruta.read_text(encoding="utf-8")
    assert _roi_del_archivo(ruta) == ESPERADO[despues]
    assert texto.count("Puesto por la lectura de V750-B: brazo") == 1
    assert f"brazo {despues} (scripts/roi_v750b_a_grillas.py)." in texto
    assert texto.count('Hasta la lectura de V750-B, "def" en todos') == 1 and 'Hoy "def" en todos' not in texto


def test_brazo_desconocido_y_archivo_ajeno_se_niegan():
    with pytest.raises(ValueError):
        R.roi_por_volcan("B6")
    with pytest.raises(ValueError):
        R.variante(_texto().replace("  Lascar:", "  LascarX:"), "B1")


def test_el_cambio_se_ve_en_la_caja_de_cordon_caulle(tmp_path, monkeypatch):
    """S182, control de efecto (S126): en Cordón Caulle el cráter cae en la celda (23, 30), en el borde norte del anillo
    21 x 21 (filas 23 a 43). La caja de B4 (sens) deja fuera la fila 22, al norte de la fisura, y pone el umbral
    sensible en todo el flanco sur del Puyehue; la de B4c (crater) cubre la fila 22 y deja el sur conservador. Es lo
    que separa los 10,1 MW de la vía del 2026-10-21 05:48 NOAA-21 de los 0,36 MW de MIROVA
    (experiments/_s182_pcc_crater/)."""
    vy = _volcanes_yaml()["PuyehueCordonCaulle"]
    cajas = {}
    for brazo in ("B4", "B4c"):
        ruta = tmp_path / f"{brazo}.yaml"
        ruta.write_text(R.variante(_texto(), brazo), encoding="utf-8")
        monkeypatch.setattr(MV, "_GRILLAS_YAML", ruta)
        MV._referencias.cache_clear()
        g = MV.grilla_del_volcan("PuyehueCordonCaulle")
        celda = MV.celda_de(g, vy["vent_lat"], vy["vent_lon"]) if "vent_lat" in vy else MV.celda_de(g, vy["lat"], vy["lon"])
        cfg = MV.FAMILIAS["VIIRS750"]
        cajas[brazo] = MV.caja_roi(g["roi"], n=g["n"], celda_crater=celda, inner_km=float(vy["inner_radius_km"]),
                                   lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
    MV._referencias.cache_clear()
    assert celda == (23, 30)
    b4, b4c = cajas["B4"], cajas["B4c"]
    assert b4[22, 30] == 0 and b4c[22, 30] == 2          # la fila al norte de la fisura entra con umbral sensible
    assert b4[37, 26] == 2 and b4c[37, 26] == 1          # el flanco sur (píxeles del 21-oct) pasa a conservador
    assert (b4c == 2).sum() == 49 and (b4 == 2).sum() == 21 * 21
