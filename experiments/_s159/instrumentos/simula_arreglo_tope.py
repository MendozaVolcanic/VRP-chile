# -*- coding: utf-8 -*-
"""S159, tarea A, control: plugin de pytest que SIMULA el arreglo propuesto de store.py sin editarlo (A45).

Envuelve store._apply_sanity_cap para que, como en el diff propuesto de NOTAS.md, la temperatura de VIIRS 375
(t_max_i04_k) se copie a t_max_k ANTES de juzgar la causa. Con el arreglo simulado, la prueba xfail(strict=True)
tiene que pasar y por eso ponerse ROJA (XPASS estricto): así se comprueba que la marca vigila el defecto y no otra cosa.

Uso: PYTHONPATH=experiments/_s159/instrumentos python -m pytest -p simula_arreglo_tope tests/test_tope_cordura_v375_s159.py
"""
import pipeline.store as store

_original = store._apply_sanity_cap


def _con_normalizacion(record):
    if "t_max_i04_k" in record and "t_max_k" not in record:
        record["t_max_k"] = record["t_max_i04_k"]
    return _original(record)


store._apply_sanity_cap = _con_normalizacion
