# -*- coding: utf-8 -*-
"""S145: el fondo por vecinos (D25) en VIIRS 750 (M-band).

POR QUE. El helper de vrp_regimes ya es agnostico de sensor; lo que este archivo fija es que en
M-band se use M13_LAMBDA (4,05 um) y no I04, que el respaldo del pixel sin vecinos sea el fondo de
hoy, y que el flag propio de V750 no se confunda con el de I-band (A92).

Plan: docs/superpowers/plans/2026-09-20-d25-fondo-vecinos-viirs750.md
"""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# M13_LAMBDA NO vive en pipeline.constants: esta definido en el propio process_viirs_mod,
# igual que I04_LAMBDA vive en process_viirs. Importarlo de constants da ImportError.
from pipeline.process_viirs_mod import M13_LAMBDA, vrp_bg_neighbor_mean_v750  # noqa: E402
from pipeline.vrp_regimes import neighbor_mean_radiance_background  # noqa: E402


def test_el_envoltorio_de_m_band_usa_la_longitud_de_onda_de_m13():
    """Si usara I04 (3,74 um) el fondo saldria distinto: Planck no es plano entre 3,74 y 4,05 um."""
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 400.0
    alerta = np.zeros((5, 5), dtype=bool)
    alerta[2, 2] = True
    l_bg, n_sin = vrp_bg_neighbor_mean_v750(bt, alerta, [2], [2], 9.99, max_half_px=1)
    esperado, _ = neighbor_mean_radiance_background(
        bt, alerta, [2], [2], M13_LAMBDA, max_half_px=1)
    assert n_sin == 0
    np.testing.assert_allclose(l_bg, esperado)


def test_sin_vecinos_no_alertados_cae_al_fondo_de_hoy_y_lo_cuenta():
    """Un unico pixel de una escena 1x1: no hay a quien promediar, manda el respaldo."""
    bt = np.full((1, 1), 300.0)
    alerta = np.ones((1, 1), dtype=bool)
    l_bg, n_sin = vrp_bg_neighbor_mean_v750(bt, alerta, [0], [0], 0.1234, max_half_px=3)
    assert n_sin == 1
    np.testing.assert_allclose(l_bg, [0.1234])


def test_el_flag_de_v750_existe_y_esta_apagado_en_el_perfil_operacional():
    """A45: el default operacional es OFF; encenderlo es una decision aparte, con A/B."""
    import pipeline.profile as p
    assert hasattr(p, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750")
    assert p.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 is False


def test_los_dos_flags_son_independientes_y_no_se_confunden_por_subcadena():
    """A92: ningun nombre es subcadena del otro, y el YAML declara los dos por separado."""
    import pipeline.profile as p
    i, m = "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375", "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750"
    assert i not in m and m not in i
    yaml_txt = (ROOT / "pipeline" / "profiles" / "mirova_equivalent.yaml").read_text(encoding="utf-8")
    for clave in ("enable_vrp_bg_neighbor_mean_viirs375", "enable_vrp_bg_neighbor_mean_viirs750"):
        assert re.search(r"^\s*" + clave + r"\s*:", yaml_txt, re.M), clave
    assert getattr(p, i) is False and getattr(p, m) is False


def _fuente_v750():
    return (ROOT / "pipeline" / "process_viirs_mod.py").read_text(encoding="utf-8")


def test_los_cuatro_usos_del_flag_estan_donde_corresponde():
    """Los 3 bloques que restan fondo en M-band, mas el de diagnostico, consultan el flag.

    Son CUATRO, no tres: el bloque de diagnostico abre la cuarta guarda. Es el mismo numero que
    I-band (`grep -c "if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375:" pipeline/process_viirs.py` da 4).

    Se cuenta la GUARDA, no el nombre suelto: un import sin cablear dejaria el flag inerte y este
    test en verde (A89, el cero de un grep se lee como ausencia).
    """
    s = _fuente_v750()
    guardas = re.findall(r"if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:", s)
    assert len(guardas) == 4, (
        f"esperaba 4 guardas (sitios A, B, C y el bloque de diagnostico), hay {len(guardas)}")
    assert s.count("vrp_bg_neighbor_mean_v750(") == 4, "3 llamadas + la definicion"


def test_el_recorte_a_cero_sigue_despues_del_fondo_nuevo():
    """D25 cambia el FONDO; el recorte del exceso negativo es otra pregunta, abierta con el autor."""
    s = _fuente_v750()
    assert s.count("np.maximum(") >= 3
    assert "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750" in s


def test_v750_no_nombra_el_flag_de_i_band():
    """A92: el sensor equivocado leyendo el flag del otro es el modo de falla de esta familia."""
    s = _fuente_v750()
    assert not re.search(r"(?<![A-Za-z0-9_])ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375(?![A-Za-z0-9_])", s)
    assert not re.search(r"(?<![A-Za-z0-9_])vrp_bg_neighbor_mean_v375(?![A-Za-z0-9_])", s)


def test_el_contador_se_reinicia_solo_en_el_bloque_que_publica():
    """Espejo exacto de la forma de I-band (tests/test_d25_fondo_vecinos_s142.py:216-219).

    El bloque contextual ACUMULA (+=), el segundo recompute del Test 1 REINICIA (=), y el primero
    no cuenta: si contara, el diagnostico describiria una poblacion distinta de la publicada.
    """
    s = _fuente_v750()
    assert len(re.findall(r"_bg_vecinos_n_sin_vecinos \+= _n_sin", s)) == 1
    assert len(re.findall(r"_bg_vecinos_n_sin_vecinos = _n_sin", s)) == 1
    assert len(re.findall(r"diag_L_bg_vecinos = redondear_diag\(", s)) == 2


def test_el_fondo_del_test1_promedia_sobre_la_union_de_alertados():
    """Un vecino alertado por la ruta contextual no puede entrar al promedio del fondo del Test 1."""
    s = _fuente_v750()
    union = re.findall(
        r"np\.asarray\(hot_mask_2d, dtype=bool\) \| np\.asarray\(test1_hot_filtered, dtype=bool\)", s)
    assert len(union) == 2, f"los 2 bloques del Test 1 deben usar la union; hay {len(union)}"


def test_los_diagnosticos_solo_aparecen_con_el_flag_encendido():
    """Con el flag OFF la salida queda IDENTICA a la de hoy: ni una clave nueva.

    M-band no tiene variable `record` como I-band: arma un dict literal y lo devuelve. Por eso el
    bloque se escribe sobre `salida`, el nombre que la Tarea 4 le pone a ese dict.
    """
    s = _fuente_v750()
    assert 'salida["diag_L_bg_vecinos_w_m2_sr_um"]' in s
    assert 'salida["diag_bg_vecinos_n_sin_vecinos"]' in s
    bloque = s.split("if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:")[-1]
    assert "diag_L_bg_vecinos_w_m2_sr_um" in bloque, "los diag deben colgar de la guarda del flag"


def test_el_dict_de_salida_se_devuelve_una_sola_vez():
    """Control de A49: nombrar el dict no puede dejar un `return` huerfano ni duplicado."""
    s = _fuente_v750()
    assert s.count("    salida = {") == 1
    assert s.count("    return salida") == 1


def test_con_el_flag_on_el_fondo_baja_y_la_magnitud_sube(monkeypatch):
    """El punto entero del cambio, ejercido de punta a punta sobre una escena sintetica.

    En la escena `nevado` del arnes de S142 el crater esta sobre un cono frio: la mediana del
    anillo regional es mas tibia que sus vecinos inmediatos, asi que el fondo por vecinos baja y
    el exceso sube. El arnes de M-band solo trae `nevado` y `plana` (ESCENAS_V750), no la
    `nevado_vecino_tibio` que si existe en V375 y MODIS.

    Los 6 tests de arriba son greps sobre el fuente: comprueban que el cableado ESTA ESCRITO. Este
    comprueba que FUNCIONA, que es otra cosa (A110).
    """
    import pipeline.process_viirs_mod as pvm
    sys.path.insert(0, str(ROOT / "tests"))
    import arnes_sintetico_s142 as arnes

    apagado = arnes.correr_v750("nevado")
    monkeypatch.setattr(pvm, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750", True)
    encendido = arnes.correr_v750("nevado")

    assert "diag_L_bg_vecinos_w_m2_sr_um" not in apagado
    assert "diag_L_bg_vecinos_w_m2_sr_um" in encendido
    assert encendido["vrp_mw"] >= apagado["vrp_mw"], (
        "el fondo por vecinos no puede bajar la magnitud en una cumbre fria")
    assert encendido["vrp_mw"] != apagado["vrp_mw"], (
        "la escena no ejerce el camino: un test que pasa porque no toca el codigo es peor que "
        "no tenerlo (A110). Elegir otra escena antes de dar esto por verificado")
