# -*- coding: utf-8 -*-
"""S145: las dos cuentas del sustrato de D25 en VIIRS 750 miden lo que dicen medir.

POR QUE. El numero de `noches_alerta_hoy_sin_cubrir` es el que da vuelta la prioridad del frente:
dice que el fondo por vecinos en M-band no destapa ni una noche de alerta. Un instrumento que
decide se valida antes de usarse (A110), y una cuenta que nombra un conjunto tiene que salir de la
definicion de ese conjunto y no de un pareo intermedio (A93).

Las dos trampas que estos tests cubren:
  - contar una noche como ganada cuando OTRA pasada de esa misma noche ya publica (seria contar
    recall que ya tenemos; es el error de unidades de A94);
  - clasificar por distancia sin mirar el radio interno del volcan, que va de 3 a 20 km segun el
    volcan y no es uniforme.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "_s145_d25_v750"))

from sustrato import clasificar, noches  # noqa: E402


def _r(vol, noche, lab):
    return {"vol": vol, "noche": noche, "lab": lab}


def test_una_noche_ya_cubierta_por_otra_pasada_no_cuenta_como_ganada():
    """El corazon de A94: si otra pasada de esa noche ya publica, rescatar esta no agrega alerta."""
    rescate = [_r("Villarrica", "2026-05-01", "pos")]
    ya_cubiertas = {("Villarrica", "2026-05-01")}
    assert noches(rescate, "pos", ya_cubiertas) == []
    assert noches(rescate, "pos", set()) == ["Villarrica 2026-05-01"]


def test_la_cobertura_es_por_volcan_y_noche_no_por_noche_sola():
    """Que Villarrica publique el 1 de mayo no cubre a Llaima el 1 de mayo."""
    rescate = [_r("Llaima", "2026-05-01", "pos")]
    assert noches(rescate, "pos", {("Villarrica", "2026-05-01")}) == ["Llaima 2026-05-01"]


def test_cada_etiqueta_cuenta_por_separado_y_las_noches_no_se_repiten():
    rescate = [_r("Isluga", "2026-06-02", "pos"),
               _r("Isluga", "2026-06-02", "pos"),      # dos pasadas, una sola noche
               _r("Isluga", "2026-06-03", "neg_limpio")]
    assert noches(rescate, "pos", set()) == ["Isluga 2026-06-02"]
    assert noches(rescate, "neg_limpio", set()) == ["Isluga 2026-06-03"]


def test_clasificar_usa_el_radio_interno_del_volcan_y_no_un_corte_fijo():
    """Mismo cumulo a 6 km: dentro en Cordon Caulle (inner 20), fuera en Lastarria (inner 3)."""
    r = {"pc_dist": 6.0, "pc_vrp": 0.0}
    assert clasificar(r, 20.0) == "rescate_crater_en_cero"
    assert clasificar(r, 3.0) == "cumulo_fuera_del_inner"


def test_clasificar_separa_el_cero_de_la_magnitud_y_el_sin_cumulo():
    assert clasificar({"pc_dist": None, "pc_vrp": None}, 5.0) == "sin_cumulo"
    assert clasificar({"pc_dist": 1.0, "pc_vrp": 0.0}, 5.0) == "rescate_crater_en_cero"
    assert clasificar({"pc_dist": 1.0, "pc_vrp": None}, 5.0) == "rescate_crater_en_cero"
    assert clasificar({"pc_dist": 1.0, "pc_vrp": 0.3}, 5.0) == "expuesta_ya_tiene_magnitud"
