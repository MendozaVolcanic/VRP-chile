# -*- coding: utf-8 -*-
"""S127 - la corona Eq.6 y el single-pixel mode tienen que usar el MISMO fondo.

POR QUE: el A/B de la corona en VIIRS375 salio inconcluso DOS veces. La segunda vez
la corona si corrio -1.179 records de 1.278- pero solo cambio el numero publicado en
15. El diagnostico, verificado sobre los brazos en disco:

    los que NO cambiaron -> single_pixel_mode: {True: 1164}
    los que SI cambiaron -> single_pixel_mode: {False: 15}

`apply_single_pixel_mode` corre DESPUES del recompute de la corona y recibe los VRP
por pixel calculados con el fondo VIEJO (el anillo regional). Para un cluster sub-MW
de <=3 px reemplaza el total por max(per_pixel), y ese maximo viene del fondo anterior:
la corona se calcula y se tira.

El caso limite lo dice todo: para un cluster de UN pixel, "la suma del cluster" y
"el maximo por pixel" son EL MISMO NUMERO por definicion. Que el single-pixel mode
cambie el valor de un cluster de un pixel solo puede significar que los dos lados
se calcularon contra fondos distintos. Y el 98 % de los clusters de Villarrica son
de un pixel.

Es una instancia de "lo declarado no coincide con lo efectivo" (tecnica T9,
docs/superpowers/plans/2026-08-30-auditoria-s127.md): el flag de la corona quedaba
encendido, el helper corria, el record decia `corona_degraded: false` -y el numero
publicado seguia siendo el del fondo viejo.

Evidencia: docs/S126_COSTO_FILTRO_CONTEXTUAL.md, docs/S126_LASCAR_ES_UN_PIXEL.md
"""
from pathlib import Path

import numpy as np
import pytest

WOOSTER_I04 = 18.0
LAMBDA_I04 = 3.74
A_PIX_I = 140625.0


def _escena_corona_tibia():
    """Escena donde la corona es MAS TIBIA que el fondo regional.

    Es el caso que importa: la corona sube el fondo, baja el dL y por lo tanto
    DESINFLA el VRP -que es justamente para lo que existe (desplomar la fluctuacion
    de terreno). Si el single-pixel mode reinyecta el valor del fondo regional, el
    desinflado se pierde entero.
    """
    bt = np.full((9, 9), 250.0)      # fondo regional frio
    bt[3:6, 3:6] = 268.0             # entorno inmediato del cluster, TIBIO
    bt[4, 4] = 271.0                 # el pixel del cluster
    areas = np.full((9, 9), A_PIX_I)
    hot = np.zeros((9, 9), dtype=bool)
    hot[4, 4] = True
    return bt, areas, hot


def test_existe_el_vrp_por_pixel_bajo_un_fondo_dado():
    """Hace falta poder pedir los VRP POR PIXEL bajo el fondo de la corona.

    Sin esto el call site no tiene con que alimentar al single-pixel mode y esta
    obligado a pasarle los del fondo viejo, que es exactamente el bug.
    """
    from pipeline.vrp_regimes import (cluster_vrp_mw_with_bg,
                                      cluster_vrp_per_pixel_with_bg)

    bt, areas, _ = _escena_corona_tibia()
    bt[4, 5] = 269.0
    cluster = [(4, 4), (4, 5)]

    por_pixel = cluster_vrp_per_pixel_with_bg(
        bt, areas, cluster, 268.0, WOOSTER_I04, LAMBDA_I04)

    assert len(por_pixel) == len(cluster), "un valor por pixel, en el mismo orden"
    total = cluster_vrp_mw_with_bg(
        bt, areas, cluster, 268.0, WOOSTER_I04, LAMBDA_I04)
    assert sum(por_pixel) == pytest.approx(total, rel=1e-12), (
        "la suma de los VRP por pixel tiene que ser el total del cluster: si no, "
        "son dos formulas distintas y van a divergir")


def test_single_pixel_mode_no_puede_cambiar_un_cluster_de_un_pixel():
    """El invariante que el bug viola.

    Para un cluster de UN pixel, sum == max por definicion. Si el single-pixel mode
    mueve el numero, es que los dos lados miraron fondos distintos.
    """
    from pipeline.process_viirs import apply_corona_magnitude_v375
    from pipeline.single_pixel_mode import apply_single_pixel_mode
    from pipeline.vrp_regimes import cluster_vrp_per_pixel_with_bg

    bt, areas, hot = _escena_corona_tibia()
    cluster = [(4, 4)]

    # VRP con el fondo REGIONAL (lo que hay antes de la corona).
    pix_regional = cluster_vrp_per_pixel_with_bg(
        bt, areas, cluster, 250.0, WOOSTER_I04, LAMBDA_I04)
    vrp_regional = sum(pix_regional)

    vrp_corona, degradada, pix_corona = apply_corona_magnitude_v375(
        vrp_regional, bt, areas, cluster, hot, enabled=True)
    assert degradada is False
    assert vrp_corona < vrp_regional, (
        "la escena esta armada para que la corona DESINFLE; si no, el test no "
        "prueba lo que dice")
    assert pix_corona is not None, (
        "con la corona aplicada, el helper tiene que devolver los VRP por pixel "
        "de ESE fondo para que el single-pixel mode no reinyecte el viejo")

    pc = apply_single_pixel_mode(
        {"n_pixels": 1, "vrp_mw": round(vrp_corona, 3)}, pix_corona,
        enabled=True, threshold_mw=5.0, max_pixels=3)

    assert pc["vrp_mw"] == pytest.approx(round(vrp_corona, 3), abs=1e-9), (
        "el single-pixel mode piso el valor de la corona. Con un solo pixel eso es "
        "imposible salvo que se le hayan pasado los VRP de otro fondo.")


def test_alimentarlo_con_el_fondo_viejo_reproduce_el_bug():
    """Contra-prueba: con los VRP del fondo regional, el bug aparece.

    Este test documenta el modo de falla exacto que dejo el A/B inconcluso. Si algun
    dia deja de fallar por si solo, es que la escena dejo de ser representativa.
    """
    from pipeline.process_viirs import apply_corona_magnitude_v375
    from pipeline.single_pixel_mode import apply_single_pixel_mode
    from pipeline.vrp_regimes import cluster_vrp_per_pixel_with_bg

    bt, areas, hot = _escena_corona_tibia()
    cluster = [(4, 4)]
    pix_viejos = cluster_vrp_per_pixel_with_bg(
        bt, areas, cluster, 250.0, WOOSTER_I04, LAMBDA_I04)

    vrp_corona, _, _ = apply_corona_magnitude_v375(
        sum(pix_viejos), bt, areas, cluster, hot, enabled=True)

    pc = apply_single_pixel_mode(
        {"n_pixels": 1, "vrp_mw": round(vrp_corona, 3)}, pix_viejos,
        enabled=True, threshold_mw=5.0, max_pixels=3)

    assert pc["single_pixel_mode"] is True
    assert pc["vrp_mw"] > round(vrp_corona, 3), (
        "con los VRP del fondo viejo el modo TIENE que reinyectar el valor grande: "
        "es el bug que este PR arregla")


def test_la_corona_degradada_no_devuelve_por_pixel():
    """Si la corona no aplico, el call site debe seguir con los VRP que ya tenia."""
    from pipeline.process_viirs import apply_corona_magnitude_v375

    bt = np.full((3, 3), np.nan)
    bt[1, 1] = 280.0
    areas = np.full((3, 3), A_PIX_I)
    hot = np.zeros((3, 3), dtype=bool)
    hot[1, 1] = True

    vrp, degradada, por_pixel = apply_corona_magnitude_v375(
        1.234, bt, areas, [(1, 1)], hot, enabled=True)
    assert degradada is True and vrp == 1.234
    assert por_pixel is None, (
        "sin corona valida no hay VRP por pixel nuevos; devolver None obliga al "
        "call site a ser explicito en vez de usar valores de un fondo que no aplico")

    vrp_off, deg_off, pix_off = apply_corona_magnitude_v375(
        1.234, bt, areas, [(1, 1)], hot, enabled=False)
    assert deg_off is None and pix_off is None and vrp_off == 1.234


def test_ningun_call_site_alimenta_el_modo_con_el_array_del_fondo_viejo():
    """Guard estructural: el bug estaba en el ORDEN, no en las funciones.

    Los helpers tenian tests y andaban bien. Lo que fallaba era que el call site
    construia `_pix_vrps` desde el array 2-D calculado con el fondo regional. Un test
    de comportamiento sobre los helpers nunca lo habria visto -- el mismo motivo por
    el que #543 necesito un guard estructural.

    La regla: entre el recompute de la corona y `apply_single_pixel_mode` no puede
    haber una lectura cruda del array de VRP viejo sin pasar por el fondo efectivo.
    """
    raiz = Path(__file__).resolve().parents[1] / "pipeline"
    for archivo, array_viejo in (("process_viirs.py", "vrp_per_pixel_2d"),
                                 ("process_viirs.py", "t1_vrp_2d"),
                                 ("process_modis.py", "vrp_per_pixel_2d")):
        src = (raiz / archivo).read_text(encoding="utf-8")
        patron = "float(%s[i, j])" % array_viejo
        assert patron not in src, (
            "%s: sigue alimentando el single-pixel mode desde `%s`, que se calculo "
            "con el fondo regional. Si la corona corrio, ese array quedo obsoleto y "
            "el modo revierte el recompute (1.164 de 1.179 records en el A/B de S126)."
            % (archivo, array_viejo))


def test_con_la_corona_apagada_el_total_es_identico_al_de_antes():
    """El no-op operacional, PROBADO en vez de afirmado.

    Los dos flags de corona estan OFF en `mirova_equivalent`, asi que este PR no debe
    mover ni un numero de produccion. Pero "es no-op" fue exactamente la afirmacion que
    en S126 (#535) apago la mascara de nube en produccion creyendo que no cambiaba nada
    -- de ahi la regla: un no-op necesita un test detras.

    Lo unico que este PR toco del camino operacional es `cluster_vrp_mw_with_bg`, que
    paso de acumular en un loop a sumar la lista por pixel. Este test reimplementa la
    formula VIEJA verbatim -- incluida su forma de saltear NaN, que ahora aportan 0.0 --
    y exige igualdad exacta, no aproximada.
    """
    import math

    from pipeline.vrp_regimes import C1, C2, cluster_vrp_mw_with_bg

    def formula_vieja(grid, areas, indices, t_bk, wooster, lam):
        l_bg = C1 / (lam ** 5 * (math.exp(C2 / (lam * float(t_bk))) - 1))
        total = 0.0
        for (i, j) in indices:
            bt = grid[i, j]
            if np.isnan(bt):
                continue
            l_pix = C1 / (lam ** 5 * (math.exp(C2 / (lam * float(bt))) - 1))
            delta = max(l_pix - l_bg, 0.0)
            total += float(areas[i, j]) * float(wooster) * delta / 1e6
        return float(total)

    rng = np.random.default_rng(127)
    for _ in range(50):
        bt = rng.uniform(240.0, 320.0, size=(6, 6))
        bt[rng.random((6, 6)) < 0.15] = np.nan          # NaN dispersos
        areas = rng.uniform(1e5, 1e6, size=(6, 6))
        idx = [(int(i), int(j)) for i, j in
               zip(rng.integers(0, 6, 5), rng.integers(0, 6, 5))]
        t_bk = float(rng.uniform(240.0, 300.0))

        nueva = cluster_vrp_mw_with_bg(bt, areas, idx, t_bk, 18.0, 3.74)
        vieja = formula_vieja(bt, areas, idx, t_bk, 18.0, 3.74)
        assert nueva == vieja, (
            "el refactor movio el total: %r vs %r (fondo %.2f K)" % (nueva, vieja, t_bk))


def test_en_modis_el_focal_no_puede_pisar_la_corona():
    """La variante LATENTE y peor: en MODIS el recompute focal esta ENCENDIDO.

    `cluster_focal_vrp_mw` reasigna `_vrp_c` sin condicion, leyendo el array de VRP
    del fondo regional. Corre inmediatamente despues de la corona, asi que con los dos
    flags encendidos la corona no se anulaba en el 98 % de los casos como en VIIRS375
    -- se anulaba en el 100 %, siempre, y sin dejar marca en el record (`corona_degraded`
    quedaba en `false`, que se lee como "la corona corrio bien").

    Hoy no se nota porque `ENABLE_LOCAL_CLUSTER_MAGNITUDE` esta OFF. Ese es exactamente
    el momento de ponerle un guard: el dia que alguien encienda la corona en MODIS para
    un A/B, el A/B mediria el control contra si mismo y saldria "sin efecto" -- el mismo
    desenlace que #539 y #543 en VIIRS375, dos veces.

    Focal y corona son ortogonales: el focal SELECCIONA que pixeles entran, la corona
    fija el FONDO. Componen bien siempre que el focal lea los VRP del fondo efectivo.
    """
    src = (Path(__file__).resolve().parents[1] / "pipeline" / "process_modis.py"
           ).read_text(encoding="utf-8")

    assert "_c[\"pixel_indices\"], vrp_per_pixel_2d, dnti_ctx_hot" not in src, (
        "process_modis.py: el recompute focal del bloque contextual lee "
        "`vrp_per_pixel_2d` (fondo regional) en vez del array efectivo. Corre despues "
        "de la corona y la pisa sin condicion ni rastro.")

    assert "_vrp_pp_eff" in src, (
        "process_modis.py: falta el array de VRP por pixel EFECTIVO (corona si aplico, "
        "regional si no). Sin el, los consumidores de aguas abajo no tienen forma de "
        "saber contra que fondo se midio.")
