"""A118 (S148/S149): la geometria del ROI1 tiene que llegar a TODOS los pases, no solo al primero.

POR QUE EXISTE
--------------
El ROI1 decide donde rige el umbral sensible (summit) y donde el estricto (scene). El flag
`enable_roi1_box_paper` (D18) cambia esa geometria del circulo per-volcan a la caja de 5 x 5 km del
paper. S148 encontro que la caja llegaba solo a las funciones del primer pase: los procesadores
armaban por su cuenta `is_summit = vent_dist_per_pixel <= inner_radius_km` para las llamadas a
`second_pass_adjacent`, asi que el segundo pase seguia usando el circulo y recapturaba con el umbral
sensible lo que el primero acababa de rechazar con el estricto. En 51 negativos de fuera de la caja el
primer pase cayo de 86 a 7 pixeles, la recaptura subio de 98 a 175 y el cumulo publicado quedo
identico (docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md). El A/B de la caja media el cableado, no la
caja.

`detection_context.roi1_summit_mask` ya centraliza la decision; este guard exige que los tres
procesadores la usen para TODA mascara de summit que pase a `second_pass_adjacent`, y que no quede
ninguna copia en linea de la expresion vieja (A102).

Con el flag apagado `_roi1_mask` es None y `roi1_summit_mask` devuelve el mismo circulo de siempre:
el cambio es inerte en produccion, y eso tambien se prueba aca.
"""
import ast
import os
import re

import numpy as np
import pytest

from pipeline.detection_context import roi1_summit_mask

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESADORES = ("process_modis.py", "process_viirs.py", "process_viirs_mod.py")
# la copia en linea de la geometria vieja, con frontera de palabra (A92)
EXPRESION_VIEJA = re.compile(r"(?<![A-Za-z0-9_])is_summit(_mask)?\s*=\s*vent_dist_per_pixel\s*<=\s*inner_radius_km")


def _src(f):
    return open(os.path.join(RAIZ, "pipeline", f), encoding="utf-8").read()


@pytest.mark.parametrize("f", PROCESADORES)
def test_no_queda_la_copia_en_linea_del_circulo(f):
    hits = [i + 1 for i, linea in enumerate(_src(f).splitlines()) if EXPRESION_VIEJA.search(linea)]
    assert not hits, (f"{f}: lineas {hits} arman la mascara de summit con el circulo a mano; "
                      "debe salir de roi1_summit_mask(..., _roi1_mask) para que la caja llegue al segundo pase")


@pytest.mark.parametrize("f", PROCESADORES)
def test_toda_mascara_de_summit_del_segundo_pase_sale_de_roi1_summit_mask(f):
    arbol = ast.parse(_src(f))
    # nombres asignados desde una llamada a roi1_summit_mask que recibe _roi1_mask
    buenos = set()
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Assign) and isinstance(nodo.value, ast.Call)
                and getattr(nodo.value.func, "id", None) == "roi1_summit_mask"):
            args = [getattr(a, "id", None) for a in nodo.value.args] + [getattr(k.value, "id", None) for k in nodo.value.keywords]
            assert "_roi1_mask" in args, f"{f}:{nodo.lineno}: roi1_summit_mask sin _roi1_mask"
            buenos.update(t.id for t in nodo.targets if isinstance(t, ast.Name))
    llamadas = [n for n in ast.walk(arbol) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "second_pass_adjacent"]
    assert len(llamadas) >= 3, f"{f}: esperaba al menos 3 llamadas a second_pass_adjacent, hay {len(llamadas)}"
    for c in llamadas:
        kw = {k.arg: k.value for k in c.keywords}
        assert "is_summit" in kw, f"{f}:{c.lineno}: second_pass_adjacent sin is_summit"
        usados = {n.id for n in ast.walk(kw["is_summit"]) if isinstance(n, ast.Name)} - {"ENABLE_DUAL_ROI_SECOND_PASS", "None"}
        assert usados and usados <= buenos, (f"{f}:{c.lineno}: is_summit usa {sorted(usados)}, que no sale de "
                                            f"roi1_summit_mask (validos: {sorted(buenos)})")


def test_con_el_flag_apagado_es_el_mismo_circulo_bit_a_bit():
    rng = np.random.default_rng(149)
    dist = rng.uniform(0, 30, size=(60, 60))
    for inner in (3.0, 5.0, 20.0):
        assert np.array_equal(roi1_summit_mask(dist, inner, None), dist <= inner)
