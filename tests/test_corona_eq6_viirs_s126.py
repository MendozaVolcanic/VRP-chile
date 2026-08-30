# -*- coding: utf-8 -*-
"""S126 - corona Eq.6 (Coppola 2016a) cableada en VIIRS 375.

POR QUE: el fondo del Test 1 en VIIRS375 sale hoy de un anillo fijo [1,5-3] km al
crater mientras el ROI del Test 1 es el disco de 3 km (TEST1_ROI_KM). El anillo es
el 75 % del area de lo que mide, asi que cada pixel se compara contra la media de
sus propios tres cuartos exteriores y el clip a cero de process_viirs.py se queda
con la mitad de arriba: un fondo AUTORREFERENTE.

Coppola 2016a SP426.5 Eq.6, verbatim: "L4bk is estimated from the arithmetic mean
of all the pixels surrounding the active one (or around the active cluster)".

Evidencia: docs/S126_COSTO_FILTRO_CONTEXTUAL.md
"""
import importlib

import numpy as np
import pytest


def _profile(monkeypatch, name="mirova_equivalent"):
    monkeypatch.setenv("VRP_PROFILE", name)
    import pipeline.profile as prof
    return importlib.reload(prof)


def test_flag_corona_v375_existe_y_esta_off_por_defecto(monkeypatch):
    """El flag existe y NO cambia el comportamiento operacional."""
    prof = _profile(monkeypatch)
    assert prof.ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 is False


def test_corona_desploma_la_fluctuacion_y_conserva_el_foco():
    """La corona Eq.6 distingue lo que un anillo fijo al crater no puede.

    Dos escenas identicas salvo por el ENTORNO del pixel caliente:
      - fluctuacion: vecinos a la misma temperatura -> dL ~ 0 -> se desploma.
      - foco real:   vecinos frios (nieve)          -> dL grande -> sobrevive.

    Un fondo tomado de un anillo lejano daria el MISMO numero en los dos casos:
    no mira el entorno del pixel, asi que no puede separarlos. Este es el eje
    espacial que A83 identifico como el unico capaz de discriminar.
    """
    from pipeline.vrp_regimes import cluster_corona_background, cluster_vrp_mw_with_bg

    areas = np.full((7, 7), 140625.0)          # I-band nadir
    cluster = [(3, 3)]
    hot = np.zeros((7, 7), dtype=bool)
    hot[3, 3] = True

    fluctuacion = np.full((7, 7), 272.0)
    fluctuacion[3, 3] = 273.0                  # 1 K sobre un entorno a su temperatura

    foco = np.full((7, 7), 272.0)
    foco[2:5, 2:5] = 262.0                     # entorno inmediato frio
    foco[3, 3] = 273.0                         # mismo pixel, misma temperatura

    t_bk_fluct, deg_f = cluster_corona_background(fluctuacion, cluster, hot)
    t_bk_foco, deg_c = cluster_corona_background(foco, cluster, hot)
    assert not deg_f and not deg_c
    assert t_bk_fluct == pytest.approx(272.0)
    assert t_bk_foco == pytest.approx(262.0)

    vrp_fluct = cluster_vrp_mw_with_bg(fluctuacion, areas, cluster, t_bk_fluct, 18.0, 3.74)
    vrp_foco = cluster_vrp_mw_with_bg(foco, areas, cluster, t_bk_foco, 18.0, 3.74)

    assert vrp_foco > 5 * vrp_fluct, (
        f"la corona no discrimina: fluctuacion={vrp_fluct:.5f} foco={vrp_foco:.5f}")


def test_corona_v375_recomputa_el_vrp_solo_con_el_flag_on():
    """El helper de VIIRS375 aplica la corona unicamente cuando el flag esta ON."""
    from pipeline.process_viirs import apply_corona_magnitude_v375

    bt = np.full((7, 7), 272.0)
    bt[2:5, 2:5] = 262.0
    bt[3, 3] = 280.0
    areas = np.full((7, 7), 140625.0)
    hot = np.zeros((7, 7), dtype=bool)
    hot[3, 3] = True

    base = 1.234
    off, deg_off, pix_off = apply_corona_magnitude_v375(
        base, bt, areas, [(3, 3)], hot, enabled=False)
    assert off == base and deg_off is None and pix_off is None

    on, deg_on, pix_on = apply_corona_magnitude_v375(
        base, bt, areas, [(3, 3)], hot, enabled=True)
    assert deg_on is False and pix_on is not None
    assert on != base and on > 0


def test_corona_v375_usa_la_banda_I04_y_su_coeficiente():
    """Debe usar I04 (3,74 um) y Wooster 18,0, no los de otra banda."""
    from pipeline.process_viirs import apply_corona_magnitude_v375
    from pipeline.vrp_regimes import cluster_vrp_mw_with_bg

    bt = np.full((7, 7), 272.0)
    bt[2:5, 2:5] = 262.0
    bt[3, 3] = 285.0
    areas = np.full((7, 7), 140625.0)
    hot = np.zeros((7, 7), dtype=bool)
    hot[3, 3] = True

    out, deg, _ = apply_corona_magnitude_v375(
        9.99, bt, areas, [(3, 3)], hot, enabled=True)
    assert deg is False
    esperado = cluster_vrp_mw_with_bg(bt, areas, [(3, 3)], 262.0, 18.0, 3.74)
    assert out == pytest.approx(esperado, rel=1e-9)


def test_corona_v375_degradada_conserva_el_vrp_regional():
    """Con menos de min_corona pixeles validos NO se pisa el VRP.

    El fallback es EXPLICITO (degraded=True queda en el record) y no silencioso,
    para poder contar despues cuantas veces la corona no alcanzo.
    """
    from pipeline.process_viirs import apply_corona_magnitude_v375

    bt = np.full((3, 3), np.nan)
    bt[1, 1] = 280.0                            # corona entera NaN -> degradada
    areas = np.full((3, 3), 140625.0)
    hot = np.zeros((3, 3), dtype=bool)
    hot[1, 1] = True

    base = 1.234
    out, deg, _ = apply_corona_magnitude_v375(
        base, bt, areas, [(1, 1)], hot, enabled=True)
    assert deg is True
    assert out == base


def test_la_corona_esta_cableada_en_LOS_DOS_paths_de_viirs375():
    """Guard del modo de falla que arruino el primer A/B (#539).

    La corona se cableo primero SOLO en el bloque Test 1, y el A/B salio identico al
    control en los 5 volcanes. Diagnostico: de las 80 noches que se comparan contra
    MIROVA, 77 vienen del path CONTEXTUAL y solo 3 del Test 1 — la corona no llegaba
    adonde se mide. Es el mismo modo de falla que el brazo A de S125 ("la corona no
    dice que no sirve, dice que no llega adonde se mide"), y MODIS la tiene justamente
    en el bloque contextual (process_modis.py:1049), no en su Test 1.

    Este test es estructural a proposito: el bug no estaba en la funcion —que ya tenia
    tests y andaba bien— sino en DONDE se la llamaba. Un test de comportamiento sobre
    el helper no lo habria visto nunca.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "pipeline" / "process_viirs.py"
           ).read_text(encoding="utf-8")
    llamadas = src.count("apply_corona_magnitude_v375(")
    # 1 definicion + 2 call sites
    assert llamadas >= 3, (
        f"solo hay {llamadas - 1} call site(s) de la corona en process_viirs.py. "
        "Tienen que ser 2: el bloque contextual (_clusters) y el bloque Test 1 "
        "(t1_clusters). Con uno solo, el A/B mide un path que casi no se compara.")

    # y las dos ramas deben marcar el record, para poder auditarlo despues
    assert src.count('primary_cluster["corona_degraded"]') >= 2, (
        "las dos ramas deben dejar `corona_degraded` en el record; sin esa marca no "
        "se puede distinguir 'la corona corrio y no cambio nada' de 'la corona no corrio'."
    )
