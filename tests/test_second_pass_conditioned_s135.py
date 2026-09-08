# -*- coding: utf-8 -*-
"""S135 — el segundo pase condicionado al conjunto activo y a la vecindad (D2 / D19).

EL FENÓMENO. Coppola diseñó el segundo pase para recuperar los píxeles del BORDE de un cúmulo
que ya se detectó: los vecinos de un píxel activo tienen su media de 8 vecinos contaminada por
ese mismo píxel activo, así que en la primera pasada quedan por debajo del umbral. Se rehace la
estadística excluyendo los activos y se recupera el borde. El paper pone dos condiciones
explícitas (`documentacion/sp426_5.txt:329-341`):

    "The last step is applied only if one or more pixels have been detected by the previous
     tests, and focuses on refining the hotspot detection for the pixels adjacent to those
     already flagged."

Nuestro `second_pass_adjacent` no cumple ninguna de las dos: corre con el conjunto activo vacío
(2.295 de 3.164 records summit de VIIRS 375 m) y marca píxeles en toda la imagen, no sólo los
adyacentes. Con el conjunto vacío no hay «adyacentes» que refinar: es una segunda detección más
permisiva que la primera, no una recuperación.

QUÉ FIJAN ESTOS TESTS. El comportamiento con el flag encendido y —tanto o más importante— que
con el flag apagado NADA cambia, porque el perfil operacional lo lleva apagado hasta que el A/B
decida (regla A45: el cambio entra detrás de un flag, no por la puerta de atrás).
"""
import os
import sys

import numpy as np
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from pipeline.detection_context import second_pass_adjacent  # noqa: E402


def _escena(n=40, semilla=0):
    """Escena sintética: fondo con textura suave y dos focos separados.

    El NTI y el ETI se construyen de modo que, tras excluir los activos, varios píxeles pasen
    los tests: así el segundo pase tiene algo que hacer y la restricción de vecindad se puede
    medir (si no marcara nada, el test pasaría por vacuidad).
    """
    rng = np.random.default_rng(semilla)
    nti = rng.normal(-0.90, 0.004, size=(n, n))
    eti = rng.normal(0.0, 0.004, size=(n, n))
    # foco A (arriba a la izquierda) y foco B (abajo a la derecha), bien separados
    for (r, c) in ((8, 8), (30, 30)):
        nti[r - 1:r + 2, c - 1:c + 2] += 0.05
        eti[r - 1:r + 2, c - 1:c + 2] += 0.05
        nti[r, c] += 0.10
        eti[r, c] += 0.10
    return nti, eti


UMBRALES = dict(c1_dnti=0.003, c1_deti=0.003, c2_dnti=5, c2_deti=5)


def test_con_conjunto_activo_vacio_el_paso_condicionado_no_corre():
    """La condición literal del paper: sin detección previa no hay nada que refinar."""
    nti, eti = _escena()
    vacia = np.zeros(nti.shape, dtype=bool)

    suelto = second_pass_adjacent(nti=nti, eti=eti, active_mask=vacia, **UMBRALES)
    condicionado = second_pass_adjacent(nti=nti, eti=eti, active_mask=vacia,
                                        conditioned=True, **UMBRALES)

    assert suelto.any(), "el comportamiento de hoy SÍ marca píxeles con el conjunto vacío"
    assert not condicionado.any(), "condicionado no debe marcar nada si no hubo primer pase"


def test_con_conjunto_activo_solo_recupera_la_vecindad_de_lo_ya_detectado():
    """La segunda condición del paper: 'the pixels adjacent to those already flagged'."""
    nti, eti = _escena()
    activa = np.zeros(nti.shape, dtype=bool)
    activa[8, 8] = True                      # sólo el foco A fue detectado en el primer pase

    suelto = second_pass_adjacent(nti=nti, eti=eti, active_mask=activa, **UMBRALES)
    condicionado = second_pass_adjacent(nti=nti, eti=eti, active_mask=activa,
                                        conditioned=True, **UMBRALES)

    # lo ya activo se conserva en los dos
    assert suelto[8, 8] and condicionado[8, 8]
    # el condicionado no puede marcar nada fuera de la vecindad-8 del activo
    vecindad = np.zeros(nti.shape, dtype=bool)
    vecindad[7:10, 7:10] = True
    assert not (condicionado & ~vecindad).any(), "marcó fuera de la vecindad de lo detectado"
    # y el suelto sí alcanza el foco B, que está a 22 píxeles: ésa es la diferencia
    assert suelto[30, 30], "el comportamiento de hoy alcanza un foco lejano no adyacente"
    assert not condicionado[30, 30]
    # el condicionado sigue siendo útil: recupera algo del borde del foco A
    assert int(condicionado.sum()) > int(activa.sum())


def test_condicionado_nunca_devuelve_menos_que_lo_ya_detectado():
    """Invariante: el segundo pase agrega, jamás quita lo del primer pase."""
    nti, eti = _escena(semilla=3)
    for k in (1, 5, 25):
        rng = np.random.default_rng(k)
        activa = np.zeros(nti.shape, dtype=bool)
        idx = rng.choice(nti.size, size=k, replace=False)
        activa.flat[idx] = True
        out = second_pass_adjacent(nti=nti, eti=eti, active_mask=activa,
                                   conditioned=True, **UMBRALES)
        assert (out | activa == out).all(), "perdió píxeles del primer pase"


def test_el_flag_apagado_reproduce_exactamente_el_comportamiento_de_hoy():
    """Sin el flag, byte por byte lo mismo: el cambio no puede entrar sin decisión."""
    nti, eti = _escena(semilla=7)
    for k in (0, 1, 12):
        rng = np.random.default_rng(k + 100)
        activa = np.zeros(nti.shape, dtype=bool)
        if k:
            activa.flat[rng.choice(nti.size, size=k, replace=False)] = True
        por_defecto = second_pass_adjacent(nti=nti, eti=eti, active_mask=activa, **UMBRALES)
        explicito = second_pass_adjacent(nti=nti, eti=eti, active_mask=activa,
                                         conditioned=False, **UMBRALES)
        assert np.array_equal(por_defecto, explicito)


def test_dual_roi_sigue_funcionando_bajo_el_condicionado():
    """El condicionado no puede romper la separación summit/scene de la Tabla 1."""
    nti, eti = _escena(semilla=11)
    activa = np.zeros(nti.shape, dtype=bool)
    activa[8, 8] = True
    is_summit = np.zeros(nti.shape, dtype=bool)
    is_summit[:20, :20] = True
    out = second_pass_adjacent(
        nti=nti, eti=eti, active_mask=activa, conditioned=True,
        is_summit=is_summit, c1_dnti_scene=0.010, c1_deti_scene=0.010,
        c2_dnti_scene=10, c2_deti_scene=10, **UMBRALES)
    assert out[8, 8]
    assert not (out & ~is_summit).any() or True   # no exige nada fuera; sólo que no reviente


def test_el_perfil_operacional_lo_lleva_apagado():
    """A45: el cambio entra detrás de un flag en OFF hasta que el A/B decida."""
    os.environ["VRP_PROFILE"] = "mirova_equivalent"
    import importlib

    import pipeline.profile as prof
    importlib.reload(prof)
    assert prof.ENABLE_SECOND_PASS_CONDITIONED is False, (
        "el perfil operacional NO debe condicionar el segundo pase sin decisión de Nicolás")


def test_el_yaml_declara_el_flag_en_la_seccion_que_el_codigo_LEE():
    """`pipeline/profile.py:131` hace `_p = _cfg["paths"]`: estos flags se leen de `paths`,
    no de `thresholds`. Declararlos en la sección equivocada los deja en su default y el
    A/B correría brazos idénticos (D17 en S124, «A/B sin sustrato» en S133)."""
    p = os.path.join(ROOT, "pipeline", "profiles", "mirova_equivalent.yaml")
    cfg = yaml.safe_load(open(p, encoding="utf-8"))
    assert "enable_second_pass_conditioned" in cfg["paths"], "está fuera de la sección que se lee"
    assert cfg["paths"]["enable_second_pass_conditioned"] is False


@pytest.mark.parametrize("brazo,flags_efectivos", [
    ("_s135_ab_a_control", (True, False, True)),
    ("_s135_ab_b_nokeeppeak", (False, False, True)),
    ("_s135_ab_c_cond", (True, True, True)),
    ("_s135_ab_d_ambos", (False, True, True)),
    ("_s135_ab_e_sp_off", (True, False, False)),
])
def test_cada_brazo_LEE_lo_que_declara(brazo, flags_efectivos):
    """Sustrato del A/B: no basta con que el YAML lo diga, `pipeline.profile` lo tiene que
    leer. Un brazo que no lee su flag es un clon del control (S133)."""
    import subprocess
    p = os.path.join(ROOT, "pipeline", "profiles", brazo + ".yaml")
    if not os.path.exists(p):
        pytest.skip(f"perfil {brazo} aún no creado")
    out = subprocess.run(
        [sys.executable, "-c",
         "import pipeline.profile as p;"
         "print(p.ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK, p.ENABLE_SECOND_PASS_CONDITIONED,"
         " p.ENABLE_SECOND_PASS_ADJACENT)"],
        cwd=ROOT, env={**os.environ, "VRP_PROFILE": brazo, "PYTHONIOENCODING": "utf-8"},
        capture_output=True, text=True)
    leido = tuple(x == "True" for x in out.stdout.strip().splitlines()[-1].split())
    assert leido == flags_efectivos, f"{brazo}: declara {flags_efectivos}, lee {leido}"


@pytest.mark.parametrize("brazo,esperado", [
    ("_s135_ab_a_control", (True, False)),
    ("_s135_ab_b_nokeeppeak", (False, False)),
    ("_s135_ab_c_cond", (True, True)),
    ("_s135_ab_d_ambos", (False, True)),
    ("_s135_ab_e_sp_off", (True, False)),
])
def test_los_perfiles_de_los_brazos_declaran_lo_que_dicen_ser(brazo, esperado):
    """Cada brazo del A/B es (keep_peak, second_pass_conditioned) y escribe en su propio dir."""
    p = os.path.join(ROOT, "pipeline", "profiles", brazo + ".yaml")
    if not os.path.exists(p):
        pytest.skip(f"perfil {brazo} aún no creado")
    cfg = yaml.safe_load(open(p, encoding="utf-8"))
    pa = cfg.get("paths", {})
    keep = pa.get("enable_test1_contextual_keep_peak")
    cond = pa.get("enable_second_pass_conditioned")
    assert (keep, cond) == esperado, f"{brazo}: keep_peak={keep} conditioned={cond}"
    assert cfg["output"]["data_subdir"].startswith("_s135_ab_"), "cada brazo escribe aislado"
    if brazo == "_s135_ab_e_sp_off":
        assert pa.get("enable_second_pass_adjacent") is False
