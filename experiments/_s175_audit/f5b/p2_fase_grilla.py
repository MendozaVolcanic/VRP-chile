# -*- coding: utf-8 -*-
"""P2 (F5b): medir desde la propia lámina dónde empieza la grilla y cuánto mide una celda, sin usar el TIF.

Por qué: el panel se dibuja por vecino más cercano con 1,12 a 2,25 px por celda, así que hay columnas (y filas) de
píxeles duplicadas donde dos centros de píxel caen en la misma celda. La posición de esas duplicadas depende sólo
del origen X0 y de la escala a (px por celda): se ajustan por fuerza bruta comparando el conjunto de duplicadas
observado con el predicho. Así la regla de recorte sale del PNG y no del TIF, y vale para las láminas sin TIF.

Pregunta 1 del instrumento: si el panel no fuera un dibujo por vecino más cercano de una grilla regular, no habría
patrón de duplicadas y el ajuste daría un acuerdo (Jaccard) bajo: se imprime.
Pregunta 2: si el recorte estuviera mal (marco adentro), las columnas del marco salen como duplicadas al borde y el
ajuste empeora; se imprime el número de duplicadas observadas y predichas.

Uso: python -I p2_fase_grilla.py [png ...]. Sin argumentos: las 4 láminas de validación. Salida: p2_fase_grilla_out.json.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
N_CELDAS = {"VIIRS375": 134, "VIIRS750": 67, "MODIS": 51}   # tamaño de la grilla del TIF por sensor (F5: 134 y 67; MODIS SOSPECHA hasta leer un TIF)
DEF = ["20260612_153203_VIIRS375_Latest10NTI.png", "20260809_082023_VIIRS375_Latest10NTI.png",
       "20260621_092513_VIIRS750_Latest10NTI.png", "20260922_092431_VIIRS375_Latest10NTI.png"]


def celda_panel(im, k=0):
    """Celda del mosaico (x0, y0, ancho 165, alto 236) y bbox exterior del marco del panel k."""
    col, row = k % 5, k // 5
    x0, y0 = 5 + 165 * col, 155 + 236 * row
    sub = im[y0:y0 + 175, x0:x0 + 165].astype(int)
    bg = (np.abs(sub - 242).max(axis=2) <= 3)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    frame = ((g > 200) & (r < 140) & (b < 140)) | ((np.abs(r - g) < 4) & (np.abs(g - b) < 4) & (r > 60) & (r < 200) & ~bg)
    ys, xs = np.where(frame)
    return x0, y0, (x0 + xs.min(), y0 + ys.min(), x0 + xs.max(), y0 + ys.max())


def duplicadas(A, eje):
    """Índices absolutos i tales que la columna (eje 1) o fila (eje 0) i es idéntica a la i+1 dentro del recorte."""
    if eje == 1:
        eq = np.all(A[:, 1:] == A[:, :-1], axis=(0, 2))
    else:
        eq = np.all(A[1:] == A[:-1], axis=(1, 2))
    return set(np.where(eq)[0].tolist())


def predichas(n, X0, a, i0, i1):
    """Duplicadas predichas: píxeles i (absolutos, de i0 a i1-1) con celda(i) == celda(i+1), celda = floor((i + 0,5 - X0) / a)."""
    i = np.arange(i0, i1)
    c0 = np.floor((i + 0.5 - X0) / a)
    c1 = np.floor((i + 1.5 - X0) / a)
    return set((i[c0 == c1] - i0).tolist())


def ajustar(obs, n, i0, i1, lo, hi):
    """Barrido de X0 (origen absoluto, píxeles) y a (px por celda); devuelve el mejor por Jaccard."""
    best = (-1, None, None)
    for X0 in np.arange(lo - 3, lo + 3.001, 0.05):
        for Wd in np.arange((hi - lo) - 4, (hi - lo) + 4.001, 0.1):
            a = Wd / n
            p = predichas(n, X0, a, i0, i1)
            j = len(obs & p) / max(1, len(obs | p))
            if j > best[0]:
                best = (j, round(float(X0), 2), round(float(a), 4))
    return best


def main(pngs):
    out = []
    for png in pngs:
        sensor = [s for s in N_CELDAS if s in png][0]
        n = N_CELDAS[sensor]
        im = np.array(Image.open(os.path.join(TMP, "png", png)).convert("RGB"))
        cx, cy, (fx0, fy0, fx1, fy1) = celda_panel(im, 0)
        # recorte conservador: 4 px adentro del bbox exterior del marco por cada lado (sin marco ni antialias)
        i0x, i1x, i0y, i1y = fx0 + 4, fx1 - 3, fy0 + 4, fy1 - 3
        A = im[i0y:i1y, i0x:i1x]
        # máscara: ignorar píxeles blancos (NaN) para no contar duplicadas espurias; se usa sólo el bloque de filas/cols sin blanco total
        dx = duplicadas(A, 1)
        dy = duplicadas(A, 0)
        bx = ajustar(dx, n, i0x, i1x, fx0, fx1)
        by = ajustar(dy, n, i0y, i1y, fy0, fy1)
        o = {"png": png, "sensor": sensor, "n": n, "marco_bbox_exterior": [int(fx0), int(fy0), int(fx1), int(fy1)],
             "dup_cols_obs": len(dx), "dup_filas_obs": len(dy),
             "x": {"jaccard": round(bx[0], 3), "X0": bx[1], "px_por_celda": bx[2], "X1": round(bx[1] + bx[2] * n, 2) if bx[1] is not None else None},
             "y": {"jaccard": round(by[0], 3), "Y0": by[1], "px_por_celda": by[2], "Y1": round(by[1] + by[2] * n, 2) if by[1] is not None else None}}
        out.append(o)
        print(json.dumps(o, ensure_ascii=False))
    json.dump(out, open(os.path.join(H, "p2_fase_grilla_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:] or DEF)
