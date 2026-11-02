# -*- coding: utf-8 -*-
"""S173, hallazgo 208: el revert del PR B (el que enciende la vía «código MIROVA» de MODIS) no choca con otro PR que
cambie una clave cercana del perfil de producción.

POR QUÉ. La regla de reversión de MODIS (experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §4.3) manda
revertir el mismo día con `git revert -m 1` del merge de B si producción calla una alerta protegida que la guardia K
publica. git trata como conflicto dos cambios en líneas contiguas: con el bloque de B pegado a las tres claves de MxD03,
un PR que encendiera cualquiera de ellas hacía chocar ese revert (V2 sobre 208 lo provocó y vio el conflicto), y la
reversión de emergencia pasaba a necesitar una resolución a mano. Desde S173 el bloque va al inicio de `thresholds:`,
separado de toda clave por líneas que B no toca. Esta prueba lo comprueba con `git merge-file` (el mismo merge de tres
vías que usa `git revert`) sobre el texto real del perfil, y lleva controles positivos para poder fallar.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PERFIL = ROOT / "pipeline" / "profiles" / "mirova_equivalent.yaml"
INICIO_BLOQUE = "  # S172, MOD-D ENCENDIDO"
LINEA_FLAG = "  enable_modis_codigo_mirova: true\n"
CLAVES_MXD03 = ("enable_modis_geo_mxd03", "enable_modis_crater_sin_dato", "enable_modis_dist_desde_crater")

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="sin git en el PATH")


def _con_b():
    return PERFIL.read_bytes().decode("utf-8").replace("\r\n", "\n")


def _sin_b(texto):
    """El perfil tal como queda tras el revert de B: sin el bloque de B (comentario y flag)."""
    ini = texto.index(INICIO_BLOQUE)
    fin = texto.index(LINEA_FLAG) + len(LINEA_FLAG)
    assert ini < fin
    return texto[:ini] + texto[fin:]


def _cambiar_clave(texto, clave):
    """Lo que haría otro PR: encender una clave que hoy está en false."""
    patron = re.compile(r"^(  " + re.escape(clave) + r":\s*)false\b", re.MULTILINE)
    nuevo, n = patron.subn(r"\1true", texto)
    assert n == 1, clave
    return nuevo


def _merge3(tmp_path, ours, base, theirs):
    """git merge-file -p ours base theirs: devuelve (n_conflictos, texto). Es el merge que hace `git revert`, con
    base = el perfil con B, theirs = el perfil sin B (el revert) y ours = main con el cambio del otro PR."""
    archivos = []
    for nombre, texto in (("ours", ours), ("base", base), ("theirs", theirs)):
        f = tmp_path / f"{nombre}.yaml"
        f.write_bytes(texto.encode("utf-8"))
        archivos.append(str(f))
    r = subprocess.run(["git", "merge-file", "-p", *archivos], capture_output=True)
    assert r.returncode >= 0, r.stderr
    return r.returncode, r.stdout.decode("utf-8")


def test_el_bloque_esta_en_thresholds_y_el_flag_se_lee():
    datos = yaml.safe_load(_con_b())
    assert datos["thresholds"]["enable_modis_codigo_mirova"] is True
    assert "enable_modis_codigo_mirova" not in yaml.safe_load(_sin_b(_con_b()))["thresholds"]


def test_el_bloque_no_toca_lineas_de_clave():
    """La línea anterior y la siguiente al bloque de B no son claves que otro PR vaya a cambiar."""
    lineas = _con_b().split("\n")
    i_ini = next(i for i, ln in enumerate(lineas) if ln.startswith(INICIO_BLOQUE))
    i_fin = lineas.index(LINEA_FLAG.rstrip("\n"))
    antes, despues = lineas[i_ini - 1], lineas[i_fin + 1]
    assert antes == "thresholds:"
    assert despues.lstrip().startswith("#"), despues


@pytest.mark.parametrize("clave", CLAVES_MXD03)
def test_revert_de_b_no_choca_con_un_cambio_en_mxd03(tmp_path, clave):
    con_b = _con_b()
    sin_b = _sin_b(con_b)
    main_con_otro_pr = _cambiar_clave(con_b, clave)
    n, resultado = _merge3(tmp_path, main_con_otro_pr, con_b, sin_b)
    assert n == 0, resultado
    # el resultado es: sin el flag de B y con el cambio del otro PR
    assert resultado == _cambiar_clave(sin_b, clave)
    t = yaml.safe_load(resultado)["thresholds"]
    assert "enable_modis_codigo_mirova" not in t and t[clave] is True


def test_control_un_cambio_en_la_linea_del_flag_si_choca(tmp_path):
    """Control positivo: si otro PR toca la misma línea del flag, el merge tiene que chocar. Sin esto, un merge-file
    que nunca reporta conflictos daría verde a todo."""
    con_b = _con_b()
    otro = con_b.replace(LINEA_FLAG, "  enable_modis_codigo_mirova: true   # comentario de otro PR\n")
    assert otro != con_b
    n, _ = _merge3(tmp_path, otro, con_b, _sin_b(con_b))
    assert n > 0


def test_control_la_ubicacion_vieja_si_chocaba(tmp_path):
    """Control positivo del defecto 208: con el bloque pegado a las claves de MxD03 (la ubicación de la ronda 2), un
    cambio en la última de ellas choca con el revert. Es la prueba de que el instrumento ve el problema que arregla."""
    con_b = _con_b()
    sin_b = _sin_b(con_b)
    bloque = con_b[con_b.index(INICIO_BLOQUE):con_b.index(LINEA_FLAG) + len(LINEA_FLAG)]
    ultima = re.search(r"^  enable_modis_dist_desde_crater:.*\n", sin_b, re.MULTILINE)
    viejo_con_b = sin_b[:ultima.end()] + bloque + sin_b[ultima.end():]
    n, _ = _merge3(tmp_path, _cambiar_clave(viejo_con_b, "enable_modis_dist_desde_crater"), viejo_con_b, sin_b)
    assert n > 0
