# -*- coding: utf-8 -*-
"""Selector del lector para el re-control (vuelta 65 del loop).
LECTOR=estudio : dist_png.py del estudio (scipy, desempate por ruido de punto flotante)
LECTOR=port    : dist_serie.py (OpenCV, puntaje redondeado y orden estable: gana la fila de arriba)
LECTOR=centro  : port, pero el pico se mueve al centro de la meseta de empate (los pixeles con el mismo
                 puntaje dentro de +-sep alrededor del pico), que es el centro geometrico del marcador."""
import os
import numpy as np

modo = os.environ.get("LECTOR", "port")
if modo == "estudio":
    from dist_png_estudio import *          # noqa
    import dist_png_estudio as _m
else:
    from dist_serie import *                # noqa
    import dist_serie as _m
    if modo == "centro":
        def _picos(score, umbral, sep=3):
            score = np.round(score, 9)
            ys, xs = np.nonzero(score >= umbral)
            orden = np.argsort(-score[ys, xs], kind="stable")
            tomados = []
            for i in orden:
                y, x = ys[i], xs[i]
                if all(abs(y - a) > sep or abs(x - b) > sep for a, b, _ in tomados):
                    s = score[y, x]
                    y0, x0 = max(0, y - sep), max(0, x - sep)
                    w = score[y0:y + sep + 1, x0:x + sep + 1] == s
                    py, px = np.nonzero(w)
                    yc, xc = int(round(y0 + py.mean())), int(round(x0 + px.mean()))
                    tomados.append((yc, xc, float(s)))
            return tomados
        _m._picos = _picos
leer = _m.leer
