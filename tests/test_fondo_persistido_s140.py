# -*- coding: utf-8 -*-
"""Fase 0 tarea 7 (S140): el record guarda la radiancia de fondo que se resta, sin cambiar decisiones.

POR QUE: MIROVA publica su fondo por pasada (`Tot_Lmir_bk`) y nosotros solo `t_bg_k` redondeado.
Para comparar fondo contra fondo sin reprocesar, cada record guarda:
  * `diag_L_bg_w_m2_sr_um`: la radiancia del fondo global del anillo, en la banda MIR del sensor;
  * `diag_n_bg_anillo`: cuantos pixeles del anillo entraron a la mediana de `t_bg`. El plan lo
    llamaba `diag_n_suitable`, pero en el paper "suitable" son los pixeles aptos para mu y sigma de
    los Tests 2 y 3, que es otra cosa (renombrado S140, recomendacion aceptada por Nicolas);
  * `diag_L_bg_local_w_m2_sr_um`: la mediana del fondo por pixel cuando actua el kernel local 3x3
    (los 5 volcanes opt-in), que es justo donde el fondo global engañaria; None si no actua o no hay
    kernel (VIIRS 750 m).

No existe un test que procese un granule sintetico de punta a punta; por eso se fija (a) que la
radiancia coincide con la funcion de Planck de cada procesador y (b) con guards de fuente, con
frontera de palabra (A92), que cada record usa la banda con la que se calcula `delta_L`.
"""
import math
import re
from pathlib import Path

import numpy as np
import pytest

from pipeline.diag_fondo import radiancia_planck

ROOT = Path(__file__).resolve().parents[1]


def _src(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("t", [230.0, 255.3, 271.84, 300.0])
def test_coincide_con_planck_de_los_procesadores(t):
    import pipeline.process_modis as pm
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    modis = pm.C1 / (pm.BAND21_LAMBDA ** 5 * (np.exp(pm.C2 / (pm.BAND21_LAMBDA * t)) - 1))
    assert math.isclose(radiancia_planck(t, pm.BAND21_LAMBDA), float(modis), rel_tol=1e-12)
    assert math.isclose(radiancia_planck(t, pv.I04_LAMBDA),
                        float(pv.bt_to_spectral_radiance(np.float64(t), pv.I04_LAMBDA)), rel_tol=1e-12)
    assert math.isclose(radiancia_planck(t, pvm.M13_LAMBDA),
                        float(pvm.bt_to_spectral_radiance(np.float64(t), pvm.M13_LAMBDA)), rel_tol=1e-12)


def test_temperatura_invalida_da_none():
    for t in (None, float("nan"), 0.0, -5.0):
        assert radiancia_planck(t, 3.74) is None


@pytest.mark.parametrize("rel,t_bg,lam,n_bg", [
    ("pipeline/process_modis.py", "t_bg", "BAND21_LAMBDA", "_n_bg"),
    ("pipeline/process_viirs.py", "t_bg_i04", "I04_LAMBDA", "n_bg_i04"),
    ("pipeline/process_viirs_mod.py", "t_bg", "M13_LAMBDA", "_n_bg"),
])
def test_record_guarda_fondo_en_la_banda_del_delta_L(rel, t_bg, lam, n_bg):
    s = _src(rel)
    assert re.search(r'"diag_L_bg_w_m2_sr_um":\s*redondear_diag\(radiancia_planck\(' + t_bg + r",\s*" + lam + r"\)\)", s), rel
    assert re.search(r'"diag_n_bg_anillo":\s*int\(' + re.escape(n_bg) + r"\)", s), rel
    assert re.search(r'"diag_L_bg_local_w_m2_sr_um":', s), rel
    assert not re.search(r"(?<![A-Za-z0-9_])diag_n_suitable(?![A-Za-z0-9_])", s), f"{rel}: nombre viejo"


@pytest.mark.parametrize("rel", ["pipeline/process_modis.py", "pipeline/process_viirs.py"])
def test_kernel_local_persiste_la_mediana_del_fondo_que_resta(rel):
    s = _src(rel)
    init = re.search(r"^\s*diag_L_bg_local = None\b", s, flags=re.M)
    kernel = re.search(r"^\s*if ENABLE_LOCAL_KERNEL_BG and local_kernel_bg_compatible:", s, flags=re.M)
    asigna = re.search(r"^\s*diag_L_bg_local = redondear_diag\(float\(np\.nanmedian\(L_bg\)\)\)", s, flags=re.M)
    assert init and kernel and asigna, rel
    # la inicializacion va antes del kernel: sin eso, una pasada sin pixeles anomalos da NameError
    assert init.start() < kernel.start() < asigna.start(), rel
    assert re.search(r'"diag_L_bg_local_w_m2_sr_um":\s*diag_L_bg_local\b', s), rel


def test_mband_no_tiene_kernel_y_guarda_none():
    assert re.search(r'"diag_L_bg_local_w_m2_sr_um":\s*None\b', _src("pipeline/process_viirs_mod.py"))
