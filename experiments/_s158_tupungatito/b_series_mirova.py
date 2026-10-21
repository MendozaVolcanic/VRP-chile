# -*- coding: utf-8 -*-
"""S158. Lee, píxel a píxel, las series «Last Month» de distancia (Dist.png) y de potencia (logVRP.png) que
MIROVA dibuja para Tupungatito VIIRS 375, en las imágenes bajadas por a_bajar_imagenes.py.

POR QUÉ: las dos alertas protegidas que no publicamos (2026-09-28 05:18, 2,51 MW; 2026-09-29 04:54, 1,86 MW)
son filas «sólo OCR» cuya distancia el OCR leyó de la imagen de OTRA pasada (la cabecera «Last Update» de los
archivos de 05:18 y de 04:54 dice 05:36:01 y 06:36:00). Pero cada lámina trae además la serie de los últimos
30 días, donde MIROVA dibuja cada pasada con alerta: tallo y marcador ROJO si la anomalía está a menos de 7 km
del volcán, GRIS-NEGRO si está a más (leyenda de la lámina, «<7km» y «>7km»). Esa serie la dibuja MIROVA, no
el OCR. Si en el día de la alerta hay dos marcadores y la tabla latest.php (independiente del OCR) ya dice cuál
de las dos pasadas es la cercana y con qué VRP, el otro marcador es el de la pasada sólo OCR.

Calibración leída de la propia lámina (no supuesta): en Dist.png, las líneas horizontales del panel van cada
5 km de 0 (eje) a 25 km (marco); en logVRP.png, de 10^4 W (eje) a 10^11 W (marco), con una línea por década.
Se comprueba que salgan 6 y 8 líneas. El valor se lee en el centro del marcador (caja del contorno, sin el
tallo). Los marcadores son huecos (cuadrado o círculo en Dist, triángulo en logVRP): en el triángulo el centro
de la caja queda ~1 px bajo el centro de masa, o sea ~0,04 décadas; no cambia ninguna conclusión.

Uso: python -I b_series_mirova.py <dir_imagenes>
"""
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = Path(sys.argv[1])
Y0, Y1 = 105, 297            # franja del panel «Last Month» (marco en y~110, eje en y~294)
X0, X1 = 280, 740            # a la derecha de 740 están los rótulos de nivel de logVRP («Extreme», ...)


def mascaras(im):
    r, g, b = (im[..., i].astype(int) for i in range(3))
    gris = (np.abs(r - g) < 10) & (np.abs(g - b) < 10) & (r < 170)
    rojo = (r > 170) & (g < 130) & (b < 130)
    return {"gris": gris, "rojo": rojo}


def lineas_horizontales(im):
    filas = [y for y in range(Y0, Y1) if (im[y, 400:700].astype(int).sum(1) < 720).mean() > 0.8]   # 400:700 evita la caja de la leyenda
    grupos, act = [], []
    for y in filas:
        if act and y - act[-1] > 1:
            grupos.append(sum(act) / len(act)); act = []
        act.append(y)
    if act:
        grupos.append(sum(act) / len(act))
    return grupos


def sin_tallos_ni_lineas(m):
    """Quita tramos verticales largos (tallos, >= 8 px) y horizontales largos (líneas, >= 20 px)."""
    m = m.copy()
    v = np.zeros_like(m)
    for x in range(m.shape[1]):
        col = m[:, x]; y = 0
        while y < len(col):
            if col[y]:
                y2 = y
                while y2 < len(col) and col[y2]:
                    y2 += 1
                if y2 - y >= 8:          # bordes de marcador: 7 px como mucho
                    v[y:y2, x] = True
                y = y2
            else:
                y += 1
    h = np.zeros_like(m)
    for y in range(m.shape[0]):
        fila = m[y]; x = 0
        while x < len(fila):
            if fila[x]:
                x2 = x
                while x2 < len(fila) and fila[x2]:
                    x2 += 1
                if x2 - x >= 20:
                    h[y, x:x2] = True
                x = x2
            else:
                x += 1
    return m & ~v & ~h


def marcadores(im):
    out = []
    for nombre, m in mascaras(im).items():
        sub = sin_tallos_ni_lineas(m[Y0:Y1, X0:X1])
        lab, n = ndimage.label(sub, structure=np.ones((3, 3)))
        for i, sl in enumerate(ndimage.find_objects(lab), start=1):
            # Un resto del tallo (menos de 8 px) puede quedar pegado bajo el marcador: la caja se mide sin las
            # columnas cuya extensión vertical supera 7 px (el tallo; el contorno del marcador mide 7 o menos).
            comp = lab[sl] == i
            cols = [c for c in range(comp.shape[1]) if comp[:, c].any()
                    and (np.where(comp[:, c])[0].max() - np.where(comp[:, c])[0].min()) <= 7]
            if not cols:
                continue
            filas = np.where(comp[:, cols].any(1))[0]
            sl = (slice(sl[0].start + filas.min(), sl[0].start + filas.max() + 1), sl[1])
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            # un marcador hueco partido por su tallo deja dos mitades de 3 a 4 px de ancho: se juntan abajo
            if 4 <= h <= 9 and 2 <= w <= 10:   # círculo relleno: hasta 9 px
                out.append({"color": nombre, "y0": sl[0].start + Y0, "y1": sl[0].stop - 1 + Y0,
                            "x0": sl[1].start + X0, "x1": sl[1].stop - 1 + X0})
    # juntar mitades del mismo marcador (mismo color, cajas que se tocan o casi en x y se solapan en y)
    out.sort(key=lambda d: (d["color"], d["x0"]))
    juntos = []
    for d in out:
        if (juntos and juntos[-1]["color"] == d["color"] and d["x0"] - juntos[-1]["x1"] <= 4
                and min(d["y1"], juntos[-1]["y1"]) >= max(d["y0"], juntos[-1]["y0"])):
            j = juntos[-1]
            j["x1"] = max(j["x1"], d["x1"]); j["y0"] = min(j["y0"], d["y0"]); j["y1"] = max(j["y1"], d["y1"])
        else:
            juntos.append(dict(d))
    for d in juntos:
        d["xc"] = (d["x0"] + d["x1"]) / 2.0
        d["yc"] = (d["y0"] + d["y1"]) / 2.0
    return sorted(juntos, key=lambda d: d["xc"])


for f in sorted(D.glob("*_Dist.png")) + sorted(D.glob("*_logVRP.png")):
    im = np.array(Image.open(f).convert("RGB"))
    gl = lineas_horizontales(im)
    es_dist = f.name.endswith("_Dist.png")
    esperadas = 6 if es_dist else 8
    print(f"\n== {f.name}")
    print(f"   líneas horizontales del panel: {len(gl)} (esperadas {esperadas}) en y = {[round(v, 1) for v in gl]}")
    if len(gl) != esperadas:
        print("   CALIBRACIÓN NO CONFIABLE: se omite"); continue
    top, base = gl[0], gl[-1]
    paso = (base - top) / (esperadas - 1)
    print(f"   paso entre líneas {paso:.2f} px (desv. máx. {max(abs(gl[i] - (top + i * paso)) for i in range(len(gl))):.2f} px)")
    for d in marcadores(im):
        if d["xc"] < 600:
            continue                      # sólo los últimos ~13 días del panel
        if es_dist:
            v = 25.0 * (base - d["yc"]) / (base - top)
            txt = f"{v:5.2f} km"
        else:
            v = 11.0 - 7.0 * (d["yc"] - top) / (base - top)
            txt = f"log10 W {v:5.2f} = {10 ** v / 1e6:6.3f} MW"
        print(f"   x {d['xc']:6.1f}  {d['color']:4s}  caja y {d['y0']}-{d['y1']} x {d['x0']}-{d['x1']}  -> {txt}")
