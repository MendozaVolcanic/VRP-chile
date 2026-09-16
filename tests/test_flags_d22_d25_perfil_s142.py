# -*- coding: utf-8 -*-
"""S142: los flags D22 y D25 existen, están OFF en el perfil operacional, se declaran en la sección
que el código LEE, y cada brazo del A/B lee lo que declara.

POR QUÉ LA SECCIÓN IMPORTA. `pipeline/profile.py` lee los `enable_*` de `paths:` (`_p`) y los
parámetros de `thresholds:` (`_t`). Una clave en la sección equivocada arranca en su default sin
síntoma y el A/B corre brazos idénticos (S124 con enable_utm_regrid, S133 "A/B sin sustrato").

BRAZOS DEL A/B: los perfiles `_s142_ab_*` son de la Tarea 7 del plan, que NO se ejecutó en esta
sesión (decisión del dueño: Tareas 0 a 6). Sus tests quedan escritos y se saltan mientras los
perfiles no existan, así que se vuelven exigibles solos en cuanto la Tarea 7 los cree.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
YAML_OP = ROOT / "pipeline" / "profiles" / "mirova_equivalent.yaml"
PERFILES = ROOT / "pipeline" / "profiles"
LEER = ("import pipeline.profile as p;"
        "print(p.ENABLE_TESTS_23_NO_BT_GATE_VIIRS375, p.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375,"
        " p.ENABLE_SECOND_PASS_CONDITIONED, p.ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK,"
        " p.ENABLE_SECOND_PASS_ADJACENT, p.ENABLE_TESTS_23_PROSE_BRANCH,"
        " p.ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375, p.VRP_BG_NEIGHBOR_MAX_HALF_PX,"
        " p.SENSOR_MODIS, p.SENSOR_VIIRS_375, p.SENSOR_VIIRS_750, p.DATA_SUBDIR)")


def _leer_perfil(nombre):
    out = subprocess.run([sys.executable, "-c", LEER], cwd=str(ROOT), capture_output=True, text=True,
                         env={**os.environ, "VRP_PROFILE": nombre, "PYTHONIOENCODING": "utf-8"})
    assert out.returncode == 0, out.stderr[-2000:]
    campos = out.stdout.strip().splitlines()[-1].split()
    flags = tuple(c == "True" for c in campos[:7])
    return flags, int(campos[7]), tuple(c == "True" for c in campos[8:11]), campos[11]


def test_el_perfil_operacional_los_lleva_apagados():
    flags, max_half, _sens, subdir = _leer_perfil("mirova_equivalent")
    assert flags[0] is False and flags[1] is False
    assert max_half == 3
    assert subdir == "mirova_equivalent"


def test_el_yaml_los_declara_en_la_seccion_que_el_codigo_lee():
    cfg = yaml.safe_load(YAML_OP.read_text(encoding="utf-8"))
    for clave in ("enable_tests_23_no_bt_gate_viirs375", "enable_vrp_bg_neighbor_mean_viirs375"):
        assert clave in cfg["paths"], f"{clave} fuera de paths:"
        assert cfg["paths"][clave] is False
        assert clave not in cfg["thresholds"] and clave not in cfg
    assert cfg["thresholds"]["vrp_bg_neighbor_max_half_px"] == 3
    assert "vrp_bg_neighbor_max_half_px" not in cfg["paths"]


def test_max_half_invalido_falla_con_mensaje_claro(tmp_path):
    """Un perfil mal escrito falla con mensaje claro, no con un IndexError dentro del bucle.

    POR QUÉ NO SE CARGA UN PERFIL DE VERDAD. `pipeline/profile.py` sólo reconoce perfiles que
    estén en `pipeline/profiles/` (VALID_PROFILES sale de un glob de ese directorio), así que un
    YAML en una ruta temporal no se puede cargar por VRP_PROFILE. Y escribir el perfil roto
    dentro del repo deja basura versionable si el test se interrumpe (H10 del verificador del
    plan). Entonces el YAML se escribe en tmp_path y se pasa por el MISMO validador que corre al
    cargar el perfil, que es donde vive la regla.
    """
    from pipeline.profile import validar_vrp_bg_neighbor_max_half_px as validar
    p = tmp_path / "_s142_tmp_max_half_cero.yaml"
    p.write_text("thresholds:\n  vrp_bg_neighbor_max_half_px: 0\n", encoding="utf-8")
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="vrp_bg_neighbor_max_half_px"):
        validar(cfg["thresholds"]["vrp_bg_neighbor_max_half_px"])
    with pytest.raises(ValueError, match="vrp_bg_neighbor_max_half_px"):
        validar(-1)
    assert validar(3) == 3 and validar(1) == 1
    assert not list(PERFILES.glob("_s142_tmp_*")), "el test dejó un perfil suelto en el repo"


# (no_gate, vecinos, conditioned, keep_peak, adjacent, prose, corona)
BRAZOS = {
    "_s142_ab_control":            (False, False, False, True,  True, False, False),
    "_s142_ab_literal":            (True,  True,  True,  False, True, False, False),
    "_s142_ab_lit_sin_fondo":      (True,  False, True,  False, True, False, False),
    "_s142_ab_lit_con_compuerta":  (False, True,  True,  False, True, False, False),
    "_s142_ab_lit_sp_suelto":      (True,  True,  False, False, True, False, False),
    "_s142_ab_lit_keep_peak":      (True,  True,  True,  True,  True, False, False),
}


@pytest.mark.parametrize("brazo,esperado", sorted(BRAZOS.items()))
def test_cada_brazo_lee_lo_que_declara(brazo, esperado):
    if not (PERFILES / f"{brazo}.yaml").exists():
        pytest.skip(f"falta el perfil {brazo} (Tarea 7, fuera del alcance de esta sesión)")
    flags, max_half, sensores, subdir = _leer_perfil(brazo)
    assert flags == esperado, f"{brazo}: declara {esperado}, lee {flags}"
    assert max_half == 3
    assert sensores == (False, True, False), f"{brazo}: el A/B de la Fase 1 es sólo VIIRS 375"
    assert subdir == brazo, f"{brazo}: escribe en {subdir}, no aislado"


def test_ningun_brazo_apaga_keep_peak_solo():
    """Spec §6: nunca keep_peak apagado solo (§1.3 del spec)."""
    for brazo, f in BRAZOS.items():
        solo_keep_peak_off = (not f[3]) and not (f[0] or f[1] or f[2])
        assert not solo_keep_peak_off, brazo


def test_el_perfil_de_verificacion_solo_enciende_los_dos_flags_nuevos():
    nombre = "_s142_verif_flags_nuevos"
    if not (PERFILES / f"{nombre}.yaml").exists():
        pytest.fail(f"falta el perfil {nombre} (Tarea 6)")
    flags, _mh, _s, subdir = _leer_perfil(nombre)
    _f_op, _mh2, _s2, _sub = _leer_perfil("mirova_equivalent")
    assert flags[:2] == (True, True)
    assert flags[2:] == _f_op[2:], "el perfil de verificación no puede cambiar otros flags"
    assert subdir == nombre
