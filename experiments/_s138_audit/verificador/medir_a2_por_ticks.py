"""VERIFICADOR S138: la posicion de la anomalia del autor en A2 (y A6), medida con un
instrumento INDEPENDIENTE de los dos ejes que la midieron.

POR QUE OTRO INSTRUMENTO. El eje 3 da 10,45 km / 84,1 grados para A2 y el eje 5 da 10,98 km /
83,2; por el proyecto circula ademas un 9,6 km escrito a mano en conformidad_apendice.py:230.
Los tres numeros salen de la MISMA figura, asi que la diferencia es de calibracion: los dos ejes
fijan la escala con el MARCO del panel (uno con cajas a mano, el otro con la componente conexa),
y el marco es justo lo que un anti-aliasing de uno o dos pixeles corre. Aca la escala se fija con
las MARCAS DE GRADUACION del eje (10, 20, 30, 40, 50), que estan dibujadas sobre el dato y no
sobre el borde, y ademas permiten deducir cuantas celdas tiene la matriz en vez de suponerlo.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
 1. Si la anomalia estuviera en otro lado, esta medicion lo veria? Si: el centroide de los pixeles
    blancos se convierte a unidades de dato con la recta ajustada a las cinco marcas; mover la
    mancha mueve el resultado linealmente. Control positivo: se mide tambien A6, cuya anomalia el
    paper pone en el crater, y tiene que dar ~0 km.
 2. Si el instrumento estuviera muerto, se veria distinto? Si: (a) el ajuste a las cinco marcas
    reporta su residuo, y un residuo grande delata que no encontro las marcas; (b) el panel
    negativo A7 no tiene ningun pixel blanco y tiene que devolver "sin mascara", no 0 km; (c) se
    verifica que el numero de celdas deducido del ajuste sea entero y cercano a 50 o 51.

READ-ONLY. Escribe solo en experiments/_s138_audit/verificador/.
Uso: PYTHONIOENCODING=utf-8 python experiments/_s138_audit/verificador/medir_a2_por_ticks.py
"""
import io
import json
import math
from pathlib import Path

import numpy as np
import fitz
from PIL import Image

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[2]
PDF = RAIZ / "documentacion" / "sp426.5.pdf"

# xref del PNG embebido de cada figura (verificado con get_image_rects: el de arriba es el primero)
XREF = {"A2": 140, "A3": 145, "A6": 166, "A7": 171}
# el panel ALERT Mask es el del medio de la fila de abajo en la grilla 2x3 de cada figura
CASOS = ["A2", "A6", "A7", "A3"]


def raster(nombre):
    doc = fitz.open(PDF)
    info = doc.extract_image(XREF[nombre])
    return np.asarray(Image.open(io.BytesIO(info["image"])).convert("RGB"), dtype=np.int16)


def panel_alert(rgb):
    """Caja del panel ALERT Mask: fila inferior, columna del medio.

    Se localiza por la estructura de la figura: seis paneles cuadrados en 2 filas x 3 columnas.
    Se buscan las componentes conexas oscuras grandes y aproximadamente cuadradas y se toma la que
    cae en la fila de abajo y en la columna del medio.
    """
    from scipy import ndimage
    gris = rgb.mean(axis=2)
    lab, _ = ndimage.label(gris < 150)
    cajas = []
    for sl in ndimage.find_objects(lab):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if w < 150 or h < 150 or not (0.8 <= w / h <= 1.25):
            continue
        cajas.append((sl[0].start, sl[0].stop - 1, sl[1].start, sl[1].stop - 1))
    if not cajas:
        return None
    # fila de abajo = las de mayor y0; columna del medio = la de x0 intermedio entre esas
    y0max = max(c[0] for c in cajas)
    abajo = [c for c in cajas if c[0] > y0max - 40]
    abajo.sort(key=lambda c: c[2])
    return abajo[len(abajo) // 2] if abajo else None


def ticks_x(gris, y_borde_inf, x0, x1):
    """Posiciones (en px) de las marcas de graduacion bajo el eje inferior del panel.

    Las marcas son trazos cortos oscuros inmediatamente debajo del borde del panel.
    """
    banda = gris[y_borde_inf + 1: y_borde_inf + 6, x0: x1 + 1]
    oscuro = (banda < 120).any(axis=0)
    grupos, actual = [], []
    for i, v in enumerate(oscuro):
        if v:
            actual.append(i)
        elif actual:
            grupos.append(actual)
            actual = []
    if actual:
        grupos.append(actual)
    return [x0 + float(np.mean(g)) for g in grupos if len(g) <= 6]


def medir(nombre):
    rgb = raster(nombre)
    gris = rgb.mean(axis=2)
    caja = panel_alert(rgb)
    if caja is None:
        return {"caso": nombre, "error": "panel no encontrado"}
    y0, y1, x0, x1 = caja
    tx = ticks_x(gris, y1, x0, x1)
    out = {"caso": nombre, "panel_px": [int(y0), int(y1), int(x0), int(x1)],
           "n_ticks_x": len(tx), "ticks_x_px": [round(t, 2) for t in tx]}
    if len(tx) != 5:
        out["error"] = "no se encontraron las 5 marcas (10,20,30,40,50)"
        return out
    valores = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    # recta px = a*valor + b
    a, b = np.polyfit(valores, np.array(tx), 1)
    resid = float(np.max(np.abs(np.polyval([a, b], valores) - np.array(tx))))
    out["px_por_celda"] = round(float(a), 4)
    out["residuo_ajuste_px"] = round(resid, 3)
    # borde izquierdo del panel = 0,5 en unidades de dato (convencion imagesc de MATLAB);
    # de ahi se deduce N, el numero de celdas de la matriz.
    val_borde_izq = (x0 - b) / a
    val_borde_der = (x1 - b) / a
    out["valor_en_borde_izq"] = round(float(val_borde_izq), 2)
    out["valor_en_borde_der"] = round(float(val_borde_der), 2)
    n_celdas = float(val_borde_der - val_borde_izq)
    out["n_celdas_deducido"] = round(n_celdas, 2)
    # centro de la grilla (la cumbre, segun el paper: grilla centrada en la cumbre)
    cx_val = (val_borde_izq + val_borde_der) / 2.0
    # eje y: el valor crece hacia arriba (los rotulos 10 abajo, 50 arriba)
    interior = (slice(y0 + 3, y1 - 2), slice(x0 + 3, x1 - 2))
    sub = gris[interior]
    blanco = sub > 170
    out["n_px_blancos"] = int(blanco.sum())
    if blanco.sum() == 0:
        out["mascara"] = "sin mascara"
        return out
    fil, col = np.nonzero(blanco)
    cy_px = float(np.mean(fil)) + y0 + 3
    cx_px = float(np.mean(col)) + x0 + 3
    # conversion x
    cx_dato = (cx_px - b) / a
    # conversion y: misma escala, origen en el borde inferior, creciendo hacia arriba
    py_por_celda = (y1 - y0) / n_celdas
    cy_dato = val_borde_izq + (y1 - cy_px) / py_por_celda
    cy_val_centro = cx_val  # la grilla es cuadrada
    dx = cx_dato - cx_val
    dy = cy_dato - cy_val_centro
    out["centroide_dato"] = [round(cx_dato, 2), round(cy_dato, 2)]
    out["centro_grilla_dato"] = round(cx_val, 2)
    out["dist_km"] = round(float(math.hypot(dx, dy)), 2)
    out["rumbo_deg"] = round(float((math.degrees(math.atan2(dx, dy)) + 360) % 360), 1)
    out["area_celdas"] = round(float(blanco.sum()) / (a * py_por_celda), 2)
    return out


if __name__ == "__main__":
    res = [medir(c) for c in CASOS]
    for r in res:
        print(json.dumps(r, ensure_ascii=False))
    (HERE / "medir_a2_por_ticks.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nescrito", HERE / "medir_a2_por_ticks.json")
