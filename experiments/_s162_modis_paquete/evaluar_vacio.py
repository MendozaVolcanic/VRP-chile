# -*- coding: utf-8 -*-
"""Evaluador VACÍO de MOD-D: la misma interfaz que evaluar_paquete.evaluar, que no mira los datos y devuelve siempre la
estructura completa con CANDIDATO y todo en orden. Existe sólo para que probar_evaluar_paquete.py demuestre que cada
prueba puede fallar (S156): contra este archivo, todas tienen que fallar por aserción."""


def _brazo():
    return {"p1": {"estado": "SIN PERDIDA", "perdidas": [], "n_protegidas_k": 0},
            "p1b": {"decide": [], "contraria_lista": []},
            "p2": {"estado": "EMPATE", "neto": 0, "B": 0, "s_k": 0, "s_b": 0, "sumas_bloque": [], "discordantes": []},
            "m": {"n": 0, "regla": "SIN PARES"}, "curva_cenit": {}, "costura": {}, "noches_a94": {"lista": []},
            "soporte_adenda1": {"n": 0, "candidatas": [], "lista": [], "por_soporte_y_cenit": {}},
            "borde_granulo": {}}


BLOBS_SELLADOS = {}


def externos_de_entrada(pob, cab, crudas, ref, commit_esperado=None):
    return {k: {"estado": "OK"} for k in ("manifiesto", "blobs", "predicado", "procedencia", "referencia",
                                         "reetiquetado")}


def evaluar(filas, grillas, recorridos, externos, esperadas, crudas, nuestros=(), alertas_mirova=None, dir_s159=None):
    ok = {"estado": "OK"}
    return {"veredicto": "CANDIDATO",
            "controles": {"k_produccion": dict(ok), "port_s159": dict(ok), "placebo": dict(ok, n=0, dprima_max_abs=0),
                          "contador": dict(ok, inyectados=0, s_pm_antes=0, s_pm_con_inyeccion=0),
                          "cobertura": dict(ok, fuera_del_denominador={}, protegidas_fuera_del_denominador=[])},
            "brazos": {b: _brazo() for b in ("PM", "PM-geo5", "PM-sens", "K33", "PM-pixel", "PM-b21")},
            "chillan": {"estado": "SIN RESOLVER", "recuperadas": [], "pares": [], "n_pares": 0},
            "s1": {"n_ok": 0, "n_identidad_falla": 0, "tabla": {}}}
