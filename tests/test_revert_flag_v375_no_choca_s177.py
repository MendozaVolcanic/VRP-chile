# -*- coding: utf-8 -*-
"""S177, PR B1: revertir el merge de B1 (el que enciende la vía «código MIROVA» de VIIRS 375) no choca con B2 (la de
VIIRS 750), con el encendido de MODIS (#934) ni con otro PR que cambie una clave cercana de los perfiles.

POR QUÉ. La regla de reversión de VIIRS (experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md §4.3, SIN
SELLO) manda revertir el mismo día con `git revert -m 1` del merge del PR de ESE sensor si producción calla una alerta
protegida que la guardia K publica, y nunca revertir el otro. git trata como conflicto dos cambios en líneas contiguas
(hallazgo 208 de S173): si el bloque de B1 quedara pegado al de B2 o al de MODIS, la reversión de emergencia pasaría a
necesitar una resolución a mano. Por eso cada bloque de B2 y de B1 va en un lugar propio de cada perfil, con al menos
una línea existente entre ellos y entre ellos y el bloque de MODIS.

Cómo se prueba. Con `git merge-file` (el merge de tres vías que usan `git merge` y `git revert`) sobre el texto real de
cada perfil que B1 toca: se arma el estado con los dos PR (si B2 aún no está en este árbol, se pone un bloque de B2
sintético en el lugar donde B2 lo pone), se mergea en los dos órdenes y se revierte cada uno. Lleva controles
positivos: un cambio en la misma línea del flag y un bloque puesto en el lugar del de B2 sí tienen que chocar.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PERFILES = ROOT / "pipeline" / "profiles"

# Cada PR marca la primera línea de cada bloque suyo con su etiqueta; el bloque termina en la línea de su flag.
ESTE = {"etiqueta": "S177 B1:", "clave": "enable_v375_codigo_mirova"}
OTRO = {"etiqueta": "S177 B2:", "clave": "enable_v750_codigo_mirova"}
# archivo -> (línea tras la cual B1 pone su bloque, línea tras la cual B2 pone el suyo, valor del flag en ese archivo)
LUGARES = {
    "mirova_equivalent": ("  test1_intermediate_bg_ring_km: [1.5, 3.0]", "  n_sigma_vent: 2.0", "true"),
    "experimental": ("thresholds:", "  enable_modis_codigo_mirova: false", "false"),
    "experimental_ndc_focus": ("thresholds:", "  enable_modis_codigo_mirova: false", "false"),
    "_s146_ab_control": ("thresholds:", "  enable_modis_codigo_mirova: false", "false"),
    "guardia_k_modis": ("thresholds:", "  enable_modis_codigo_mirova: false", "false"),
}
INICIO_MODIS = "  # S172, MOD-D ENCENDIDO"
FLAG_MODIS = "  enable_modis_codigo_mirova: true\n"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="sin git en el PATH")


def _texto(nombre):
    return (PERFILES / f"{nombre}.yaml").read_bytes().decode("utf-8").replace("\r\n", "\n")


def _spans(texto, pr):
    """(inicio, fin) de cada bloque del PR: desde la línea con su etiqueta hasta la línea de su flag, inclusive."""
    out = []
    for m in re.finditer(r"^.*" + re.escape(pr["etiqueta"]) + r".*\n", texto, re.MULTILINE):
        f = re.compile(r"^  " + re.escape(pr["clave"]) + r":.*\n", re.MULTILINE).search(texto, m.start())
        assert f is not None, pr
        out.append((m.start(), f.end()))
    return out


def _quitar(texto, pr):
    for ini, fin in reversed(_spans(texto, pr)):
        texto = texto[:ini] + texto[fin:]
    return texto


def _poner_tras(texto, ancla, bloque):
    linea = ancla + "\n"
    assert texto.count(linea) == 1, ancla
    i = texto.index(linea) + len(linea)
    return texto[:i] + bloque + texto[i:]


def _estados(nombre):
    """(ambos, solo_b1, solo_b2, ninguno) del perfil. Si B2 no está en el árbol, se sintetiza en su lugar."""
    t = _texto(nombre)
    _, ancla_b2, valor = LUGARES[nombre]
    if not _spans(t, OTRO):
        sintetico = f"  # {OTRO['etiqueta']} bloque sintético del otro PR, en su lugar\n  {OTRO['clave']}: {valor}\n"
        t = _poner_tras(t, ancla_b2, sintetico)
    ambos = t
    solo_b1, solo_b2 = _quitar(ambos, OTRO), _quitar(ambos, ESTE)
    return ambos, solo_b1, solo_b2, _quitar(solo_b1, ESTE)


def _merge3(tmp_path, ours, base, theirs):
    """git merge-file -p ours base theirs: (n_conflictos, texto)."""
    archivos = []
    for nombre, texto in (("ours", ours), ("base", base), ("theirs", theirs)):
        f = tmp_path / f"{nombre}.yaml"
        f.write_bytes(texto.encode("utf-8"))
        archivos.append(str(f))
    r = subprocess.run(["git", "merge-file", "-p", *archivos], capture_output=True)
    assert r.returncode >= 0, r.stderr
    return r.returncode, r.stdout.decode("utf-8")


@pytest.mark.parametrize("nombre", sorted(LUGARES))
def test_el_bloque_de_b1_esta_y_va_tras_su_ancla(nombre):
    t = _texto(nombre)
    spans = _spans(t, ESTE)
    assert len(spans) == 1, nombre
    ancla_b1, _, valor = LUGARES[nombre]
    assert t[:spans[0][0]].endswith(ancla_b1 + "\n"), nombre
    bloque = t[spans[0][0]:spans[0][1]]
    assert bloque.endswith(f"  {ESTE['clave']}: {valor}\n"), bloque
    # y en yaml, dentro de `thresholds:` (donde lo lee pipeline/profile.py, A89)
    assert yaml.safe_load(t)["thresholds"][ESTE["clave"]] is (valor == "true")


@pytest.mark.parametrize("nombre", sorted(LUGARES))
def test_los_dos_ordenes_de_merge_no_chocan(tmp_path, nombre):
    ambos, solo_b1, solo_b2, ninguno = _estados(nombre)
    assert _merge3(tmp_path, solo_b2, ninguno, solo_b1) == (0, ambos)   # B2 primero, entra B1
    assert _merge3(tmp_path, solo_b1, ninguno, solo_b2) == (0, ambos)   # B1 primero, entra B2


@pytest.mark.parametrize("nombre", sorted(LUGARES))
def test_revertir_b1_con_b2_ya_en_main_no_choca(tmp_path, nombre):
    ambos, solo_b1, solo_b2, ninguno = _estados(nombre)
    # B1 entró antes que B2: base del revert = main tras B1, theirs = main antes de B1
    assert _merge3(tmp_path, ambos, solo_b1, ninguno) == (0, solo_b2)
    # B1 entró después de B2
    assert _merge3(tmp_path, ambos, ambos, solo_b2) == (0, solo_b2)


@pytest.mark.parametrize("nombre", sorted(LUGARES))
def test_revertir_b2_con_b1_ya_en_main_no_se_lleva_el_bloque_de_b1(tmp_path, nombre):
    ambos, solo_b1, solo_b2, ninguno = _estados(nombre)
    assert _merge3(tmp_path, ambos, solo_b2, ninguno) == (0, solo_b1)


def test_revertir_modis_con_b2_y_b1_en_main_no_choca(tmp_path):
    ambos, _, _, ninguno = _estados("mirova_equivalent")
    ini = ninguno.index(INICIO_MODIS)
    fin = ninguno.index(FLAG_MODIS) + len(FLAG_MODIS)
    ninguno_sin_modis = ninguno[:ini] + ninguno[fin:]
    a, b = ambos.index(INICIO_MODIS), ambos.index(FLAG_MODIS) + len(FLAG_MODIS)
    assert _merge3(tmp_path, ambos, ninguno, ninguno_sin_modis) == (0, ambos[:a] + ambos[b:])


@pytest.mark.parametrize("clave", ["enable_modis_geo_mxd03", "enable_modis_crater_sin_dato",
                                   "enable_modis_dist_desde_crater"])
def test_revertir_b1_no_choca_con_otro_pr_que_cambie_mxd03(tmp_path, clave):
    ambos, solo_b1, solo_b2, _ = _estados("mirova_equivalent")
    patron = re.compile(r"^(  " + re.escape(clave) + r":\s*)false\b", re.MULTILINE)
    otro_pr = patron.subn(r"\1true", ambos)
    assert otro_pr[1] == 1, clave
    n, resultado = _merge3(tmp_path, otro_pr[0], ambos, solo_b2)
    assert n == 0, resultado
    t = yaml.safe_load(resultado)["thresholds"]
    assert ESTE["clave"] not in t and t[clave] is True and t[OTRO["clave"]] is True


def test_control_un_cambio_en_la_linea_del_flag_si_choca(tmp_path):
    """Si otro PR toca la misma línea del flag, el revert tiene que chocar: sin esto, un merge-file que nunca reporta
    conflictos daría verde a todo."""
    ambos, _, solo_b2, _ = _estados("mirova_equivalent")
    linea = f"  {ESTE['clave']}: true\n"
    otro = ambos.replace(linea, f"  {ESTE['clave']}: true   # comentario de otro PR\n")
    assert otro != ambos
    n, _ = _merge3(tmp_path, otro, ambos, solo_b2)
    assert n > 0


@pytest.mark.parametrize("nombre", sorted(LUGARES))
def test_control_un_bloque_en_el_lugar_del_de_b2_si_choca(tmp_path, nombre):
    """Control del defecto 208: con el bloque de B1 en el lugar del de B2, el segundo merge choca. Es la prueba de que
    el instrumento ve el problema que la ubicación evita."""
    ambos, solo_b1, solo_b2, ninguno = _estados(nombre)
    b2 = _spans(solo_b2, OTRO)[0]
    b1 = solo_b1[_spans(solo_b1, ESTE)[0][0]:_spans(solo_b1, ESTE)[0][1]]
    pegado_solo_b1 = ninguno[:b2[0]] + b1 + ninguno[b2[0]:]
    n, _ = _merge3(tmp_path, solo_b2, ninguno, pegado_solo_b1)
    assert n > 0
