# -*- coding: utf-8 -*-
"""S126 — fija el estado REAL de la máscara de nube en el perfil operacional.

POR QUÉ EXISTE: el PR #535 (S125) sacó el umbral de nube de un literal y lo pasó
al perfil, y su comentario afirmaba que el cambio era "NO-OP en producción" porque
`mirova_equivalent.yaml` fijaría `cloud_mask_bt_k: 260.0`. Ese YAML declara `0.0`
desde S29 y #535 no lo tocó, así que el cambio NO fue inerte: apagó la máscara de
VIIRS 375 en producción. Nadie lo notó porque nada verificaba la afirmación.

Este test convierte esa afirmación en algo que el CI comprueba. No pretende que
`0.0` sea la respuesta correcta —eso lo decide el A/B de los perfiles
`_s125_cloudmask_{on,off}`— sino que un cambio de ese valor sea una decisión
CONSCIENTE y no un efecto colateral: si alguien lo mueve, este test falla y lo
obliga a actualizar el veredicto junto con el valor.

Es la defensa durable que pide A63 (una consolidación no puede revertir una
intención deliberada sin que algo grite) y el antídoto a A87 (un flag no dice por
sí solo en qué estado quedó el sistema).
"""
import importlib

import pytest


@pytest.fixture
def profile_operacional(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as prof
    return importlib.reload(prof)


def test_umbral_de_nube_operacional_es_cero_y_eso_apaga_la_mascara(profile_operacional):
    """El perfil operacional declara 0.0 → la máscara NO filtra nada.

    Si este test falla, alguien cambió el umbral. Antes de actualizar el número:
    leer docs/S126_CLOUDMASK_YA_ESTA_VIVA.md y el veredicto del A/B, y dejar
    escrito en el commit por qué el nuevo valor es el correcto.
    """
    assert profile_operacional.CLOUD_MASK_BT_K == 0.0, (
        "cloud_mask_bt_k cambió en mirova_equivalent.yaml. Eso mueve la semántica "
        "de VIIRS 375 en producción (noches ciegas vs fondo contaminado). "
        "Ver docs/S126_CLOUDMASK_YA_ESTA_VIVA.md antes de tocar este test.")


def test_los_dos_brazos_del_ab_siguen_difiriendo_solo_en_el_umbral(monkeypatch):
    """Guard del A/B: si los perfiles dejan de diferir, el experimento no mide nada."""
    import pipeline.profile as prof

    valores = {}
    for nombre in ("_s125_cloudmask_on", "_s125_cloudmask_off"):
        monkeypatch.setenv("VRP_PROFILE", nombre)
        p = importlib.reload(prof)
        valores[nombre] = (p.CLOUD_MASK_BT_K, p.DATA_SUBDIR)

    assert valores["_s125_cloudmask_on"][0] == 260.0
    assert valores["_s125_cloudmask_off"][0] == 0.0
    assert valores["_s125_cloudmask_on"][1] != valores["_s125_cloudmask_off"][1], (
        "los dos brazos escriben al mismo data_subdir: se pisarían (A47)")


def test_un_umbral_de_cero_deja_pasar_todo_el_rango_de_bt_real(profile_operacional):
    """Semántica del umbral: `I05 >= 0.0` es verdadero para cualquier BT física.

    Documenta por qué 0.0 significa "apagada" y no "umbral muy bajo": no existe
    una temperatura de brillo negativa, así que la comparación nunca descarta.
    """
    umbral = profile_operacional.CLOUD_MASK_BT_K
    for bt_k in (180.0, 220.0, 259.9, 260.0, 300.0, 400.0):
        assert bt_k >= umbral, f"BT {bt_k} K quedaría enmascarada con umbral {umbral}"
