# -*- coding: utf-8 -*-
"""Radiancia de fondo en la banda MIR, para persistirla en el record (Fase 0, tarea 7, plan S139).

POR QUE. La magnitud nuestra queda en ~0,7 de MIROVA y S139 la separo en conteo de pixeles y exceso
por pixel; el exceso depende del FONDO que se resta. MIROVA publica su fondo por pasada
(`Tot_Lmir_bk` en el OSF) y nosotros solo guardabamos `t_bg_k`, una temperatura redondeada a 2
decimales, del anillo 5-25 km. Para comparar fondo contra fondo sin reprocesar hace falta la
radiancia que efectivamente se resta, en la misma banda y con la misma formula de Planck que usa el
calculo de `delta_L`. Esta funcion es esa formula; no cambia ninguna decision del pipeline.

Mismas constantes que los tres procesadores (`pipeline.constants.C1/C2`):
    B(lambda, T) = C1 / (lambda^5 * (exp(C2 / (lambda * T)) - 1))   [W m-2 sr-1 um-1]
"""
from __future__ import annotations

import math
from typing import Optional

from pipeline.constants import C1, C2


def radiancia_planck(t_k, lambda_um: float) -> Optional[float]:
    """Radiancia espectral de cuerpo negro a `t_k` (K) y `lambda_um` (um). None si T no es valida."""
    if t_k is None:
        return None
    t = float(t_k)
    if not math.isfinite(t) or t <= 0:
        return None
    return C1 / (lambda_um ** 5 * (math.exp(C2 / (lambda_um * t)) - 1.0))


def redondear_diag(valor) -> Optional[float]:
    """Redondeo a 6 decimales para el JSON; deja pasar None y descarta NaN."""
    if valor is None:
        return None
    v = float(valor)
    return round(v, 6) if math.isfinite(v) else None
