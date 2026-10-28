# -*- coding: utf-8 -*-
"""Evaluador VACÍO de S166 MOD-D fase 4: los mismos nombres que evaluar_f4.py, sin lógica. La batería corrida contra
este módulo tiene que fallar en TODOS sus escenarios, y por aserción (no por excepción): así se prueba que cada
escenario mide algo del evaluador y no pasa por construcción (S152, S156)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def variante_posicion(rec, regla, dists, inner):
    return None


def distancias(*a, **k):
    return {}


def evaluable(f):
    return False, None


def armar_tabla(filas, predicado=None):
    return filas


def predicado_node(casos):
    return [(0, 0.0)] * len(casos)


def control_placebo(filas):
    return {}


def control_contador(filas, predicado=None):
    return {}


def control_predicado(predicado=None):
    return {}


def evaluar(*a, **k):
    return {}
