# -*- coding: utf-8 -*-
"""Evaluador VACIO del A/B de MxD03: misma interfaz que evaluar_mxd03.py y ninguna regla. Existe solo para mostrar que
cada prueba de probar_evaluar_mxd03.py FALLA cuando el evaluador no hace nada (S140)."""
TOL_S = 120


def pareadas(lista, t):
    return list(lista)


def filas_p2(filas):
    return []


def ruido_p2(dr):
    return 0


def regla_p2(dx, dr, r_vivo):
    return "EMPATE"


def p1(filas):
    return {"estado": "SIN PERDIDA", "perdidas": []}


def p2(filas):
    return {"estado": "EMPATE", "delta_x": None}


def p2_informe(filas):
    return {"sobre35": {"delta_x": None}, "sin_cc_le35": {"delta_x": None}}


def p6(filas):
    return []


def control_k2(filas):
    return "OK"


def control_arnes(filas, recorridos):
    return {"estado": "OK", "deriva": []}


def control_cobertura(filas, esperadas):
    return {"estado": "OK", "none_por_brazo": {}}


def m_informa(filas):
    return {"regla_d": "NEUTRO", "g": None}


def regla_vara(a, b):
    return "NO DETIENE"


def evaluar_filas(filas, recorridos, vara=None, externos=None):
    return {}


def veredicto(res):
    return "?"
