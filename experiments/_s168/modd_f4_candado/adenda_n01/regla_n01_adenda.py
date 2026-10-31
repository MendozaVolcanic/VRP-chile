# -*- coding: utf-8 -*-
"""BORRADOR (S170, sin sellar): la regla candidata de la adenda a N-01 (§8.2 del pre-registro de MOD-D fase 4). No la
usa el evaluador sellado: vive aparte para que Nicolás la lea y para probarla. Si se aprueba, entra a
`evaluar_f4.control_identidad` (sello nuevo) y `identidad_f4.py` agrega el campo `motivo_censo`.

Regla sellada hoy (N-01): una pasada con grilla del censo que el runner saca por un motivo sellado es un desacuerdo;
cuenta como otro gránulo si la identidad lo declara así, y si no, deja la identidad en rojo.
Regla candidata: además, esa pasada cuenta como ACUERDO, y no entra al tope de otro gránulo, cuando se cumplen las
cuatro condiciones:
  1. el motivo es `escena_invalida` (sólo ese: «volcán fuera del gránulo» sigue como N-01, porque el censo sí cubrió el
     volcán y eso es justo la lectura rota de MxD03 que N-01 vigila);
  2. el port del censo llegó al mismo motivo en esa pasada (`motivo_censo == "escena_invalida"`);
  3. es el mismo gránulo (`mismo_granulo`);
  4. es la misma grilla: celda a celda igual a la precisión float32 del censo (`grilla_igual_float32`), con la misma
     máscara y el mismo VRP a 0,001 MW.
"""
MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo", "escena_invalida")
TOL_VRP_IDENTIDAD = 1e-3


def acuerdo_en_motivo(x, motivo_runner):
    """True si la pasada sellada con grilla del censo es un acuerdo según la regla candidata."""
    return (motivo_runner == "escena_invalida" and x.get("motivo_censo") == "escena_invalida"
            and bool(x.get("mismo_granulo")) and bool(x.get("grilla_igual_float32")) and bool(x.get("misma_mascara"))
            and x.get("dvrp") is not None and abs(x["dvrp"]) <= TOL_VRP_IDENTIDAD)


def selladas_sin_explicar(ident, filas):
    """Lo que cambia en control_identidad: la lista de pasadas con grilla del censo y motivo sellado que no se explican.
    Sellada hoy: se explica sólo si la identidad la declara de otro gránulo. Candidata: también si hay acuerdo en el
    motivo. filas: con `grilla_censo` y `_motivo` (como en el evaluador)."""
    sel = [(f["vol"], f["dt"], f["_motivo"]) for f in filas
           if f.get("grilla_censo") and f.get("_motivo") in MOTIVOS_SELLADOS]
    vieja = sorted((v, d) for v, d, m in sel if not ((v, d) in ident and not ident[(v, d)]["mismo_granulo"]))
    nueva = sorted((v, d) for v, d, m in sel if not ((v, d) in ident and (
        not ident[(v, d)]["mismo_granulo"] or acuerdo_en_motivo(ident[(v, d)], m))))
    return vieja, nueva
