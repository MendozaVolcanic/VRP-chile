# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): flags de los que depende la taxonomía del probe, afirmados (no sólo impresos).

POR QUÉ (VERIFICADOR_V2_PRE_CORRIDA.md H10). Las imposibilidades por construcción del plan (§4) valen
con el código de hoy: nada filtra la máscara entre el segundo pase (process_viirs.py:1287) y el cúmulo
contextual (:1467), el segundo pase no está condicionado, y la ruta del Test 1 publica
Test 1 ∩ dNTI contextual más el pico. Si un flag cambia, las imposibilidades dejan de valer y los
rótulos mienten en silencio; por eso el runner se detiene antes de bajar un solo granule.
Los nombres se leen del namespace de `pipeline.process_viirs` (A89).
"""

FLAGS_ESPERADOS = {
    "ENABLE_FIRST_PASS_TESTS_2_AND_3": True,
    "ENABLE_SECOND_PASS_ADJACENT": True,
    "ENABLE_SECOND_PASS_CONDITIONED": False,
    "ENABLE_SECOND_PASS_INTRA_RADIO_GATE": False,
    "ENABLE_FINAL_PIXEL_FILTER": False,
    "PATH_D_REQUIRES_COVALIDATION": False,
    "ENABLE_EXCLUDE_ZONES": False,
    "ENABLE_ETI_QUADRATIC_SCENE": False,
    "ENABLE_DNTI_CONTEXTUAL_PATH": True,
    "ENABLE_DNTI_DUAL_ROI": True,
    "ENABLE_TEST1_NTI_INTEGRAL": False,
    "ENABLE_TEST1_CONTEXTUAL_FILTER": True,
    "ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK": True,
    "ENABLE_TEST1_PIXEL_FILTER": False,
    "ENABLE_TEST1_SPATIAL_CORE": False,
    "ENABLE_TEST1_LAVA_LAKE_EQ16": False,
    "ENABLE_VENT_ANCHORED_CLUSTERING": True,
}

_FALTA = object()


def verificar_flags(ns):
    distintos = {}
    for k, v in FLAGS_ESPERADOS.items():
        real = getattr(ns, k, _FALTA)
        if real is _FALTA:
            distintos[k] = "<no existe>"
        elif real != v:
            distintos[k] = real
    assert not distintos, f"flags distintos de los que asume la taxonomía del probe: {distintos}"
