"""VERIFICADOR S138: posicion de la mascara del autor, escala fijada por los ROTULOS del eje.

POR QUE. Eje 3 da 10,45 km para A2 y eje 5 da 10,98; el proyecto arrastra ademas un 9,6 escrito a
mano. Los tres salen de la misma figura: la diferencia es de calibracion, porque los dos ejes fijan
la escala con el MARCO del panel y el marco esta corrido ~1,3 px respecto del limite real del eje.
Aca la escala sale de los rotulos 10/20/30/40/50 de cada eje, que estan ligados al dato.

DOS PREGUNTAS. (1) Si la mancha estuviera en otro lado la recta la movería linealmente; control
positivo A6 (el paper la pone en el crater) tiene que dar ~0 km. (2) Si el instrumento estuviera
muerto: el ajuste reporta su residuo, A7 (negativo) tiene que dar "sin mascara" y no 0 km, y el
numero de celdas deducido tiene que salir entero (~51).
"""
import io, json, math
from pathlib import Path
import numpy as np, fitz
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[2]
PDF = RAIZ / "documentacion" / "sp426.5.pdf"
XREF = {"A1": 132, "A2": 140, "A3": 145, "A4": 153, "A5": 158, "A6": 166, "A7": 171, "A8": 179, "A9": 184}

def raster(n):
    d = fitz.open(PDF)
    return np.asarray(Image.open(io.BytesIO(d.extract_image(XREF[n])["image"])).convert("RGB"), dtype=np.int16)

def paneles(g):
    lab, _ = ndimage.label(g < 150)
    out = []
    for sl in ndimage.find_objects(lab):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if w > 150 and h > 150 and 0.8 <= w / h <= 1.25:
            out.append((sl[0].start, sl[0].stop - 1, sl[1].start, sl[1].stop - 1))
    return out

def grupos(mask):
    gs, cur = [], []
    for i, v in enumerate(mask):
        if v: cur.append(i)
        elif cur: gs.append(cur); cur = []
    if cur: gs.append(cur)
    return gs

def juntar(centros, extremos, gap=12):
    """Une los grupos de un mismo rotulo de dos digitos (separados por < gap px)."""
    out, cur = [], [0]
    for i in range(1, len(extremos)):
        if extremos[i][0] - extremos[i - 1][1] < gap: cur.append(i)
        else: out.append(cur); cur = [i]
    out.append(cur)
    return [((extremos[c[0]][0] + extremos[c[-1]][1]) / 2.0) for c in out]

def eje_x(g, y1, x0, x1):
    b = g[y1 + 5:y1 + 20, x0 - 18:x1 + 19]
    gs = grupos((b < 150).any(axis=0))
    ext = [(x0 - 18 + q[0], x0 - 18 + q[-1]) for q in gs]
    return juntar(None, ext)

def eje_y(g, y0, y1, x0):
    b = g[y0 - 12:y1 + 13, max(0, x0 - 26):x0 - 4]
    gs = grupos((b < 150).any(axis=1))
    ext = [(y0 - 12 + q[0], y0 - 12 + q[-1]) for q in gs]
    return [(e[0] + e[1]) / 2.0 for e in ext]   # los rotulos del eje y no se parten en vertical

def medir(nombre):
    rgb = raster(nombre); g = rgb.mean(axis=2)
    ps = paneles(g)
    y0m = max(p[0] for p in ps)
    abajo = sorted([p for p in ps if p[0] > y0m - 40], key=lambda p: p[2])
    y0, y1, x0, x1 = abajo[len(abajo) // 2]
    cx = eje_x(g, y1, x0, x1); cy = eje_y(g, y0, y1, x0)
    r = {"caso": nombre, "panel": [int(y0), int(y1), int(x0), int(x1)],
         "n_rotulos_x": len(cx), "n_rotulos_y": len(cy)}
    if len(cx) != 5 or len(cy) != 5:
        r["error"] = "rotulos no detectados"; r["cx"] = cx; r["cy"] = cy; return r
    v = np.array([10., 20., 30., 40., 50.])
    ax, bx = np.polyfit(v, np.array(cx), 1)
    ay, by = np.polyfit(v[::-1], np.array(cy), 1)   # el eje y crece hacia arriba
    r["px_por_celda_x"] = round(float(ax), 4); r["px_por_celda_y"] = round(float(-ay), 4)
    r["residuo_x_px"] = round(float(np.max(np.abs(np.polyval([ax, bx], v) - np.array(cx)))), 2)
    r["residuo_y_px"] = round(float(np.max(np.abs(np.polyval([ay, by], v[::-1]) - np.array(cy)))), 2)
    r["celdas_x_en_panel"] = round(float((x1 - x0) / ax), 2)
    r["celdas_y_en_panel"] = round(float((y1 - y0) / -ay), 2)
    centro = 26.0    # grilla 51 x 51 (deducido: el panel abarca 51,1 celdas), cumbre al centro
    sub = g[y0 + 3:y1 - 2, x0 + 3:x1 - 2]
    bl = sub > 170
    r["n_px_blancos"] = int(bl.sum())
    if bl.sum() == 0:
        r["mascara"] = "sin mascara"; return r
    fil, col = np.nonzero(bl)
    px = float(np.mean(col)) + x0 + 3; py = float(np.mean(fil)) + y0 + 3
    vx = (px - bx) / ax; vy = (py - by) / ay
    dx, dy = vx - centro, vy - centro
    r["centroide_celdas"] = [round(vx, 2), round(vy, 2)]
    r["dist_km"] = round(float(math.hypot(dx, dy)), 2)
    r["rumbo_deg"] = round(float((math.degrees(math.atan2(dx, dy)) + 360) % 360), 1)
    r["area_celdas"] = round(float(bl.sum()) / (ax * -ay), 2)
    return r

if __name__ == "__main__":
    res = [medir(c) for c in ["A1", "A2", "A3", "A5", "A6", "A8", "A4", "A7", "A9"]]
    for x in res: print(json.dumps(x, ensure_ascii=False))
    (HERE / "ticks2.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
