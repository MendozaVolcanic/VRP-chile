# -*- coding: utf-8 -*-
"""Lector del panel "Last Month" de Dist.png de MIROVA (850 x 600 o 850 x 596).

Que dibuja MIROVA ahi: una serie de tiempo de la distancia maxima ("Max Distance") de cada pasada con anomalia, un
marcador por pasada sobre un tallo vertical: circulo rojo (< 5 km), cuadrado negro (> 5 km); la pasada de la
cabecera "Last Update" lleva una estrella amarilla si la anomalia esta activa, y una linea punteada vertical marca
el momento del grafico. Eje y 0 a 25 km (lo de mas de 25 km no se dibuja en este panel).

Lee: geometria (techo 25 km, eje 0 km como ocr_utils V29; marcas semanales del eje x), marcadores (plantillas de
anillo y cuadrado, x afinado al tallo), estrella y linea punteada. La fecha de la primera marca semanal y el
desfase horario se resuelven fuera (control_dist.calibrar)."""
import numpy as np
from PIL import Image
from scipy.signal import correlate2d


def _ring(r_in=2.4, r_out=4.1, n=9):
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    d = np.hypot(yy - c, xx - c)
    return (d >= r_in) & (d <= r_out)


def _square(w, h):
    t = np.zeros((h + 2, w + 2), bool)
    t[1, 1:w + 1] = t[h, 1:w + 1] = True
    t[1:h + 1, 1] = t[1:h + 1, w] = True
    return t


RING = _ring()
SQUARES = [_square(6, 7), _square(7, 7), _square(6, 6)]


def _score(mask, tpl):
    return correlate2d(mask.astype(float), tpl.astype(float), mode="same") / tpl.sum()


def _picos(score, umbral, sep=3):
    ys, xs = np.nonzero(score >= umbral)
    orden = np.argsort(-score[ys, xs])
    tomados = []
    for i in orden:
        y, x = ys[i], xs[i]
        if all(abs(y - a) > sep or abs(x - b) > sep for a, b, _ in tomados):
            tomados.append((int(y), int(x), float(score[y, x])))
    return tomados


def _grupos(f, gap=2):
    if not f:
        return []
    g = [[f[0]]]
    for y in f[1:]:
        (g[-1].append(y) if y - g[-1][-1] <= gap else g.append([y]))
    return [float(np.mean(x)) for x in g]


def geometria(gray):
    h = gray.shape[0]; sy = h / 600.0
    def filas(y0, y1, u):
        v = gray[y0:y1, 300:790] < u
        return [y0 + i for i, c in enumerate(v.sum(1)) if c >= 0.93 * v.shape[1]]
    fe = filas(int(240 * sy), int(340 * sy), 170)
    if not fe:
        return None
    eje = _grupos(fe)[-1]
    cand = [t for t in _grupos(filas(int(70 * sy), int(eje - 150 * sy), 235)) if 160 * sy < eje - t < 210 * sy]
    if not cand:
        return None
    techo = min(cand, key=lambda t: abs((eje - t) - 185 * sy))
    y0, y1 = int(techo + 4), int(eje - 4)
    cols = []
    for x in range(240, 830):
        v = gray[y0:y1, x]
        if (v < 236).mean() > 0.9 and 170 < np.median(v) < 233:
            cols.append(x)
    gx = _grupos(cols)
    mejor = []
    for i in range(len(gx)):
        seq = [gx[i]]
        for x in gx[i + 1:]:
            if abs((x - seq[-1]) - 106.5) < 4:
                seq.append(x)
        if len(seq) > len(mejor):
            mejor = seq
    if len(mejor) < 3:
        return None
    ppd = float(np.median(np.diff(mejor))) / 7.0
    return {"techo": techo, "eje": eje, "ticks": mejor, "ppd": ppd}


def leer(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gray = a.mean(2)
    geo = geometria(gray)
    if geo is None:
        return None
    t0, ej = int(geo["techo"]) - 6, int(geo["eje"]) + 4
    x0, x1 = int(geo["ticks"][0]) - 4, int(geo["ticks"][-1]) + 4
    sub = (slice(t0, ej), slice(x0, x1))
    roj = ((r - (g + b) / 2) > 70)[sub]
    neutro = (np.abs(r - b) < 12) & (np.abs(r - g) < 12)      # la punteada es azulada (134,134,148): queda fuera
    osc = ((gray < 175) & neutro)[sub]
    osc[int(geo["eje"]) - t0 - 2:, :] = False                 # el eje 0 km es oscuro: no es marcador
    ama = ((r > 200) & (g > 200) & (b < 110))[sub]
    km = lambda y: (geo["eje"] - y) * 25.0 / (geo["eje"] - geo["techo"])
    ye = int(geo["eje"]) - t0 - 2

    def afinar(mask, y, x, mitad):
        y_a = y + mitad + 1
        if ye - y_a >= 3:
            vent = mask[y_a:ye, max(0, x - 5):x + 6]
            cols = vent.sum(0)
            if cols.max() >= 0.8 * vent.shape[0]:
                return max(0, x - 5) + int(np.argmax(cols))
        w = mask[max(0, y - mitad):y + mitad + 1, max(0, x - mitad):x + mitad + 1]
        ys_, xs_ = np.nonzero(w)
        return max(0, x - mitad) + xs_.mean() if len(xs_) else x

    marc = []
    for (y, x, s) in _picos(_score(roj, RING), 0.55):
        marc.append({"tipo": "circulo", "x": afinar(roj, y, x, 4) + x0, "y": y + t0, "km": km(y + t0), "score": s})
    sq = np.max([_score(osc, T) for T in SQUARES], axis=0)
    for (y, x, s) in _picos(sq, 0.65):
        marc.append({"tipo": "cuadrado", "x": afinar(osc, y, x, 4) + x0, "y": y + t0, "km": km(y + t0), "score": s})
    estrella = None
    if ama.sum() > 20:
        ys, xs = np.nonzero(ama)
        estrella = {"tipo": "estrella", "x": xs.mean() + x0, "y": ys.mean() + t0, "km": km(ys.mean() + t0)}
    pun = ((b - r >= 8) & (b - r <= 25) & (gray > 110) & (gray < 200))[int(geo["techo"]) + 3:int(geo["eje"]) - 3, x0:x1]
    frac = pun.mean(0)
    xp = int(np.argmax(frac))
    punteada = float(xp + x0) if frac[xp] > 0.25 else None
    return {"geo": geo, "marcadores": marc, "estrella": estrella, "punteada": punteada}
