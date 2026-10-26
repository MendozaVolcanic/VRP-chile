# -*- coding: utf-8 -*-
"""Prueba con controles sinteticos de g2_ajuste_grilla.py (S159 frente GEO, parte G).

Criterio fijado ANTES de correr: el ajuste IDENTIFICA cuando el mejor costo es <= 0,20 y la margen
(costo del segundo interpolador / costo del mejor) es >= 1,5. Recupera el desfase cuando |dx - dx_real| y
|dy - dy_real| son <= 15 m (4 % de la celda de 375 m) para lineal y cubico; para vecino basta con que el desfase
recuperado reproduzca el TIF (costo <= 0,02), porque el vecino tiene una meseta de desfases equivalentes.

Casos:
  P1 positivo, verdad lineal, desfase (+100, -60), barrido a nadir (muestras 375 x 380 m, giro 12 grados)
  P2 positivo, verdad vecino, mismo desfase
  P3 positivo, verdad cubico, desfase (-150, +40)
  P4 positivo oblicuo, verdad lineal, desfase (+100, -60), muestras 790 x 760 m (borde del barrido)
  P5 positivo con calibracion distinta y ruido: TIF = 1,03 x lineal + 0,01, ruido 1 %
  N1 negativo, verdad lineal, sin desfase: debe recuperar (0, 0)
  N2 nulo, el TIF sale de OTRO campo (otra semilla): NO debe identificar
Uso: python -I g2_prueba_ajuste.py
"""
import io
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g2_ajuste_grilla as g  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CELDA, N = 375.0, 60
ULX, ULY = 400000.0, 6300000.0


def campo(semilla):
    rng = np.random.default_rng(semilla)
    ondas = [(rng.uniform(600, 4000), rng.uniform(0, np.pi), rng.uniform(0, 2 * np.pi)) for _ in range(12)]
    focos = [(rng.uniform(ULX, ULX + N * CELDA), rng.uniform(ULY - N * CELDA, ULY), rng.uniform(0.2, 1.0))
             for _ in range(6)]

    def f(x, y):
        v = 0.3 + 0 * x
        for lam, ang, fase in ondas:
            v = v + 0.03 * np.sin(2 * np.pi * (x * np.cos(ang) + y * np.sin(ang)) / lam + fase)
        for fx, fy, a in focos:
            v = v + a * np.exp(-((x - fx) ** 2 + (y - fy) ** 2) / (2 * 250.0 ** 2))
        return v
    return f


def barrido(s_scan, s_track, giro_grados):
    c, s = np.cos(np.radians(giro_grados)), np.sin(np.radians(giro_grados))
    cx, cy = ULX + N * CELDA / 2, ULY - N * CELDA / 2
    L = N * CELDA * 0.85
    u = np.arange(-L, L, s_scan)
    w = np.arange(-L, L, s_track)
    U, W = np.meshgrid(u, w)
    return (cx + U * c - W * s).ravel(), (cy + U * s + W * c).ravel()


def tif_sintetico(px, py, pv, interp, dx, dy):
    fun = g.construir(px, py, pv)[interp]
    X, Y = g.centros(ULX, ULY, CELDA, N, N)
    return fun(X + dx, Y + dy)


def caso(nombre, interp, dx, dy, s_scan=375.0, s_track=380.0, giro=12.0, a=1.0, b=0.0, ruido=0.0, semilla_tif=None, paso_fino=None):
    f = campo(1)
    px, py = barrido(s_scan, s_track, giro)
    pv = f(px, py)
    if semilla_tif is None:
        ref = a * tif_sintetico(px, py, pv, interp, dx, dy) + b
    else:
        f2 = campo(semilla_tif)
        ref = tif_sintetico(px, py, f2(px, py), interp, dx, dy)
    if ruido:
        ref = ref * (1 + ruido * np.random.default_rng(7).standard_normal(ref.shape))
    _, res = g.ajustar(px, py, pv, ref, ULX, ULY, CELDA, paso_fino=paso_fino)
    m = res["mejor"]
    ident = m["costo"] <= 0.20 and res["margen"] >= 1.5
    if interp == "vecino":
        recupera = m["costo"] <= 0.02
    else:
        recupera = abs(m["dx"] - dx) <= 15 and abs(m["dy"] - dy) <= 15
    print(f"{nombre}: verdad {interp} ({dx:+.0f}, {dy:+.0f}) -> mejor {m['interp']} ({m['dx']:+.1f}, {m['dy']:+.1f}) "
          f"costo {m['costo']:.4f}; segundo {res['segundo']['interp']} {res['segundo']['costo']:.4f}; "
          f"margen {res['margen']:.2f}; identifica {ident}; interp correcto {m['interp'] == interp}; "
          f"desfase recuperado {recupera}")
    return ident, m["interp"] == interp, recupera


def main():
    r = {}
    r["P1"] = caso("P1", "lineal", 100, -60)
    r["P2"] = caso("P2", "vecino", 100, -60)
    # P2b, agregado DESPUES de ver fallar P2 (registrado en el informe): la malla fina de 7,5 m no pasa por
    # el desfase real y el vecino cambia de celda con desfases de metros. Misma verdad, malla fina de 2,5 m.
    r["P2b"] = caso("P2b", "vecino", 100, -60, paso_fino=2.5)
    r["P3"] = caso("P3", "cubico", -150, 40)
    r["P4"] = caso("P4", "lineal", 100, -60, s_scan=790.0, s_track=760.0, giro=8.0)
    r["P5"] = caso("P5", "lineal", 100, -60, a=1.03, b=0.01, ruido=0.01)
    r["N1"] = caso("N1", "lineal", 0, 0)
    r["N2"] = caso("N2", "lineal", 100, -60, semilla_tif=2)
    fallas = [k for k in ("P1", "P2", "P2b", "P3", "P4", "P5", "N1") if not all(r[k])]
    if r["N2"][0]:
        fallas.append("N2 (identifico sobre un campo ajeno)")
    print("\nRESULTADO:", "PASA" if not fallas else "FALLA en " + ", ".join(fallas))


if __name__ == "__main__":
    main()
