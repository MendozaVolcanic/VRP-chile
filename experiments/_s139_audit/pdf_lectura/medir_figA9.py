# -*- coding: utf-8 -*-
"""S139: lee los valores de dNTI y dETI de la Fig. A9 de SP426.5 (Stromboli,
19-Jan-2010, caso NEGATIVO: la leyenda dice que no se detecta hotspot) mapeando el
color de cada pixel del panel contra la barra de color del propio panel.

Por que importa: si en una escena que MIROVA declara negativa hay un pixel con
dNTI > C1 y dETI > C1 (C1 = 0,01 en ROI2 y 0,003 en ROI1), entonces la conectiva
`min(C1, mu + C2 sigma)` no puede reproducir ese negativo, porque la rama del piso
dispararia sola. Es el frente D26 / pregunta 1 del correo a Coppola.

Instrumento:
 (1) Si el mapeo color->valor estuviera roto, el histograma del panel no cubriria
     el rango de la barra y los extremos no coincidirian con los rotulos. Se imprime
     el minimo y el maximo recuperados para poder compararlos con la barra.
 (2) Control positivo: el mismo procedimiento se corre sobre el panel dNTI de la
     Fig. A8 (caso POSITIVO, hay un pixel alertado). Si el instrumento estuviera
     muerto los dos casos darian lo mismo.

Limite honesto: el maximo de la barra de color de MATLAB puede estar fijado a mano
por encima del dato, y el recorte de los paneles se hace por coordenadas medidas a
ojo. El numero de salida es una ESTIMACION, no una medicion del dato original.
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz
import numpy as np

RAIZ = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
OUT = os.path.join(RAIZ, "experiments", "_s139_audit", "pdf_lectura", "out")
PDF = os.path.join(RAIZ, "documentacion", "sp426.5.pdf")
DPI = 200
ESCALA = DPI / 72.0


def render(pagina, clip):
    doc = fitz.open(PDF)
    pix = doc[pagina - 1].get_pixmap(dpi=DPI, clip=clip)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    doc.close()
    return arr[:, :, :3].astype(np.int16)


def mapear(panel, barra, vmin, vmax):
    """barra: recorte vertical de la barra de color (alto x ancho x 3), de arriba
    (vmax) hacia abajo (vmin). Devuelve el panel convertido a valores."""
    lut = barra.reshape(-1, barra.shape[1], 3).mean(axis=1)  # promedio por fila
    if lut.shape[0] > 256:
        sel = np.linspace(0, lut.shape[0] - 1, 256).astype(int)
        lut = lut[sel]
    n = lut.shape[0]
    valores = np.linspace(vmax, vmin, n)
    plano = panel.reshape(-1, 3).astype(np.float32)
    # distancia a cada entrada de la LUT
    idx = np.empty(plano.shape[0], dtype=np.int32)
    paso = 20000
    lutf = lut.astype(np.float32)
    for i in range(0, plano.shape[0], paso):
        bloque = plano[i:i + paso]
        d = ((bloque[:, None, :] - lutf[None, :, :]) ** 2).sum(axis=2)
        idx[i:i + paso] = d.argmin(axis=1)
    return valores[idx].reshape(panel.shape[:2])


def informe(nombre, panel_clip, barra_clip, pagina, vmin, vmax):
    panel = render(pagina, panel_clip)
    barra = render(pagina, barra_clip)
    v = mapear(panel, barra, vmin, vmax)
    # recorto un 4 % del borde del panel para no comer el marco negro del eje
    h, w = v.shape
    m = max(2, int(0.04 * min(h, w)))
    v = v[m:-m, m:-m]
    print(
        "%-28s barra=[%.4f, %.4f]  recuperado min=%.4f  p99=%.4f  max=%.4f  frac>0.01=%.4f  frac>0.003=%.4f"
        % (
            nombre,
            vmin,
            vmax,
            v.min(),
            np.percentile(v, 99),
            v.max(),
            float((v > 0.01).mean()),
            float((v > 0.003).mean()),
        )
    )
    return v


if __name__ == "__main__":
    # Coordenadas en puntos PDF, medidas sobre el render de 170 dpi de la pagina 22.
    # Pagina 22 = Fig. A8 (arriba, Etna, POSITIVO) y Fig. A9 (abajo, Stromboli, NEGATIVO).
    # factor render170 -> puntos: 72/170 = 0.4235
    f = 72.0 / 170.0

    print("--- CONTROL POSITIVO: Fig. A8 Etna (hay pixel alertado) ---")
    informe(
        "A8 dNTI (Etna, positivo)",
        fitz.Rect(133 * f, 432 * f, 307 * f, 612 * f),
        fitz.Rect(341 * f, 437 * f, 356 * f, 607 * f),
        22,
        -0.01,
        0.015,
    )

    print("--- CASO NEGATIVO: Fig. A9 Stromboli (no se detecta hotspot) ---")
    informe(
        "A9 dNTI (Stromboli, negativo)",
        fitz.Rect(133 * f, 1180 * f, 307 * f, 1358 * f),
        fitz.Rect(341 * f, 1185 * f, 356 * f, 1353 * f),
        22,
        -0.01,
        0.025,
    )
    informe(
        "A9 dETI (Stromboli, negativo)",
        fitz.Rect(768 * f, 1180 * f, 941 * f, 1358 * f),
        fitz.Rect(975 * f, 1185 * f, 990 * f, 1353 * f),
        22,
        -0.01,
        0.015,
    )
