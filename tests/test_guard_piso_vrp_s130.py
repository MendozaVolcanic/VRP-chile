"""Guard S130 — el perfil operacional no tiene piso VRP.

POR QUE EXISTE
--------------
Hasta S130 ``mirova_equivalent`` llevaba un piso por sensor (MODIS 0,05 ·
VIIRS375 0,02 · VIIRS750 0,15 MW): si el VRP de una pasada quedaba por debajo,
``store.py`` lo ponia en CERO y el record pasaba a contar como "no hubo nada".

Nicolas decidio quitarlo en S130. La razon es del canon, no de conveniencia:

  · Coppola 2019 — el paper del sistema MIROVA — NO declara ningun piso.
  · Coppola 2014 EVALUO cortar en 2 MW, midio que el acierto bajaba de ~79 % a
    <59 %, y lo RECHAZO explicitamente: prefirio conservar falsas alertas antes
    que perder focos reales. Del regimen sub-MW dice que el 75 % son genuinos.
  · Un campo fumarolico entra a este pipeline en el orden de 0,07 MW — o sea,
    por debajo del piso de VIIRS750 que regia.

Medido antes del cambio (experiments/_s130_piso_vrp/):
  · 1.633 records pisados sobre 57.730; de esos, 582 quedaban INVISIBLES en el
    dashboard, porque ``isValidDetection()`` (frontend/index.html:1372) arranca
    con ``vrp_mw > 0`` y solo cae a ``triggered_test1`` como segundo camino.
  · Quitarlo no pierde NINGUNA noche que MIROVA haya confirmado (0 de 1.218) y
    devuelve +5 noches de recall en VIIRS750 (82,52 % -> 84,55 %).

QUE VIGILA
----------
Que una consolidacion de perfiles no reponga el piso sin querer (A63: S80
revirtio asi un fix deliberado de S65 al regenerar config desde el KMZ), y que
al quitar los VALORES no se borre el MECANISMO — otros perfiles lo usan y sigue
siendo una opcion de configuracion legitima.

Lee ``pipeline.profile``, NUNCA el YAML: es el modulo el que resuelve la
seccion y el default, y un flag escrito bajo la seccion equivocada se leeria
como su default sin dar error (A89).
"""
import importlib
import os

import pytest


PROFILE = "mirova_equivalent"
PISOS = ("MIN_VRP_MW_MODIS", "MIN_VRP_MW_VIIRS375", "MIN_VRP_MW_VIIRS750")


@pytest.fixture()
def prof():
    prev = os.environ.get("VRP_PROFILE")
    os.environ["VRP_PROFILE"] = PROFILE
    import pipeline.profile as p
    importlib.reload(p)
    yield p
    if prev is None:
        os.environ.pop("VRP_PROFILE", None)
    else:
        os.environ["VRP_PROFILE"] = prev
    importlib.reload(p)


@pytest.mark.parametrize("nombre", PISOS)
def test_el_perfil_operacional_no_tiene_piso(prof, nombre):
    """Los tres pisos valen 0 = sin piso (el default de profile.py)."""
    valor = getattr(prof, nombre)
    assert valor == 0.0, (
        f"{nombre} = {valor} en el perfil {PROFILE}. El piso VRP se quito en S130 "
        f"por decision de Nicolas, respaldada en Coppola 2014 (evaluo un corte "
        f"equivalente, midio que bajaba el acierto de ~79 % a <59 %, y lo rechazo). "
        f"Si esto falla, una consolidacion de perfiles lo repuso sin querer — ver "
        f"A63. Reponerlo a proposito requiere ciclo A45 y decision explicita."
    )


def test_el_mecanismo_del_piso_sigue_existiendo(prof, monkeypatch):
    """Quitar los VALORES no debe borrar la CAPACIDAD.

    Otros perfiles (experimental) usan pisos distintos, y el piso sigue siendo
    una opcion de configuracion valida. Este test fuerza un piso y comprueba que
    store.py lo aplica — si alguien borra el bloque de store.py, falla aca.
    """
    import pipeline.store as store

    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.5, raising=True)
    rec = {"sensor": "VIIRS_SNPP", "vrp_mw": 0.1}
    store._apply_vrp_floor(rec)

    assert rec["vrp_mw"] == 0.0, "con piso 0,5 un VRP de 0,1 debe irse a cero"
    assert rec["diag_vrp_raw_mw"] == 0.1, "el valor crudo debe preservarse"
    assert rec["diag_vrp_floor_mw"] == 0.5


def test_con_piso_cero_no_se_toca_nada(prof, monkeypatch):
    """El caso operacional: piso 0 deja el VRP intacto y no ensucia el schema."""
    import pipeline.store as store

    for nombre in PISOS:
        monkeypatch.setattr(store, nombre, 0.0, raising=True)
    rec = {"sensor": "VIIRS_NOAA20_750", "vrp_mw": 0.001}
    store._apply_vrp_floor(rec)

    assert rec["vrp_mw"] == 0.001
    assert "diag_vrp_raw_mw" not in rec
    assert "diag_vrp_floor_mw" not in rec
